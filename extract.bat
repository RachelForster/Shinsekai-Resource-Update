@echo off
setlocal
python "%~dp0extract_characters.py"
if %ERRORLEVEL% neq 0 pause
endlocal

pause
