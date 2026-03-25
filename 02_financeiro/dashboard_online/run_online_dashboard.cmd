@echo off
cd /d C:\Users\cesar.zarovski\Documents\Clear_OS\02_financeiro
set PYTHON_EXE=C:\Users\cesar.zarovski\AppData\Local\Programs\Python\Python312\python.exe
"%PYTHON_EXE%" dashboard_online\build_snapshot.py
start "Finance Dashboard Online" cmd /k ""%PYTHON_EXE%" -m streamlit run dashboard_online\app.py --server.address 127.0.0.1 --server.port 8511 --server.headless true"
timeout /t 6 /nobreak >nul
start "" "http://127.0.0.1:8511"
