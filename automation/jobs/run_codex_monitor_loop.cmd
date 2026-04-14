@echo off
setlocal

cd /d C:\Users\admin\Desktop\Clear-agro

:loop
python scripts\update_codex_monitor.py --publish-remote fork
timeout /t 900 /nobreak >nul
goto loop
