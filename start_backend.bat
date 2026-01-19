@echo off
cd veritas
uv run uvicorn veritas.api.main:app --reload
pause