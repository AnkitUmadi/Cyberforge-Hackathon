@echo off
.\.venv\Scripts\python.exe scripts\switch_dataset.py baseline
start http://localhost:8000
