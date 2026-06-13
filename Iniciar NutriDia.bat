@echo off
cd /d "%~dp0"
echo A iniciar o NutriDia... (abre no browser)
.venv\Scripts\streamlit.exe run app.py
pause
