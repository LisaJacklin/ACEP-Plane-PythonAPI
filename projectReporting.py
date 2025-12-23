"""
projectReporting.py

Description: provides a basic grid for all projects and tasks based on the set timeframes.

Notes:
- currently outputing as .txt and .csv...Will want to adjust to something easier to write up/edit
- separating this into a config to pass, and classes needed.

"""

# libraries
from Reporting.plane_query import PlaneClient
from Reporting.report_render import ReportRenderer


# Adjusting bulk of main to be a function
# note that calls for libraries now required.
def main():
    print(f"--- GENERATING CUSTOM GRID REPORT ---")

    # pull information from client side
    client = PlaneClient("sample-config.yaml")

    # still using txt and csv outputs for the moment...
    out_txt = client.config.get('outputs', {}).get('text_file', 'report.txt')
    out_csv = client.config.get('outputs', {}).get('csv_file', 'report.csv')

    # pull in the render for report savings and setup
    renderer = ReportRenderer(out_txt, out_csv)

    #now user data; get_user_details swapped for client.get_user()
    my_id, my_name = client.get_user()
    if not my_id:
        print("Error: Check domain/keys in config."); return
        return

    print(f"user: {my_name}")
    print(f"period: {client.start_date.date()} to {client.end_date.date()}")

    #now to check projects with client rather than the for loop
    projects = client.get_projects()
    processed_data = []

    for proj in projects:
        print(f"   ...checking {proj['name']}")
        data = client.get_project_data(my_id, proj)
        if data:
            processed_data.append(data)

    # report output data
    if processed_data:
        renderer.save(processed_data, my_name, client.start_date, client.end_date)
    else:
        print("\n No matching tasks found for this configuration.")



if __name__ == "__main__":
    main()
