# mcpqaauto
python -m py_compile src/mcpqaauto/server.py
uv run --active python -c "from mcpqaauto.server import mcp; print('QA Leadership MCP imported successfully')"

uv run --active python - <<'PY'
from mcpqaauto.server import (
    calculate_automation_metrics,
    assess_release_readiness,
    calculate_defect_escape_rate,
    score_test_risk,
)

print("\n1. AUTOMATION METRICS")
print(calculate_automation_metrics(1000, 800, 760, 950, 50))

print("\n2. RELEASE READINESS")
print(assess_release_readiness(1000, 990, 10, 0, 0, 2, True))

print("\n3. DEFECT ESCAPE RATE")
print(calculate_defect_escape_rate(80, 20))

print("\n4. TEST RISK SCORE")
print(score_test_risk(5, 4, 5))
PY


uv run --active pytest -v