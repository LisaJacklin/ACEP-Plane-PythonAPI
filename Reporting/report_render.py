# report_renderer.py
import pandas as pd
from datetime import datetime

#TODO: adjust so more flexability in table setup
class ReportRenderer:
    def __init__(self, output_txt="report.txt", output_csv="report.csv"):
        self.output_txt = output_txt
        self.output_csv = output_csv

    def _draw_grid(self, data):
        """Internal helper to create the ASCII table string."""
        if not data: return ""
        headers = ["Project", "Active (WIP)", "Completed/Review", "Detailed Task List"]

        # Prepare row data for width calculation
        rows = []
        for d in data:
            rows.append([
                d['project_name'],
                str(d['active_count']),
                str(d['completed_count']),
                d['all_tasks_list']
            ])

        # Width Calculations
        w_cols = [len(h) for h in headers]

        # Check content widths
        for row in rows:
            # Col 0 (Project)
            if len(row[0]) > w_cols[0]: w_cols[0] = len(row[0])
            # Col 3 (Tasks - check longest line)
            for line in row[3]:
                if len(line) > w_cols[3]: w_cols[3] = len(line)

        # Add Padding
        w_cols = [w + 2 for w in w_cols]

        def line():
            return f"+{'-'*w_cols[0]}+{'-'*w_cols[1]}+{'-'*w_cols[2]}+{'-'*w_cols[3]}+\n"

        def row_str(c1, c2, c3, c4):
            return f"|{str(c1).center(w_cols[0])}|{str(c2).center(w_cols[1])}|{str(c3).center(w_cols[2])}| {str(c4):<{w_cols[3]-1}}|\n"

        # Build Output
        out = line() + row_str(*headers) + line()

        for r in rows:
            tasks = r[3] if r[3] else [""]
            # First line with counts
            out += row_str(r[0], r[1], r[2], tasks[0])
            # Subsequent lines
            for t in tasks[1:]:
                out += row_str("", "", "", t)
            out += line()

        return out

    def save(self, data_list, user_name, start_date, end_date):
        # 1. Generate Grid
        grid = self._draw_grid(data_list)
        print("\n" + grid)

        # 2. Save Text File
        with open(self.output_txt, "w", encoding="utf-8") as f:
            f.write(f"EXECUTIVE SUMMARY: {user_name}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"Period: {start_date.date()} to {end_date.date()}\n\n")
            f.write(grid)

        # 3. Save CSV
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

        print(f"✅ Report saved to: {self.output_txt}")
        print(f"✅ Data saved to:   {self.output_csv}")