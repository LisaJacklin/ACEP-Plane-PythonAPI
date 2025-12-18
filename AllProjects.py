"""
AllProjects.py

Description: this script is designed to pull all projects currently in plane
 and display the name, identifier, and project id (uuid).

 Note that the project ID is needed in order to pull all work items for a project,
 and to gather other details about each project.
"""

import requests
import os

# Load in the api key from the file
# import os makes this easier
try:
    with open("plane.cred", "r") as f:
        api_key = f.read().strip()
except FileNotFoundError:
    print("Error: Could not find the .cred file. ")
    exit()

# configuration for api details
workspace_slug = "cyberinfrastructure"
base_url = "https://projects.camio.acep.uaf.edu/api/v1"

# List All Projects
url = f"{base_url}/workspaces/{workspace_slug}/projects/"

headers = {
  "x-api-key": api_key,
  "Content-Type": "application/json"
}

#print(f"Requesting: {url}")

## Processing the api request:
try:
  response = requests.get(url, headers=headers)
  if response.status_code == 200:
        # Convert the raw text into a Python list/dictionary
        projects = response.json()

        # Handle pagination (sometimes data is inside a 'results' key)
        if isinstance(projects, dict) and 'results' in projects:
            projects = projects['results']

        # print("\nSUCCESS: Retrieved Project List:\n")

        # table headers and formatting
        # :<30 means "align left, reserve 30 spaces"
        print(f"{'PROJECT NAME':<30} | {'IDENTIFIER':<12} | {'PROJECT ID (UUID)'}")
        print("-" * 85) # A divider line

        # get the info in rows
        for p in projects:
            name = p.get('name', 'Unknown')
            identifier = p.get('identifier', 'N/A')
            p_id = p.get('id', 'N/A')

            # print the formatted row
            print(f"{name:<30} | {identifier:<12} | {p_id}")

  else:
        print(f"Failed with status code: {response.status_code}")
        print(response.text)

except Exception as e:
  print (f"Error: {e}")