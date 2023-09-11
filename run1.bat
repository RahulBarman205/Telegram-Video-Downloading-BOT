@echo off
setlocal enabledelayedexpansion

:: Start the first Python program in the background
start python meow.py

:: Store the PID (Process ID) of the first Python program
for /f "tokens=*" %%a in ('tasklist /v ^| findstr /i "python meow.py"') do (
    set "process_info=%%a"
    for /f "tokens=2 delims= " %%b in (!process_info!) do (
        set "python_pid=%%b"
    )
)

:: Monitor terminal output for new text
set "previous_output="
:monitor_terminal
:: Capture the current terminal output
for /f "delims=" %%a in ('tasklist /v ^| findstr /i "python meow.py"') do (
    set "current_output=%%a"
    set "current_output=!current_output:*python meow.py=!"
    set "current_output=!current_output:~0,-1!"
)

:: Check if the terminal output has changed
if not "!current_output!"=="!previous_output!" (
    :: Kill the Python program
    taskkill /f /pid !python_pid!
) else (
    :: Delay for a short time and continue monitoring
    timeout /t 1 /nobreak >nul
    goto monitor_terminal
)

:: Run the second Python program
python telegram_youtube_downloader -k 6565741324:AAHn4lF4Ysx9AJYI2yfIscWhshzeov7DMZY

:: End the script
exit /b