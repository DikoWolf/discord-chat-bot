@echo off
echo [INFO] Menghentikan bot yang sedang berjalan...
taskkill /F /IM python.exe /T 2>nul
timeout /t 2 /nobreak >nul
echo [INFO] Memulakan bot baru...
python main.py
pause
