@echo off
chcp 65001 > nul
cd /d %~dp0

echo ========================================================
echo   データ保存状況 確認ツール (v0.85)
echo ========================================================
echo.

if not exist .venv32\Scripts\activate.bat (
    echo [ERROR] .venv32 が見つかりません。
    pause
    exit /b
)

call .venv32\Scripts\activate.bat

echo --- 保存状況サマリー (オッズデータから集計) ---
python -c "import sqlite3; conn = sqlite3.connect('data/odds_history.db'); cur = conn.cursor(); rows = cur.execute(\"SELECT substr(race_id, 1, 6) as month, COUNT(DISTINCT race_id) FROM odds_history GROUP BY month ORDER BY month DESC\").fetchall(); [print(f'  {r[0][0:4]}年{r[0][4:6]}月: {r[1]} レース分のオッズを保存済み') for r in rows]"
echo.

echo --- 直近で保存されたデータの確認 ---
python -c "import sqlite3; conn = sqlite3.connect('data/odds_history.db'); cur = conn.cursor(); rid = cur.execute(\"SELECT race_id FROM odds_history ORDER BY rowid DESC LIMIT 1\").fetchone(); rid = rid[0] if rid else 'なし'; print('  最後に書き込まれたレースID:', rid); print('\n  === 1番の最新10件 ==='); rows = cur.execute('SELECT time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max FROM odds_history WHERE race_id=? AND umaban=1 ORDER BY time_stamp DESC LIMIT 10', (rid,)).fetchall() if rid != 'なし' else []; [print(f'  {r[0]} 馬{r[1]:2d}: 単勝{r[2]:6.1f} 複勝{r[3]:6.1f}-{r[4]:6.1f}') for r in rows]"

echo.
echo ※以前の「変な数字」が残っている場合は、新しく取得し直すと正しい値になります。
echo ========================================================
pause
