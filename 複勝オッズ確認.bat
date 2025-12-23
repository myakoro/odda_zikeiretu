@echo off
chcp 65001 > nul
cd /d %~dp0

echo ========================================================
echo   複勝オッズ確認ツール (202512210909)
echo ========================================================
echo.

call .venv32\Scripts\Activate.bat

python -c "import sqlite3; conn = sqlite3.connect('data/odds_history.db'); cursor = conn.cursor(); cursor.execute('SELECT time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max FROM odds_history WHERE race_id=\"202512210909\" AND umaban=1 ORDER BY time_stamp DESC LIMIT 10'); print('\n=== 1番の最新10件 ==='); print('\n'.join([f'{r[0]} 馬{r[1]:2d}: 単勝{r[2]:6.1f} 複勝{r[3]:6.1f}-{r[4]:6.1f}' for r in cursor.fetchall()]))"

echo.
echo.
echo ========================================================
pause
