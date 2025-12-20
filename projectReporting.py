"""
projectReporting.py

Description: provides a basic grid for all projects and tasks based on the set timeframes.

Notes:
- currently outputing as .txt and .csv...Will want to adjust to something easier to write up/edit
- separating this into a config to pass, and classes needed.

"""

import requests
import pandas as pd
import os
import sys
from datetime import datetime, timezone
from dateutil import parser

# api configuration
# todo: setup as config
base_domain = "https://projects.camio.acep.uaf.edu"
api_url = f"{base_domain}/api/v1"
workspace_slug = "cyberinfrastructure"
cred_file = "../plane.cred"
#output style
output_txt = "summary_table.txt"
output_csv = "summary_table.csv"
#include date range
start_date = datetime(2025, 10, 1, tzinfo=timezone.utc)
end_date = datetime.now(timezone.utc)

#states for the tasks
task_state = [
    "Done", "Ready for Review", "Need to Review", "Completed",
    "Closed", "Cancelled"
]
normalized_tasks = {s.strip().lower() for s in task_state}

def load_api_key():
    if not os.path.exists(cred_file):
        print(f"Error: '{cred_file}' not found.")
        sys.exit(1)
    with open(cred_file, 'r') as f:
        return f.read().strip()

api_key = load_api_key()
headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

# pulls user name for reporting
def get_user_details():
    try:
        resp = requests.get(f"{api_url}/users/me/", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return data['id'], f"{data.get('first_name','')} {data.get('last_name','')}".strip()
    except: pass
    return None, None

def get_projects():
    resp = requests.get(f"{api_url}/workspaces/{workspace_slug}/projects/", headers=headers)
    return resp.json().get('results', []) if resp.status_code == 200 else []

def get_project_states(project_id):
    url = f"{api_url}/workspaces/{workspace_slug}/projects/{project_id}/states/"
    try:
        resp = requests.get(url, headers=headers)
        state_map = {}
        if resp.status_code == 200:
            for state in resp.json().get('results', []):
                state_map[state['id']] = state['name']
        return state_map
    except: return {}

def parse_plane_date(date_str):
    if not date_str: return None
    try: return parser.isoparse(date_str)
    except: return None

# grid things out for the moment...
# todo: adjustt this to work nicely in markdown or other formats...
# todo: expand the headers to include all task_states?
def create_grid_string(data):

    if not data: return ""

    headers = ["Project", "Active (WIP)", "Completed/Review", "Detailed Task List"]
    #setup column widths
    w_proj = max(len(d["Project"]) for d in data)
    w_proj = max(w_proj, len(headers[0]))
    w_act = len(headers[1])
    w_comp = len(headers[2])

    # Find max width of task lines
    w_task = len(headers[3])
    for d in data:
        lines = d["Detailed Task List"].split('\n')
        for line in lines:
            if len(line) > w_task: w_task = len(line)

    #  padding
    w_proj += 2; w_act += 2; w_comp += 2; w_task += 2

    # Helper to draw separator line
    def draw_line():
        return f"+{'-'*w_proj}+{'-'*w_act}+{'-'*w_comp}+{'-'*w_task}+\n"

    # Helper to format a row
    def format_row(c1, c2, c3, c4):
        return f"|{c1.center(w_proj)}|{str(c2).center(w_act)}|{str(c3).center(w_comp)}| {c4:<{w_task-1}}|\n"

    out = draw_line()
    out += format_row(*headers)
    out += draw_line()

    for row in data:
        # Split task list into lines
        tasks = row["Detailed Task List"].split('\n')
        if not tasks: tasks = [""]

        # First line of table
        out += format_row(row["Project"], row["Active (WIP)"], row["Completed / In Review"], tasks[0])

        # Subsequent lines (Empty Project/Counts, just task text)
        for extra_line in tasks[1:]:
            out += format_row("", "", "", extra_line)

        out += draw_line() # Row separator

    return out

def get_project_row(user_id, project):
    pid = project['id']
    pname = project['name']
    state_lookup = get_project_states(pid)
    url = f"{api_url}/workspaces/{workspace_slug}/projects/{pid}/work-items/"
    params = {"assignees": user_id, "per_page": 100}

    try: resp = requests.get(url, headers=headers, params=params)
    except: return None
    if resp.status_code != 200: return None

    items = resp.json().get('results', [])
    count_active = 0; count_completed = 0; task_list_strings = []
    has_data = False

    print(f"   Analyzing {pname}...")

    for item in items:
        if user_id not in item.get('assignees', []): continue

        c_at = parse_plane_date(item.get('created_at'))
        u_at = parse_plane_date(item.get('updated_at'))
        cmp_at = parse_plane_date(item.get('completed_at'))

        # Date Filter
        if not ((c_at and c_at >= start_date) or (cmp_at and cmp_at >= start_date) or (u_at and u_at >= start_date)):
            continue

        has_data = True
        state_id = item.get('state')
        status_name = state_lookup.get(state_id) or item.get('state_detail', {}).get('name') or "Unknown"

        task_name = item.get('name', 'Untitled')

        if str(status_name).strip().lower() in normalized_tasks:
            count_completed += 1
            task_list_strings.append(f"• {task_name} (Done)")
        else:
            count_active += 1
            task_list_strings.append(f"• {task_name}")

    if not has_data: return None

    return {
        "Project": pname,
        "Active (WIP)": count_active,
        "Completed / In Review": count_completed,
        "Detailed Task List": "\n".join(task_list_strings)
    }

# --- MAIN ---
if __name__ == "__main__":
    print(f"--- GENERATING CUSTOM GRID REPORT ---")
    my_id, my_name = get_user_details()

    if my_id:
        print(f"Scanning projects for {my_name}...")
        projects = get_projects()
        table_data = []

        for project in projects:
            row = get_project_row(my_id, project)
            if row: table_data.append(row)

        if table_data:
            grid_output = create_grid_string(table_data)

            print("\n")
            print(grid_output)

            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(f"EXECUTIVE SUMMARY: {my_name}\n")
                f.write(f"Generated: {end_date.strftime('%Y-%m-%d')}\n\n")
                f.write(grid_output)

            df = pd.DataFrame(table_data)
            df.to_csv(output_csv, index=False, encoding='utf-8-sig')

            print(f"\nSaved Grid Table to: {output_txt}")
            print(f"Saved CSV to:        {output_csv}")
        else:
            print("No data found.")
    else:
        print("Auth failed.")