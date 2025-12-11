@echo off
chcp 65001 > nul
cd /d %~dp0

:MENU
cls
echo ========================================================
echo   投資競馬オッズ取得アプリ - ランチャー
echo ========================================================
echo.
echo   [1] 過去データを取得する (collector.py)
echo   [2] リアルタイム監視を開始する (realtime_monitor.py)
echo   [3] 設定ファイル(.env)を開く
echo   [9] 終了
echo.
echo ========================================================
set /p sel="選択してください > "

if "%sel%"=="1" goto COLLECTOR
if "%sel%"=="2" goto MONITOR
if "%sel%"=="3" goto EDIT_ENV
if "%sel%"=="9" goto END

goto MENU

:COLLECTOR
cls
echo 過去データ取得を開始します...
call .venv32\Scripts\Activate.bat
python src/collector.py
pause
goto MENU

:MONITOR
cls
echo リアルタイム監視を開始します...
echo (終了するには Ctrl+C を押してください)
call .venv32\Scripts\Activate.bat
python src/realtime_monitor.py
pause
goto MENU

:EDIT_ENV
notepad .env
goto MENU

:END
exit
