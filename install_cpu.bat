@echo off
chcp 65001 > nul
echo ========================================
echo 漫画・書籍画像ファイル連番管理ツール
echo インストールスクリプト (CPU専用版)
echo ========================================
echo.

echo [1/3] Python確認...
python --version
if %errorlevel% neq 0 (
    echo エラー: Pythonがインストールされていません
    pause
    exit /b 1
)
echo.

echo [2/3] llama-cpp-python (CPU専用版) のインストール...
echo これは数分かかる場合があります...
pip install llama-cpp-python --upgrade
if %errorlevel% neq 0 (
    echo エラー: llama-cpp-pythonのインストールに失敗しました
    pause
    exit /b 1
)
echo.

echo [3/3] その他の依存関係のインストール...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo エラー: 依存関係のインストールに失敗しました
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
