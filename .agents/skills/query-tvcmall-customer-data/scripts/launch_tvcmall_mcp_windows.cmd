@echo off
setlocal

set "TVCMALL_SETUP_SCRIPT=%~dp0configure_tvcmall_mcp_windows.ps1"
set "TVCMALL_PWSH="

call :select_powershell_7 "%ProgramFiles%\PowerShell\7\pwsh.exe"
if defined TVCMALL_PWSH goto run_powershell_7
call :select_powershell_7 "%ProgramW6432%\PowerShell\7\pwsh.exe"
if defined TVCMALL_PWSH goto run_powershell_7
call :select_powershell_7 "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe"
if not defined TVCMALL_PWSH goto windows_powershell

:run_powershell_7
"%TVCMALL_PWSH%" -NoProfile -STA -ExecutionPolicy Bypass -File "%TVCMALL_SETUP_SCRIPT%"
exit /b %ERRORLEVEL%

:windows_powershell
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -STA -ExecutionPolicy Bypass -File "%TVCMALL_SETUP_SCRIPT%"
exit /b %ERRORLEVEL%

:select_powershell_7
if not exist "%~1" exit /b 0
set "TVCMALL_PWSH_PROBE="
for /f "delims=" %%V in ('""%~1" -NoLogo -NoProfile -NonInteractive -Command "$PSVersionTable.PSVersion.Major -ge 7" 2^>nul"') do set "TVCMALL_PWSH_PROBE=%%V"
if not "%TVCMALL_PWSH_PROBE%"=="True" exit /b 0
set "TVCMALL_PWSH=%~1"
exit /b 0
