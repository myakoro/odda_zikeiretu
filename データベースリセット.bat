@echo off
chcp 65001 > nul
cd /d %~dp0

echo ========================================================
echo   データベースリセット
echo ========================================================
echo.
echo 既存のデータベースを削除して、新しくデータを取り込みます。
echo.
pause

if exist data\odds_history.db (
    del data\odds_history.db
    echo データベースを削除しました。
) else (
    echo データベースが見つかりません。
)

echo.
echo 新しいデータベースを作成します...
call .venv32\Scripts\Activate.bat
python src/init_db.py

echo.
echo ========================================================
echo   完了
echo ========================================================
echo.
echo 次は「アプリ起動.bat」でデータを取り込んでください。
echo.
pause
