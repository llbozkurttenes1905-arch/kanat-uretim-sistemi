@echo off
title ERGUNBAS Kanat Uretim Portali
color 0c
echo ===================================================
echo     ERGUNBAS Group - Kanat Uretim Portali
echo ===================================================
echo.
echo Sistem baslatiliyor (Port: 8001)...
echo.
pip install -r requirements.txt
start http://localhost:8001
python app_backend.py
pause
