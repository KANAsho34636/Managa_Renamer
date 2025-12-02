@echo off
chcp 65001 > nul
echo ========================================
echo GPU版インストール (RTX 50シリーズ対応)
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

echo [2/3] llama-cpp-python (最新版) のインストール...
echo RTX 50シリーズ対応版をインストールします
echo これは10-20分かかる場合があります...
echo.
set CMAKE_ARGS=-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=native
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --verbose
if %errorlevel% neq 0 (
    echo.
    echo エラー: GPU版のインストールに失敗しました
    echo.
    echo 考えられる原因:
    echo - CUDA Toolkitが古い (12.4以上が必要)
    echo - Visual Studio Build Toolsが未インストール
    echo - CUDA環境変数が設定されていない
    echo.
    echo check_cuda.bat で環境を確認してください
    echo.
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
echo インストール完了！
echo ========================================
echo.
echo GPU版 (RTX 50シリーズ対応) がインストールされました
echo 起動: python main.py または run.bat
echo.
pause
