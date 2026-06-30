@echo off
setlocal
call :settitle 5paH54yu5qOA57Si5pm66IO95L2TIC0g5YGc5q2i

set "STOPPED=0"
for %%p in (8501 8502) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p" ^| findstr "LISTENING"') do (
    call :say 5q2j5Zyo5YGc5q2i5Y2g55SoIDg1MDEg56uv5Y+j55qE6L+b56iL
    echo port %%p pid %%a
    taskkill /PID %%a /F
    if errorlevel 1 (
      call :say 5YGc5q2i5aSx6LSl77yM6K+35omL5Yqo5YWz6Zet5a+55bqU56qX5Y+j44CC
      pause
      exit /b 1
    )
    set "STOPPED=1"
  )
)

if "%STOPPED%"=="1" (
  call :say 5bey5YGc5q2i44CC
) else (
  call :say 5pyq5Y+R546w5Y2g55SoIDg1MDEg56uv5Y+j55qE5pyN5Yqh44CC
)
pause
exit /b 0

:say
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$s='%~1'; while($s.Length %% 4){$s+='='}; [Console]::OutputEncoding=[Text.Encoding]::UTF8; [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($s))"') do echo %%i
exit /b 0

:settitle
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$s='%~1'; while($s.Length %% 4){$s+='='}; [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($s))"') do title %%i
exit /b 0
