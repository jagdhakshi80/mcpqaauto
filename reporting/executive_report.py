
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

REPORTS = Path("reports")

def generate_executive_report():
    junit_file = REPORTS / "junit.xml"

    if not junit_file.exists():
        raise FileNotFoundError(
            "junit.xml not found. Run uv run pytest first."
        )

    root = ET.parse(junit_file).getroot()
    suites = (
        [root] if root.tag == "testsuite"
        else root.findall(".//testsuite")
    )

    metrics = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "duration": 0.0,
        "failures": []
    }

    for suite in suites:
        metrics["total"] += int(suite.get("tests", 0))
        metrics["failed"] += int(suite.get("failures", 0))
        metrics["errors"] += int(suite.get("errors", 0))
        metrics["skipped"] += int(suite.get("skipped", 0))
        metrics["duration"] += float(suite.get("time", 0))

        for case in suite.findall("testcase"):
            issue = case.find("failure")
            if issue is None:
                issue = case.find("error")

            if issue is not None:
                metrics["failures"].append({
                    "test": case.get("name"),
                    "suite": case.get("classname"),
                    "message": issue.get("message", "Test failure")
                })

    metrics["passed"] = (
        metrics["total"] - metrics["failed"]
        - metrics["errors"] - metrics["skipped"]
    )

    executed = metrics["total"] - metrics["skipped"]

    metrics["pass_rate"] = round(
        metrics["passed"] / executed * 100, 2
    ) if executed else 0

    metrics["generated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    coverage_file = REPORTS / "coverage.json"

    if coverage_file.exists():
        coverage = json.loads(coverage_file.read_text())
        metrics["coverage"] = coverage.get(
            "totals", {}
        ).get("percent_covered", 0)
    else:
        metrics["coverage"] = None

    output = REPORTS / "executive_metrics.json"
    output.write_text(json.dumps(metrics, indent=2))

    print("Executive report generated:", output)
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    generate_executive_report()

