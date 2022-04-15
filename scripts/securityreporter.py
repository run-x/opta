import csv
import os
import string
import traceback
from inspect import trace

csvtfsec_output = os.popen(
    'docker run --rm -it -v "$(pwd):/src" aquasec/tfsec /src -f csv --no-colour  --include-passed'
)
# csvtfsec_output = os.popen('tfsec --no-colour -f csv')
content = ""

reader = csv.DictReader(csvtfsec_output)
ii = 0
for row in reader:
    try:
        if row["passed"] == "true":
            rowclass = "table-success"
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
    except:
        print("Error in row \n{}\nTraceback:{}".format(row, traceback.format_exc()))

template = string.Template(
    """



<body>
    <div class="container">
        <h1>Tfsec Terraform Code Analysis</h1>
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


final_output = template.substitute(elements=content)
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
