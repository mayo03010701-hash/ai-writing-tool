@echo off
cd /d "%~dp0"
echo AI Writing Tool is starting... Browser will open automatically.
echo To stop the app, close this window.
start "" cmd /c "timeout /t 4 /nobreak >nul & start http://localhost:8501"
".venv\Scripts\python.exe" -m streamlit run app.py
pause
