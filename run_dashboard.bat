@echo off
echo ===========================================================================
echo   CYBERFORGE INCIDENT REPLAY AND GROUND-TRUTH PRD BENCHMARKS
echo ===========================================================================
.\.venv\Scripts\python.exe -m src.killchain.eval.metrics
echo.
echo Launching Executive Dashboard in your browser...
start http://localhost:8000
