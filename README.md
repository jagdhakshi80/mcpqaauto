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


uv add --dev pytest-html

uv run --active pytest --cov=mcpqaauto --cov-report=html:reports/coverage --cov-report=term-missing

open reports/coverage/index.html

 asyncio_default_fixture_loop_scope = "function"
pytest
uv run pytest

uv run python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('TOML configuration OK')"

mkdir -p reports/history

uv run pytest

uv run python -m reporting.executive_report

uv run --active pytest \
  --junitxml=reports/junit.xml \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=json:reports/coverage.json

  uv add pytest-cov

  ls -lh reports/

  uv run --active python -m reporting.executive_report

  cat reports/executive_metrics.json

  uv run --active pytest \
  --junitxml=reports/junit.xml \
  --cov=src \
  --cov-report=json:reports/coverage.json

  python3 -m http.server 8000

  http://localhost:8000/reports/executive_dashboard.html?utm_source=chatgpt.com

  