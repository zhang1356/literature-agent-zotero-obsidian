@echo off
setlocal
call :settitle 5paH54yu5qOA57Si5pm66IO95L2TIC0g5a6J6KOF

set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%app.py" (
  cd /d "%SCRIPT_DIR%"
) else (
  cd /d "%SCRIPT_DIR%.."
)

call :say 5q2j5Zyo5qOA5p+lIFB5dGhvbi4uLg==
python --version >nul 2>&1
if errorlevel 1 (
  call :say 5pyq5qOA5rWL5YiwIFB5dGhvbuOAguivt+WFiOWuieijhSBQeXRob24gMy4xMCDmiJbmm7TmlrDniYjmnKzjgII=
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
  call :say UHl0aG9uIOeJiOacrOi/h+S9juOAguivt+WuieijhSBQeXRob24gMy4xMCDmiJbmm7TmlrDniYjmnKzjgII=
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  call :say 5q2j5Zyo5Yib5bu66Jma5ouf546v5aKDLi4u
  python -m venv .venv
  if errorlevel 1 (
    call :say 5Yib5bu66Jma5ouf546v5aKD5aSx6LSl44CC
    pause
    exit /b 1
  )
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  call :say 5L6d6LWW5a6J6KOF5aSx6LSl44CC
  pause
  exit /b 1
)

if not exist "config" mkdir "config"
if not exist "data" mkdir "data"
if not exist "logs" mkdir "logs"
if not exist "config\user_config.json" (
  copy "config\user_config.example.json" "config\user_config.json" >nul
)

call :say 5a6J6KOF5a6M5oiQ77yM6K+36L+Q6KGMIHN0YXJ0LmJhdOOAgg==
pause
exit /b 0

:say
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$s='%~1'; while($s.Length %% 4){$s+='='}; [Console]::OutputEncoding=[Text.Encoding]::UTF8; [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($s))"') do echo %%i
exit /b 0

:settitle
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$s='%~1'; while($s.Length %% 4){$s+='='}; [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($s))"') do title %%i
exit /b 0
