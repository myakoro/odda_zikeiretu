@echo off
chcp 65001 > nul
cd /d %~dp0

echo ========================================================
echo   データベース ゴミデータ掃除ツール (v1.0)
echo ========================================================
echo.
echo このツールは、「下限 ＞ 上限」という矛盾したオッズデータのみを削除します。
echo 正常なデータや、その他のレース情報は一切消えませんのでご安心ください。
echo.

if not exist .venv32\Scripts\activate.bat (
    echo [ERROR] .venv32 が見つかりません。
    pause
    exit /b
)

call .venv32\Scripts\activate.bat

echo --- 掃除実行中 ---
python -c "import sqlite3; conn = sqlite3.connect('data/odds_history.db'); cur = conn.cursor(); cur.execute('DELETE FROM odds_history WHERE odds_fuku_min > odds_fuku_max AND odds_fuku_max > 0'); print(f'  成功: {cur.rowcount} 件の壊れたデータを削除しました。'); conn.commit(); conn.close()"

echo.
echo 掃除が完了しました。
echo この後「複勝オッズ確認.bat」で確認してみてください。
echo.
echo ========================================================
pause
