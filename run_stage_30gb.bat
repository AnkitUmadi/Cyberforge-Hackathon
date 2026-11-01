@echo off
.\.venv\Scripts\python.exe scripts\switch_dataset.py 30gb
start http://localhost:8000
