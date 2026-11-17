from mcp.server.fastmcp import FastMCP

mcp = FastMCP("QA Leadership MCP")


@mcp.tool()
def calculate_automation_metrics(
    total_tests: int,
    automated_tests: int,
    stable_automated_tests: int,
    passed_tests: int,
    failed_tests: int,
) -> dict:
    """Calculate automation coverage, stability and pass rate."""

    if total_tests <= 0:
        raise ValueError("Total tests must be positive")

    if not 0 <= stable_automated_tests <= automated_tests <= total_tests:
        raise ValueError("Invalid automation counts")

    if min(passed_tests, failed_tests) < 0:
        raise ValueError("Execution counts cannot be negative")

    if passed_tests + failed_tests > total_tests:
        raise ValueError("Executed tests exceed total tests")

    executed = passed_tests + failed_tests

    return {
        "total_tests": total_tests,
        "automation_coverage": round(automated_tests / total_tests * 100, 2),
        "stable_automation_coverage": round(stable_automated_tests / total_tests * 100, 2),
        "automation_stability": round(stable_automated_tests / automated_tests * 100, 2) if automated_tests else 0,
        "execution_pass_rate": round(passed_tests / executed * 100, 2) if executed else None,
        "failed_tests": failed_tests,
    }


@mcp.tool()
def assess_release_readiness(
    total_tests: int,
    passed_tests: int,
    failed_tests: int,
    critical_test_failures: int,
    open_sev1_defects: int,
    open_sev2_defects: int,
    rollback_plan_tested: bool,
    minimum_pass_rate: float = 98.0,
) -> dict:
    """Evaluate release readiness against quality criteria."""

    counts = [
        total_tests, passed_tests, failed_tests,
        critical_test_failures, open_sev1_defects, open_sev2_defects,
    ]

    if any(value < 0 for value in counts):
        raise ValueError("Counts cannot be negative")

    if total_tests <= 0:
        raise ValueError("Total tests must be positive")

    if passed_tests + failed_tests > total_tests:
        raise ValueError("Execution counts exceed total tests")

    if critical_test_failures > failed_tests:
        raise ValueError("Critical failures cannot exceed failed tests")

    if not 0 <= minimum_pass_rate <= 100:
        raise ValueError("Minimum pass rate must be between 0 and 100")

    executed = passed_tests + failed_tests
    pass_rate = passed_tests / executed * 100 if executed else 0

    blockers = []
    warnings = []

    if open_sev1_defects > 0:
        blockers.append("Open Sev-1 defects")

    if critical_test_failures > 0:
        blockers.append("Critical business test failures")

    if pass_rate < minimum_pass_rate:
        blockers.append("Regression pass rate below threshold")

    if open_sev2_defects > 0:
        warnings.append("Open Sev-2 defects require risk review")

    if not rollback_plan_tested:
        warnings.append("Rollback plan has not been tested")

    status = (
        "NOT_READY" if blockers
        else "READY_WITH_RISKS" if warnings
        else "READY"
    )

    return {
        "release_readiness": status,
        "execution_pass_rate": round(pass_rate, 2),
        "blockers": blockers,
        "warnings": warnings,
    }


@mcp.tool()
def calculate_defect_escape_rate(
    pre_release_defects: int,
    production_defects: int,
) -> dict:
    """Calculate production defect escape rate."""

    if min(pre_release_defects, production_defects) < 0:
        raise ValueError("Defect counts cannot be negative")

    total = pre_release_defects + production_defects

    return {
        "pre_release_defects": pre_release_defects,
        "production_defects": production_defects,
        "defect_escape_rate": round(production_defects / total * 100, 2) if total else None,
    }


@mcp.tool()
def score_test_risk(
    business_impact: int,
    failure_likelihood: int,
    change_exposure: int,
) -> dict:
    """Prioritize testing using a 1-5 risk scoring model."""

    scores = [business_impact, failure_likelihood, change_exposure]

    if any(score < 1 or score > 5 for score in scores):
        raise ValueError("All risk scores must be between 1 and 5")

    risk_score = business_impact * failure_likelihood * change_exposure

    if risk_score >= 60:
        priority = "CRITICAL"
    elif risk_score >= 30:
        priority = "HIGH"
    elif risk_score >= 10:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    recommendations = {
        "CRITICAL": "Prioritize immediate testing.",
        "HIGH": "Include in priority regression testing.",
        "MEDIUM": "Include in planned regression testing.",
        "LOW": "Consider lower-priority exploratory testing.",
    }

    return {
        "risk_score": risk_score,
        "priority": priority,
        "recommendation": recommendations[priority],
    }


if __name__ == "__main__":
    mcp.run()
