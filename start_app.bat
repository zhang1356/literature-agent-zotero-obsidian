@echo off
setlocal

cd /d "D:\codexproject\literature-agent-zotero-obsidian"
if errorlevel 1 (
  echo Failed to enter project directory.
  pause
  exit /b 1
)

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
) else (
  echo .venv not found. Using current Python environment.
)

streamlit run app.py
if errorlevel 1 (
  echo Streamlit failed to start.
  pause
  exit /b 1
)

pause
