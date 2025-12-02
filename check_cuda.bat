@echo off
chcp 65001 > nul
echo ========================================
echo CUDA環境確認スクリプト
echo ========================================
echo.

echo [1] NVIDIA GPU確認:
nvidia-smi
echo.

echo [2] CUDA Toolkitバージョン:
nvcc --version
echo.

echo [3] 環境変数CUDA_PATH:
echo %CUDA_PATH%
echo.

echo ========================================
echo 推奨環境:
echo - CUDA Toolkit 12.4以上
echo - RTX 50シリーズ (Blackwell) 対応
echo ========================================
pause
