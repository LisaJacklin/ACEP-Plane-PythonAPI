# report_renderer.py
import pandas as pd
from datetime import datetime

class ReportRenderer:
    def __init__(self, output_md="report.md", output_csv="report.csv"):
        self.output_md = output_md
        self.output_csv = output_csv

    #rather than building a grid, adjust to create a markdown table
    def generate_md_table(self, data):
        if not data:
            return ""

        headers = ["Projects", "Active (WIP)", "Complete/Review", "Detailed Tasks List"]

        md = f"| {' | '.join(headers)} | \n"
        md += f"| {' | '.join(['---'] * len(headers))} |\n"

        #adjusting the data rows a bit now
        for d in data:
            project = str(d['project_name']).replace('|', '&#124;').replace('\n',' ')
            active = str(d['active_count']).replace('|', '&#124;').replace('\n', ' ')
            completed = str(d['completed_count']).replace('|', '&#124;').replace('\n','')

            #format things into a markdown table
            task_list = d.get('all_tasks_list', [])
            if task_list:
                format_tasks = [str(t).replace('|', '&#124;').replace('\n', ' ') for t in task_list]
                tasks_formatted = "<br>".join([f" {t}" for t in task_list])
            else:
                tasks_formatted = "None"

            first_task = str(task_list[0]).replace('|', '&#124;').replace('\n', ' ')
            md += f"| {project} | {active} | {completed} | {first_task} |\n"
            
            # Print SUBSEQUENT rows for the remaining tasks (leaving project/count columns blank)
            for t in task_list[1:]:
                task_str = str(t).replace('|', '&#124;').replace('\n', ' ')
                md += f"| | | | {task_str} |\n"
        return md

    def save(self, data_list, user_name, start_date, end_date):
        md_table = self.generate_md_table(data_list)

        #adjust to built header differently for md
        content = f"EXECUTIVE SUMMARY: {user_name}\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n"
        content += f"Period: {start_date.date()} to {end_date.date()}\n"
        content += md_table

        print("\n" + content)

        #now to save this new format into a markdown file
        with open(self.output_md, "w", encoding="utf-8") as f:
            f.write(content)

        # Flatten for CSV (join tasks with semicolon for single cell)
        csv_rows = []
        for d in data_list:
            csv_rows.append({
                "Project": d['project_name'],
                "Active Count": d['active_count'],
                "Completed Count": d['completed_count'],
                "Tasks": " | ".join(d['all_tasks_list'])
            })

        df = pd.DataFrame(csv_rows)
        df.to_csv(self.output_csv, index=False, encoding='utf-8-sig')

        print(f"✅ Report saved to: {self.output_md}")
        print(f"✅ Data saved to:   {self.output_csv}")