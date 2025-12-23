@echo off
chcp 65001 > nul
cd /d %~dp0

echo ========================================================
echo   データ確認ツール
echo ========================================================
echo.
echo レースID 202512210912 の 1番と11番のオッズを確認します...
echo.

call .venv32\Scripts\Activate.bat

python -c "import sqlite3; conn = sqlite3.connect('data/odds_history.db'); cursor = conn.cursor(); cursor.execute('SELECT umaban, odds_tan, odds_fuku_min, odds_fuku_max FROM odds_history WHERE race_id=\"202512210912\" AND umaban IN (1, 11) ORDER BY time_stamp DESC, umaban LIMIT 10'); print('\n'.join([f'馬{r[0]:2d}: 単勝{r[1]:6.1f} 複勝{r[2]:6.1f}-{r[3]:6.1f}' for r in cursor.fetchall()]))"

echo.
echo ========================================================
pause
