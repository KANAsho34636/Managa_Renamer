@echo off
chcp 65001 > nul
echo ========================================
echo 漫画・書籍画像ファイル連番管理ツール
echo インストールスクリプト (CPU専用版)
echo ========================================
echo.

echo [1/2] Python確認...
python --version
if %errorlevel% neq 0 (
    echo エラー: Pythonがインストールされていません
    pause
    exit /b 1
)
echo.

echo [2/2] 依存関係のインストール (CPU専用版)...
echo これは数分かかる場合があります...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo エラー: インストールに失敗しました
    pause
    exit /b 1
)
echo.

echo ========================================
echo インストール完了！ (CPU専用版)
echo ========================================
echo.
echo 注意: CPU専用版は処理が遅くなります
echo GPU版が必要な場合は install.bat を使用してください
echo.
echo 起動: python main.py または run.bat
echo.
pause
