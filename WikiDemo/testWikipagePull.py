"""
testpull.py

Description: Wiki page test information pull for title, and contents.
This test does not convert the html of plane pages to markdown.

Notes:
- Test Page: Plane API Wiki Tester
- Struggling to get the page contents in html to display....I may be doing this wrong
- determining the page_id is difficult...working to find a way to search for it.
"""

import requests
import json
import sys

# api configuration
# todo: add in config for wiki pages
workspace_slug = "cyberinfrastructure"
base_url = "https://projects.camio.acep.uaf.edu/api/v1"
page_id = "18d0288f-55f8-45fe-a2b6-a0e708ac6e5b"
# think of this similar to project_id; no easy way to find this...
url = f"{base_url}/workspaces/{workspace_slug}/pages/{page_id}/"

# load required api token
try:
    with open("../plane.cred", "r") as f:
        api_key = f.read().strip()
except FileNotFoundError:
    print("Error: Could not find the .cred file.")
    sys.exit()

headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

# start of api request
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status() # added for error status

    # parse the JSON response
    data = response.json()

    print("--- SUCCESS: Page Metadata ---")
    print(f"Title: {data.get('name', 'No Title')}")
    print(f"Created By: {data.get('created_by', 'Unknown')}")
    print("-" * 30)

    # Print the raw content to verify
    # todo: determine why result is "none"...
    print("--- PAGE CONTENT (HTML/Raw) ---")
    content = data.get('description_html') or data.get('description')
    print(content)


except requests.exceptions.HTTPError as err:
    print(f"HTTP Error: {err}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"An error occurred: {e}")