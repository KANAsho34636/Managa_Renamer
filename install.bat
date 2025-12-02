@echo off
chcp 65001 > nul
echo ========================================
echo 漫画・書籍画像ファイル連番管理ツール
echo インストールスクリプト
echo ========================================
echo.

echo [1/3] 依存関係の確認...
python --version
if %errorlevel% neq 0 (
    echo エラー: Pythonがインストールされていません
    echo Python 3.8以上をインストールしてください
    pause
    exit /b 1
)
echo.

echo [2/3] llama-cpp-python (GPU版) のインストール...
echo CUDA対応版をビルドします（数分かかる場合があります）
set CMAKE_ARGS=-DGGML_CUDA=on
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
if %errorlevel% neq 0 (
    echo.
    echo 警告: GPU版のインストールに失敗しました
    echo CPU専用版をインストールしますか？ (Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        echo CPU専用版をインストールします...
        pip install llama-cpp-python
    ) else (
        echo インストールを中止しました
        pause
        exit /b 1
    )
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
echo インストール完了！
echo ========================================
echo.
echo アプリケーションを起動するには:
echo   python main.py
echo.
echo または run.bat を実行してください
echo.
pause
