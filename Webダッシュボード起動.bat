@echo off
chcp 65001 > nul
cd /d %~dp0

echo ========================================================
echo   Webダッシュボード起動
echo ========================================================
echo.
echo Webダッシュボードを起動します...
echo ブラウザで http://localhost:5000 を開いてください。
echo.
echo 終了するには Ctrl+C を押してください。
echo.
echo ========================================================

call .venv32\Scripts\Activate.bat
python src/api_server.py

pause
