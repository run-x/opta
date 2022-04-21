# This program uses tfsec to generate an HTML
# file containing a list of security issues found
# in all terraform files in the current working directory
# and all subdirectories (recursive).

# To run it, change directory to where your terraform files are
# and then run
# python3 /path/to/securityreporter.py

# This will create an HTML file opta-tfsec-report.html in the
# current directory.

# You don't need to install tfsec, this program assumes you have
# docker so it will pull the latest tfsec container and run the
# tfsec program via docker.

import csv
import os
import string
import traceback


def maintain_tallies(passed: str, severity: str) -> None:
    if passed == "false":
        tallies["failed"] = tallies["failed"] + 1
        if severity == "CRITICAL":
            tallies["critical_failed"] = tallies["critical_failed"] + 1
        elif severity == "HIGH":
            tallies["high_failed"] = tallies["high_failed"] + 1
        else:
            tallies["other_failed"] = tallies["other_failed"] + 1
    else:
        tallies["passed"] = tallies["passed"] + 1
        if severity == "CRITICAL":
            tallies["critical_passed"] = tallies["critical_passed"] + 1
        elif severity == "HIGH":
            tallies["high_passed"] = tallies["high_passed"] + 1
        else:
            tallies["other_passed"] = tallies["other_passed"] + 1


csvtfsec_output = os.popen(
    'docker run --pull --rm -it -v "$(pwd):/src" aquasec/tfsec /src -f csv --no-colour  --include-passed --exclude-path examples/'
)
# csvtfsec_output = os.popen('tfsec --no-colour -f csv')
content = ""

reader = csv.DictReader(csvtfsec_output)
ii = 0
tallies = {
    "passed": 0,
    "failed": 0,
    "critical_failed": 0,
    "high_failed": 0,
    "other_failed": 0,
    "critical_passed": 0,
    "high_passed": 0,
    "other_passed": 0,
}
for row in reader:
    try:
        maintain_tallies(row["passed"], row["severity"])
        if row["passed"] == "true":
            rowclass = "table-success"
            tallies["passed"]
        else:
            if row["severity"] == "CRITICAL":
                rowclass = "table-danger"
            elif row["severity"] == "HIGH":
                rowclass = "table-warning"
            else:
                rowclass = "table-info"

        content += "<tr>"
        content += f'<td class="{rowclass}">{ii + 1}</td>'
        content += f"<td class=\"{rowclass}\">{row['rule_id']}</td>"
        content += f"<td class=\"{rowclass}\">{row['severity']}</td>"
        content += f"<td class=\"{rowclass}\">{row['passed']}</td>"
        content += f"<td class=\"{rowclass}\">{row['file']}</td>"
        content += f"<td class=\"{rowclass}\">{row['link']}</td>"
        content += "</tr>"
        ii = ii + 1
    except:  # noqa
        print("Error in row \n{}\nTraceback:{}".format(row, traceback.format_exc()))

template = string.Template(
    """
<body>
    <div class="container">
        <h1>Tfsec Terraform Code Analysis</h1>
        <table id="summaryTable" class="table">
        <tr>
            <td> Total Failed </td>
            <td> $failed/$total </td>
        </tr>
        <tr>
            <td> Critical Failed </td>
            <td> $crit_failed/$crit_total </td>
        </tr>
        <tr>
            <td> High Failed </td>
            <td> $high_failed/$high_total </td>
        </tr>
        <tr>
            <td> Other Failed </td>
            <td> $other_failed/$other_total </td>
        </tr>
        </table>



        <table id="myTable" class="table">
            <thead class="thead-dark">
                <tr>
                    <th scope="col">#</th>
                    <th scope="col">Rule ID</th>
                    <th scope="col">Severity</th>
                    <th scope="col">Pass/Fail</th>
                    <th scope="col">File</th>
                    <th scope="col">Link</th>
                </tr>
            </thead>
            <tbody>
                ${elements}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
)


final_output = template.substitute(
    elements=content,
    crit_failed=tallies["critical_failed"],
    crit_total=tallies["critical_passed"] + tallies["critical_failed"],
    high_failed=tallies["high_failed"],
    high_total=tallies["high_passed"] + tallies["high_failed"],
    other_failed=tallies["other_failed"],
    other_total=tallies["other_passed"] + tallies["other_failed"],
    failed=tallies["failed"],
    total=tallies["passed"] + tallies["failed"],
)
filepath = "opta-tfsec-report.html"
with open(filepath, "w") as output:
    output.write(final_output)

headercontent = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Opta Security Report</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">
    <title>Opta Security Report</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css"
        integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css">
    <script type="text/javascript" src="https://code.jquery.com/jquery-3.5.1.js"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>

    <script>
        $(document).ready(function () {
            $('#myTable').DataTable({
                "lengthMenu": [[-1, 10, 50, 100], ["All", 10, 50, 100]]
            });
        });
    </script>
</head>

"""

with open(filepath, "r+") as file:
    content = file.read()
    file.seek(0)
    file.write(headercontent + content)
