import pytest

from mcpqaauto.server import (
    calculate_automation_metrics,
    assess_release_readiness,
    calculate_defect_escape_rate,
    score_test_risk,
)


def test_automation_metrics():
    result = calculate_automation_metrics(1200, 720, 540, 650, 70)

    assert result["automation_coverage"] == 60.0
    assert result["stable_automation_coverage"] == 45.0
    assert result["automation_stability"] == 75.0
    assert result["execution_pass_rate"] == 90.28


def test_automation_invalid_input():
    with pytest.raises(ValueError):
        calculate_automation_metrics(100, 50, 60, 40, 10)


def test_release_not_ready():
    result = assess_release_readiness(
        total_tests=1000,
        passed_tests=950,
        failed_tests=50,
        critical_test_failures=3,
        open_sev1_defects=2,
        open_sev2_defects=4,
        rollback_plan_tested=False,
    )

    assert result["release_readiness"] == "NOT_READY"
    assert len(result["blockers"]) == 2
    assert len(result["warnings"]) == 2


def test_release_ready():
    result = assess_release_readiness(
        total_tests=100,
        passed_tests=100,
        failed_tests=0,
        critical_test_failures=0,
        open_sev1_defects=0,
        open_sev2_defects=0,
        rollback_plan_tested=True,
    )

    assert result["release_readiness"] == "READY"


def test_defect_escape_rate():
    result = calculate_defect_escape_rate(85, 15)

    assert result["defect_escape_rate"] == 15.0


def test_no_defects():
    result = calculate_defect_escape_rate(0, 0)

    assert result["defect_escape_rate"] is None


def test_critical_test_risk():
    result = score_test_risk(5, 4, 5)

    assert result["risk_score"] == 100
    assert result["priority"] == "CRITICAL"


def test_invalid_risk_score():
    with pytest.raises(ValueError):
        score_test_risk(6, 4, 5)