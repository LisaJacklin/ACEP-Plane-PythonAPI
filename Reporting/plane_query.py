# plane_client.py
import requests
import os
import sys
import yaml
from datetime import datetime, timezone, timedelta
from dateutil import parser

class PlaneClient:
    def __init__(self, config_file="config.yaml"):
        self.config = self._load_config(config_file)

        #load api key and header
        self.api_key = self._load_api_key()
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        # parse dates from config
        self.start_date, self.end_date = self._parse_dates()

        # tasks status from config
        self.allowed_statuses = {s.lower() for s in self.config.get('task_status', []) if s}
        self.completed_keywords = {'done', 'completed', 'verified', 'closed', 'deployed', 'cancelled'}

    # make sure the config file exists and load it
    def _load_config(self, filename):
        try:
            with open(filename, 'r') as f: return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"❌ Error: Config file '{filename}' not found."); sys.exit(1)

    # same process here for loading in api keys
    def _load_api_key(self):
        cred_file = self.config.get('cred_filename')

        if not cred_file or not os.path.exists(cred_file.strip()):
            print(f"Error: Credential file not found.")
            sys.exit(1)

        with open(cred_file, 'r') as f: return f.read().strip()

    # parse dates from config file
    def _parse_dates(self):
        #adjusted the config file to be simpler to process: no reporting setup
        start_str = self.config.get('start_date')
        end_str = self.config.get('end_date')


        if not start_str: start = datetime.now(timezone.utc) - timedelta(days=30)
        else: start = parser.parse(str(start_str)).replace(tzinfo=timezone.utc)

        if not end_str or str(end_str).lower() == "now": end = datetime.now(timezone.utc)
        else: end = parser.parse(str(end_str)).replace(tzinfo=timezone.utc)
        return start, end

    def get_api_url(self, endpoint):
        domain = self.config.get('domain', '').rstrip('/')
        version = self.config.get('api_version', 'v1')
        return f"{domain}/api/{version}/{endpoint}"

    #get_user_details shortened and moved here
    def get_user(self):
        try:
            resp = requests.get(self.get_api_url("users/me/"), headers=self.headers)
            if resp.status_code == 200:
                d = resp.json()
                return d['id'], f"{d.get('first_name','')} {d.get('last_name','')}".strip()
        except: pass
        return None, None

    def get_projects(self):
        spec_id = self.config.get('project_id', '').strip()
        ws_slug = self.config.get('workspace_slug')

        if not ws_slug or ws_slug.isspace():
             print("❌ Error: 'workspace_slug' is missing in config."); return []

        if spec_id:
            url = self.get_api_url(f"workspaces/{ws_slug}/projects/{spec_id}/")
            resp = requests.get(url, headers=self.headers)
            return [resp.json()] if resp.status_code == 200 else []

        url = self.get_api_url(f"workspaces/{ws_slug}/projects/")
        resp = requests.get(url, headers=self.headers)
        return resp.json().get('results', []) if resp.status_code == 200 else []

    #get project_states moved here
    def get_project_data(self, user_id, project):
        ws_slug = self.config.get('workspace_slug')
        pid = project['id']

        # Get State Map
        state_resp = requests.get(self.get_api_url(f"workspaces/{ws_slug}/projects/{pid}/states/"), headers=self.headers)
        state_map = {s['id']: s['name'] for s in state_resp.json().get('results', [])} if state_resp.status_code == 200 else {}

        # Get Items
        url = self.get_api_url(f"workspaces/{ws_slug}/projects/{pid}/work-items/")
        # We try to filter by API, but we will also filter in Python to be safe
        params = {"assignees": user_id, "per_page": 100}

        try:
            resp = requests.get(url, headers=self.headers, params=params)
            if resp.status_code != 200: return None
            items = resp.json().get('results', [])
        except: return None

        # Logic Processing
        active_tasks = []
        completed_tasks = []

        for item in items:

            assignees = item.get('assignees', [])
            if user_id not in assignees:
                continue
            # -------------------------------------------------------

            status_name = state_map.get(item.get('state')) or "Unknown"
            status_clean = str(status_name).strip().lower()

            # Filter by Configured Status
            if self.allowed_statuses and status_clean not in self.allowed_statuses:
                continue

            is_completed = status_clean in self.completed_keywords

            # Date Logic
            include = False
            if is_completed:
                cmp_at = item.get('completed_at')
                if cmp_at and self.start_date <= parser.isoparse(cmp_at) <= self.end_date:
                    include = True
            else:
                include = True # Always include active

            if include:
                task_name = item.get('name', 'Untitled')
                if is_completed: completed_tasks.append(f"{task_name} (Done)")
                else: active_tasks.append(task_name)

        if not active_tasks and not completed_tasks:
            return None

        return {
            "project_name": project['name'],
            "active_count": len(active_tasks),
            "completed_count": len(completed_tasks),
            "all_tasks_list": [f"• {t}" for t in active_tasks + completed_tasks]
        }