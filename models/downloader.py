"""
Hugging FaceからGGUFモデルをダウンロード
"""
from huggingface_hub import hf_hub_download
from pathlib import Path
from typing import Callable, Optional, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelDownloader:
    """Hugging FaceからGGUFモデルをダウンロード"""

    # モデル設定
    MODELS = {
        'qwen3-vl-4b-q4': {
            'repo_id': 'Qwen/Qwen3-VL-4B-Instruct-GGUF',
            'model_file': 'Qwen3VL-4B-Instruct-Q4_K_M.gguf',
            'mmproj_file': 'mmproj-Qwen3VL-4B-Instruct-F16.gguf',
            'size_gb': 3.3  # 2.5GB + 0.8GB mmproj
        },
        'qwen2.5-vl-7b-q4': {
            'repo_id': 'unsloth/Qwen2.5-VL-7B-Instruct-GGUF',
            'model_file': 'Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf',
            'mmproj_file': 'Qwen2.5-VL-7B-Instruct-mmproj-f16.gguf',
            'size_gb': 4.8
        }
    }

    def __init__(self, cache_dir: str = None):
        """
        Args:
            cache_dir: モデル保存ディレクトリ (Noneの場合はconfig.Config.MODEL_CACHE_DIRを使用)
        """
        if cache_dir is None:
            from config import Config
            cache_dir = Config.MODEL_CACHE_DIR

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Model cache directory: {self.cache_dir}")

    def download_model(
        self,
        model_key: str = 'qwen3-vl-4b-q4',
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, str]:
        """
        モデルをダウンロード

        Args:
            model_key: MODELSキー
            progress_callback: 進捗コールバック関数 (filename, downloaded_bytes, total_bytes)

        Returns:
            {'model_path': str, 'mmproj_path': str}

        Raises:
            ValueError: 不明なモデルキー
        """
        if model_key not in self.MODELS:
            raise ValueError(f"Unknown model key: {model_key}. Available: {list(self.MODELS.keys())}")

        config = self.MODELS[model_key]
        repo_id = config['repo_id']

        logger.info(f"Downloading {model_key} from {repo_id}...")
        logger.info(f"Estimated size: {config['size_gb']} GB")

        try:
            # メインモデルファイルをダウンロード
            logger.info(f"Downloading model file: {config['model_file']}...")
            model_path = hf_hub_download(
                repo_id=repo_id,
                filename=config['model_file'],
                cache_dir=str(self.cache_dir),
                resume_download=True
            )
            logger.info(f"Model downloaded: {model_path}")

            # MMPROJファイルをダウンロード
            logger.info(f"Downloading mmproj file: {config['mmproj_file']}...")
            mmproj_path = hf_hub_download(
                repo_id=repo_id,
                filename=config['mmproj_file'],
                cache_dir=str(self.cache_dir),
                resume_download=True
            )
            logger.info(f"MMPROJ downloaded: {mmproj_path}")

            logger.info("Download complete!")
            return {
                'model_path': model_path,
                'mmproj_path': mmproj_path
            }

        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise

    def is_model_downloaded(self, model_key: str) -> bool:
        """
        モデルがダウンロード済みかチェック

        Args:
            model_key: MODELSキー

        Returns:
            ダウンロード済みならTrue
        """
        if model_key not in self.MODELS:
            return False

        config = self.MODELS[model_key]

        # キャッシュディレクトリ内を検索
        model_files = list(self.cache_dir.rglob(config['model_file']))
        mmproj_files = list(self.cache_dir.rglob(config['mmproj_file']))

        is_downloaded = len(model_files) > 0 and len(mmproj_files) > 0

        if is_downloaded:
            logger.info(f"Model {model_key} is already downloaded")
        else:
            logger.info(f"Model {model_key} is not downloaded")

        return is_downloaded

    def get_model_paths(self, model_key: str) -> Optional[Dict[str, str]]:
        """
        ダウンロード済みモデルのパスを取得

        Args:
            model_key: MODELSキー

        Returns:
            {'model_path': str, 'mmproj_path': str} or None
        """
        if not self.is_model_downloaded(model_key):
            logger.warning(f"Model {model_key} is not downloaded")
            return None

        config = self.MODELS[model_key]

        model_path = list(self.cache_dir.rglob(config['model_file']))[0]
        mmproj_path = list(self.cache_dir.rglob(config['mmproj_file']))[0]

        paths = {
            'model_path': str(model_path),
            'mmproj_path': str(mmproj_path)
        }

        logger.info(f"Model paths: {paths}")
        return paths

    def get_model_info(self, model_key: str) -> Optional[Dict]:
        """
        モデル情報を取得

        Args:
            model_key: MODELSキー

        Returns:
            モデル設定情報
        """
        return self.MODELS.get(model_key)

    def list_available_models(self) -> list:
        """
        利用可能なモデルキーのリストを取得

        Returns:
            モデルキーのリスト
        """
        return list(self.MODELS.keys())
