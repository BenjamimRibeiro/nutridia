@echo off
cd /d "%~dp0"
title NutriDia - Partilhar
echo ===================================================
echo            NutriDia - Partilhar com um amigo
echo ===================================================
echo.
echo  A arrancar a app no teu PC...
start "NutriDia" /min ".venv\Scripts\streamlit.exe" run app.py --server.port 8501 --server.headless true
echo  A preparar o link publico (aguarda uns segundos)...
timeout /t 8 /nobreak >nul
echo.
echo  ^>^>^>  O LINK aparece JA A SEGUIR (https://....trycloudflare.com)  ^<^<^<
echo.
echo        Copia esse link e envia-o ao teu amigo.
echo        Para TERMINAR a partilha: fecha esta janela.
echo        (assim que fechas, o link deixa de funcionar)
echo.
echo ===================================================
echo.
cloudflared.exe tunnel --url http://localhost:8501
echo.
echo  Partilha terminada. Podes fechar esta janela.
pause
