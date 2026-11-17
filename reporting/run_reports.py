

import json
import html
import subprocess
import sys
import xml.etree.ElementTree as ET

from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
HISTORY = REPORTS / "history"
JUNIT = REPORTS / "junit.xml"
COVERAGE = REPORTS / "coverage.json"

REPORT_TYPES = {
    "executive": "Executive Quality Dashboard",
    "execution": "Test Execution Report",
    "defects": "Defect & Failure Analysis",
    "code_coverage": "Code Coverage Report",
    "api": "API & MCP Validation",
    "regression": "Regression & Trend Report",
    "release": "Release Readiness Report",
    "evidence": "Detailed Test Evidence",
}


def prepare_directories():
    REPORTS.mkdir(exist_ok=True)
    HISTORY.mkdir(exist_ok=True)

    for folder in REPORT_TYPES:
        (REPORTS / folder).mkdir(exist_ok=True)


def run_tests():
    print("\nRunning MCP_QA pytest suite...\n")

    command = [
        sys.executable,
        "-m", "pytest",
        "-v",
        f"--junitxml={JUNIT}",
        "--cov=src",
        f"--cov-report=json:{COVERAGE}",
        "--cov-report=term-missing",
    ]

    return subprocess.run(command, cwd=ROOT).returncode


def read_test_results():
    if not JUNIT.exists():
        raise FileNotFoundError("JUnit XML was not generated.")

    root = ET.parse(JUNIT).getroot()

    data = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "duration": 0.0,
        "pass_rate": 0,
        "coverage": None,
        "failures": [],
        "tests": [],
    }

    for case in root.iter("testcase"):
        name = case.get("name", "Unknown")
        suite = case.get("classname", "Unknown")
        duration = float(case.get("time", 0) or 0)

        failure = case.find("failure")
        error = case.find("error")
        skipped = case.find("skipped")

        if failure is not None:
            status = "Failed"
            issue = failure
            data["failed"] += 1
        elif error is not None:
            status = "Error"
            issue = error
            data["errors"] += 1
        elif skipped is not None:
            status = "Skipped"
            issue = skipped
            data["skipped"] += 1
        else:
            status = "Passed"
            issue = None
            data["passed"] += 1

        message = ""
        if issue is not None:
            message = (
                issue.get("message", "")
                or (issue.text or "")[:2000]
            )

        combined = f"{suite} {name}".lower()

        if "api" in combined or "endpoint" in combined:
            category = "API"
        elif "mcp" in combined or "server" in combined:
            category = "MCP Server"
        elif "integration" in combined:
            category = "Integration"
        elif "regression" in combined:
            category = "Regression"
        else:
            category = "General"

        record = {
            "suite": suite,
            "name": name,
            "status": status,
            "duration": round(duration, 3),
            "category": category,
            "message": message,
        }

        data["tests"].append(record)
        data["total"] += 1
        data["duration"] += duration

        if status in ("Failed", "Error"):
            data["failures"].append(record)

    executed = data["total"] - data["skipped"]

    data["pass_rate"] = round(
        data["passed"] / executed * 100, 2
    ) if executed else 0

    data["duration"] = round(data["duration"], 2)

    return data


def read_coverage(data):
    if not COVERAGE.exists():
        return

    try:
        result = json.loads(COVERAGE.read_text())
        totals = result.get("totals", {})

        data["coverage"] = totals.get("percent_covered")
        data["covered_lines"] = totals.get("covered_lines")
        data["missing_lines"] = totals.get("missing_lines")

    except (ValueError, OSError) as exc:
        print("Coverage warning:", exc)


def save_history(data):
    history_file = HISTORY / "execution_history.json"

    history = []

    if history_file.exists():
        try:
            history = json.loads(history_file.read_text())
        except (ValueError, OSError):
            history = []

    history.append({
        "generated_at": data["generated_at"],
        "total": data["total"],
        "passed": data["passed"],
        "failed": data["failed"],
        "errors": data["errors"],
        "skipped": data["skipped"],
        "pass_rate": data["pass_rate"],
        "coverage": data["coverage"],
        "duration": data["duration"],
    })

    history = history[-50:]

    history_file.write_text(
        json.dumps(history, indent=2)
    )

    data["history"] = history


def assess_release(data):
    reasons = []

    if data["total"] == 0:
        reasons.append("No tests were executed.")

    if data["failed"] or data["errors"]:
        reasons.append("Test failures or errors detected.")

    if data["skipped"]:
        reasons.append("Skipped tests require review.")

    if data["coverage"] is None:
        reasons.append("Coverage data unavailable.")

    if reasons:
        status = "REVIEW REQUIRED"
    else:
        status = "EXECUTION GATES PASSED"

    return {
        "status": status,
        "reasons": reasons or [
            "All executed tests passed.",
            "No skipped tests recorded.",
            "Coverage data is available.",
            "Other release criteria still require assessment.",
        ],
    }


def safe(value):
    return html.escape(str(value or ""))


def render_report(report_type, data):
    title = REPORT_TYPES[report_type]

    if report_type == "defects":
        records = data["failures"]

    elif report_type == "api":
        records = [
            t for t in data["tests"]
            if t["category"] in ("API", "MCP Server")
        ]

    elif report_type in ("release", "regression", "code_coverage"):
        records = []

    else:
        records = data["tests"]

    rows = ""

    for item in records:
        rows += f"""
        <tr>
          <td>{safe(item['suite'])}</td>
          <td>{safe(item['name'])}</td>
          <td>{safe(item['category'])}</td>
          <td>{safe(item['status'])}</td>
          <td>{item['duration']}s</td>
          <td>{safe(item['message'][:500])}</td>
        </tr>
        """

    if not rows:
        rows = """
        <tr>
          <td colspan="6">No matching test records found.</td>
        </tr>
        """

    coverage = data["coverage"]
    coverage_text = (
        f"{coverage:.1f}%"
        if coverage is not None else "Unavailable"
    )

    assessment = data["release_assessment"]

    history_rows = ""

    for run in data.get("history", []):
        history_rows += f"""
        <tr>
          <td>{safe(run['generated_at'])}</td>
          <td>{run['total']}</td>
          <td>{run['passed']}</td>
          <td>{run['failed'] + run['errors']}</td>
          <td>{run['pass_rate']}%</td>
        </tr>
        """

    if not history_rows:
        history_rows = "<tr><td colspan='5'>No history yet.</td></tr>"

    history_json = json.dumps(
        data.get("history", [])
    ).replace("<", "\\u003c")

    nav = ""

    for key, label in REPORT_TYPES.items():
        nav += (
            f'<a href="../{key}/index.html">'
            f'{safe(label)}</a>'
        )

    coverage_link = ""

    if report_type == "code_coverage":
        coverage_link = """
        <p>
        <a href="../coverage/index.html">
        Open detailed Coverage.py HTML report
        </a>
        </p>
        """

    release_reasons = "".join(
        f"<li>{safe(reason)}</li>"
        for reason in assessment["reasons"]
    )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe(title)} | MCP QA</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f3f6fb;color:#18243b;
font-family:Inter,-apple-system,BlinkMacSystemFont,Arial,sans-serif}}
aside{{position:fixed;top:0;bottom:0;width:225px;
background:#14213d;color:white;padding:25px 16px;overflow-y:auto}}
.brand{{font-size:21px;font-weight:800;margin-bottom:25px}}
aside a{{display:block;color:#d4ddec;text-decoration:none;
padding:11px;border-radius:7px;font-size:12px}}
aside a:hover{{background:#293c68}}
main{{margin-left:225px;padding:30px;max-width:1600px}}
h1{{font-size:27px;margin:0}}
.sub{{color:#77839a;margin:8px 0 25px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}}
.card{{background:white;border-radius:13px;padding:21px;
box-shadow:0 4px 18px #17243b0a;margin-bottom:18px}}
.label{{font-size:11px;color:#7b879a;font-weight:750}}
.value{{font-size:32px;font-weight:800;margin-top:12px}}
.green{{color:#15966b}}.red{{color:#dc4545}}
.content{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
canvas{{max-height:270px}}
.table-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
td,th{{padding:12px;text-align:left;border-bottom:1px solid #edf0f5}}
th{{color:#718096;font-size:11px}}
.notice{{background:#edf3ff;border-left:4px solid #4361ee;
padding:15px;border-radius:7px}}
footer{{margin-top:20px;color:#8994a6;font-size:12px}}
a{{color:#315fc5}}
@media(max-width:950px){{aside{{display:none}}
main{{margin:0;padding:18px}}
.grid{{grid-template-columns:repeat(2,1fr)}}
.content{{grid-template-columns:1fr}}}}
@media(max-width:500px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<aside>
<div class="brand">◈ MCP QA</div>
<a href="../index.html">Reporting Portal</a>
{nav}
</aside>
<main>
<h1>{safe(title)}</h1>
<div class="sub">Enterprise Engineering Quality Reporting</div>

<section class="grid">
<div class="card">
<div class="label">TOTAL TESTS</div>
<div class="value">{data['total']}</div>
</div>
<div class="card">
<div class="label">PASSED</div>
<div class="value green">{data['passed']}</div>
</div>
<div class="card">
<div class="label">FAILED + ERRORS</div>
<div class="value red">{data['failed'] + data['errors']}</div>
</div>
<div class="card">
<div class="label">PASS RATE</div>
<div class="value">{data['pass_rate']}%</div>
</div>
</section>

<div class="content">
<div class="card">
<h3>Test Execution Distribution</h3>
<canvas id="execution"></canvas>
</div>
<div class="card">
<h3>Code Coverage</h3>
<div class="value">{coverage_text}</div>
<canvas id="coverage"></canvas>
{coverage_link}
</div>
</div>

<div class="card">
<h3>Release Assessment</h3>
<div class="notice">{safe(assessment['status'])}</div>
<ul>{release_reasons}</ul>
</div>

<div class="card">
<h3>Test Details</h3>
<div class="table-wrap">
<table>
<thead>
<tr>
<th>SUITE</th><th>TEST</th><th>CATEGORY</th>
<th>STATUS</th><th>DURATION</th><th>DETAILS</th>
</tr>
</thead>
<tbody>{rows}</tbody>
</table>
</div>
</div>

<div class="card">
<h3>Execution History</h3>
<div class="content">
<div><canvas id="trend"></canvas></div>
<div class="table-wrap">
<table>
<thead><tr><th>DATE</th><th>TOTAL</th>
<th>PASSED</th><th>FAILED</th><th>PASS RATE</th></tr></thead>
<tbody>{history_rows}</tbody>
</table>
</div>
</div>
</div>

<footer>
Generated: {safe(data['generated_at'])}
| Source: Pytest JUnit XML and Coverage JSON
</footer>
</main>

<script>
const d = {{
passed: {data['passed']},
failed: {data['failed']},
errors: {data['errors']},
skipped: {data['skipped']},
coverage: {json.dumps(data['coverage'])},
history: {history_json}
}};

new Chart(document.getElementById('execution'), {{
type:'doughnut',
data:{{
labels:['Passed','Failed','Errors','Skipped'],
datasets:[{{
data:[d.passed,d.failed,d.errors,d.skipped],
backgroundColor:['#15966b','#dc4545','#d99532','#94a3b8'],
borderWidth:0
}}]
}},
options:{{plugins:{{legend:{{position:'bottom'}}}}}}
}});

new Chart(document.getElementById('coverage'), {{
type:'doughnut',
data:{{
labels:d.coverage===null?['Unavailable']:['Covered','Remaining'],
datasets:[{{
data:d.coverage===null?[1,0]:[d.coverage,100-d.coverage],
backgroundColor:['#4361ee','#e8edf6'],
borderWidth:0
}}]
}},
options:{{plugins:{{legend:{{position:'bottom'}}}}}}
}});

new Chart(document.getElementById('trend'), {{
type:'line',
data:{{
labels:d.history.map(x=>new Date(x.generated_at).toLocaleDateString()),
datasets:[{{
label:'Pass rate (%)',
data:d.history.map(x=>x.pass_rate),
borderColor:'#4361ee',
backgroundColor:'#4361ee22',
fill:true,
tension:.3
}}]
}},
options:{{scales:{{y:{{beginAtZero:true,max:100}}}}}}
}});
</script>
</body>
</html>"""

    output = REPORTS / report_type / "index.html"
    output.write_text(page, encoding="utf-8")


def render_portal(data):
    cards = ""

    descriptions = {
        "executive": "Leadership KPIs and quality overview",
        "execution": "Test execution and duration analysis",
        "defects": "Failure investigation and error details",
        "code_coverage": "Coverage measurements and source report",
        "api": "API and MCP server validation",
        "regression": "Historical execution trends",
        "release": "Release gates and outstanding risks",
        "evidence": "Detailed test execution evidence",
    }

    for key, title in REPORT_TYPES.items():
        cards += f"""
        <a class="card" href="{key}/index.html">
        <h3>{safe(title)}</h3>
        <p>{safe(descriptions[key])}</p>
        <strong>Open report →</strong>
        </a>
        """

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MCP QA Reporting Center</title>
<style>
body{{margin:0;padding:35px;background:#f3f6fb;
font-family:Inter,Arial,sans-serif;color:#18243b}}
h1{{font-size:30px}}
.sub{{color:#718096}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}
.card{{background:white;padding:24px;border-radius:13px;
text-decoration:none;color:#18243b;
box-shadow:0 4px 18px #17243b0a}}
.card:hover{{transform:translateY(-3px)}}
.card p{{color:#718096;font-size:13px}}
.card strong{{color:#4361ee;font-size:13px}}
@media(max-width:800px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:500px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<h1>◈ MCP QA Reporting Center</h1>
<p class="sub">Enterprise Engineering Quality Platform</p>
<p>Latest execution: {safe(data['generated_at'])}</p>
<p>Tests: {data['total']} |
Passed: {data['passed']} |
Failed: {data['failed'] + data['errors']} |
Pass rate: {data['pass_rate']}%</p>
<div class="grid">{cards}</div>
</body>
</html>"""

    (REPORTS / "index.html").write_text(page, encoding="utf-8")


def main():
    prepare_directories()

    exit_code = run_tests()

    if not JUNIT.exists():
        print("ERROR: No JUnit report was generated.")
        sys.exit(exit_code or 1)

    data = read_test_results()
    read_coverage(data)

    data["generated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    save_history(data)

    data["release_assessment"] = assess_release(data)

    (REPORTS / "executive_metrics.json").write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )

    for report_type in REPORT_TYPES:
        render_report(report_type, data)

    render_portal(data)

    print("\n" + "=" * 50)
    print("MCP QA ENTERPRISE REPORTING COMPLETED")
    print("=" * 50)

    print(f"Total tests : {data['total']}")
    print(f"Passed      : {data['passed']}")
    print(f"Failed      : {data['failed']}")
    print(f"Errors      : {data['errors']}")
    print(f"Skipped     : {data['skipped']}")
    print(f"Pass rate   : {data['pass_rate']}%")
    print(f"Coverage    : {data['coverage']}")

    print("\nREPORT PORTAL: reports/index.html")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()