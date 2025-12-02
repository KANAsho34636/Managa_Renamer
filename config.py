"""
アプリケーション設定ファイル
"""
import os
from pathlib import Path

class Config:
    """アプリケーション設定"""

    # プロジェクトパス
    PROJECT_DIR = Path(__file__).parent.absolute()
    MODEL_CACHE_DIR = PROJECT_DIR / 'models'
    LOG_DIR = PROJECT_DIR / 'logs'

    # モデル設定
    MODEL_KEY = 'qwen3-vl-4b-q4'

    # GPU/CPU設定
    # torchがインストールされていない場合はCPUを使用
    try:
        import torch
        USE_GPU = torch.cuda.is_available()
    except ImportError:
        USE_GPU = False

    N_GPU_LAYERS = -1 if USE_GPU else 0  # -1: 全レイヤーGPU, 0: CPU専用
    N_THREADS = 8  # CPUスレッド数

    # 分析設定（バランス型）
    N_CTX = 4096  # コンテキストウィンドウサイズ
    TEMPERATURE = 0.3  # 生成温度 (低いほど決定論的)
    MAX_TOKENS = 512  # 最大生成トークン数

    # 画像設定
    IMAGE_RESIZE_MAX = (1024, 1024)  # VLMに送信する前のリサイズサイズ
    PREVIEW_SIZE = (400, 500)  # プレビュー表示サイズ
    THUMBNAIL_SIZE = (128, 128)  # サムネイルサイズ
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']

    # リネーム設定
    DEFAULT_PREFIX = 'page_'
    DEFAULT_DIGITS = 3  # 連番の桁数（例: 001, 002, ...）
    AUTO_BACKUP = True  # リネーム前に自動バックアップを作成

    # ペア比較設定
    ENABLE_COMPARISON_CACHE = True  # 比較結果をキャッシュして高速化

    @classmethod
    def ensure_directories(cls):
        """必要なディレクトリを作成"""
        cls.MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
