@echo off
cd /d "%~dp0"
echo A fechar instancias antigas do NutriDia (se houver)...
rem Fecha qualquer servidor que ja esteja na porta 8501, para nao acumular
rem varios servidores (o que faz o browser mostrar codigo antigo).
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
echo A iniciar o NutriDia... (abre no browser)
.venv\Scripts\streamlit.exe run app.py
pause
