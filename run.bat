@echo off
chcp 65001 > nul
echo 漫画・書籍画像ファイル連番管理ツールを起動します...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo エラー: アプリケーションの起動に失敗しました
    echo まず install.bat を実行してください
    pause
)
