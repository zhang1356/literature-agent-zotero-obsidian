@echo off
setlocal
call :settitle 5paH54yu5qOA57Si5pm66IO95L2T

set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%app.py" (
  cd /d "%SCRIPT_DIR%"
) else (
  cd /d "%SCRIPT_DIR%.."
)

if not exist ".venv\Scripts\python.exe" (
  call :say 5pyq5om+5Yiw6Jma5ouf546v5aKD44CC6K+35YWI5Y+M5Ye7IHNldHVwLmJhdOOAgg==
  pause
  exit /b 1
)

if not exist "config" mkdir "config"
if not exist "data" mkdir "data"
if not exist "logs" mkdir "logs"
if not exist "config\user_config.json" (
  copy "config\user_config.example.json" "config\user_config.json" >nul
)

set "PORT=8501"
netstat -ano | findstr ":8501" | findstr "LISTENING" >nul
if not errorlevel 1 (
  call :say 56uv5Y+jIDg1MDEg5bey6KKr5Y2g55So77yM5bCG6Ieq5Yqo5pS555SoIDg1MDLjgII=
  set "PORT=8502"
)

start "" cmd /c "timeout /t 3 >nul & start http://localhost:%PORT%"
".venv\Scripts\python.exe" -m streamlit run app.py --server.port %PORT%
exit /b %ERRORLEVEL%

:say
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$s='%~1'; while($s.Length %% 4){$s+='='}; [Console]::OutputEncoding=[Text.Encoding]::UTF8; [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($s))"') do echo %%i
exit /b 0

:settitle
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$s='%~1'; while($s.Length %% 4){$s+='='}; [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($s))"') do title %%i
exit /b 0
