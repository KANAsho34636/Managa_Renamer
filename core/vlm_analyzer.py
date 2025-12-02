"""
Vision Language Modelを使用した画像分析エンジン
"""
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
from PIL import Image
import base64
from io import BytesIO
from typing import List, Dict, Callable, Optional
from functools import cmp_to_key
from pathlib import Path
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


class VLMAnalyzer:
    """Vision Language Modelを使用した画像分析エンジン"""

    def __init__(self, model_path: str, mmproj_path: str,
                 n_ctx: int = None, n_gpu_layers: int = None, n_threads: int = None):
        """
        Args:
            model_path: メインGGUFモデルのパス
            mmproj_path: MMPROJファイルのパス
            n_ctx: コンテキストウィンドウサイズ (Noneの場合はConfig値を使用)
            n_gpu_layers: GPUに配置するレイヤー数 (-1で全て、Noneの場合はConfig値を使用)
            n_threads: CPUスレッド数 (Noneの場合はConfig値を使用)
        """
        self.model_path = model_path
        self.mmproj_path = mmproj_path

        # 設定値
        self.n_ctx = n_ctx if n_ctx is not None else Config.N_CTX
        self.n_gpu_layers = n_gpu_layers if n_gpu_layers is not None else Config.N_GPU_LAYERS
        self.n_threads = n_threads if n_threads is not None else Config.N_THREADS

        # 比較結果のキャッシュ
        self.comparison_cache = {}

        logger.info(f"Initializing VLMAnalyzer...")
        logger.info(f"Model: {model_path}")
        logger.info(f"MMPROJ: {mmproj_path}")
        logger.info(f"GPU layers: {self.n_gpu_layers}")
        logger.info(f"Context size: {self.n_ctx}")
        logger.info(f"CPU threads: {self.n_threads}")

        try:
            # Qwen2-VL用のチャットハンドラーを設定
            logger.info("Loading chat handler...")
            self.chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)

            # モデルのロード
            logger.info("Loading model...")
            self.llm = Llama(
                model_path=model_path,
                chat_handler=self.chat_handler,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                n_threads=self.n_threads,
                verbose=False
            )

            logger.info("VLMAnalyzer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize VLMAnalyzer: {e}")
            raise

    def analyze_image(self, image_path: str) -> Dict:
        """
        単一画像を分析して内容を説明

        Args:
            image_path: 分析対象の画像パス

        Returns:
            分析結果を含む辞書
            {
                'description': str,  # 画像の説明
                'is_manga_page': bool,  # 漫画ページかどうか
                'confidence': float  # 信頼度 (0.0-1.0)
            }
        """
        logger.info(f"Analyzing image: {image_path}")

        # 画像をbase64エンコード
        image_data_uri = self._image_to_data_uri(image_path)

        # プロンプト構築
        prompt = """この画像を分析して、以下の情報を提供してください:
1. これは漫画のページですか? (はい/いいえ)
2. 画像の内容を簡潔に説明してください。
3. シーンの時系列的な位置（序盤/中盤/終盤/不明）を推測してください。

簡潔に答えてください。"""

        try:
            # チャット形式でのリクエスト
            response = self.llm.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_data_uri}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS
            )

            # レスポンスの取得
            content = response['choices'][0]['message']['content']
            logger.info(f"Analysis result: {content[:100]}...")

            return {
                'description': content,
                'is_manga_page': 'はい' in content or 'Yes' in content or '漫画' in content,
                'confidence': 0.8  # 仮の値
            }

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                'description': f"分析エラー: {str(e)}",
                'is_manga_page': False,
                'confidence': 0.0
            }

    def compare_images_order(self, img1_path: str, img2_path: str) -> int:
        """
        2つの画像を比較して、どちらが先に来るべきかを判定

        Args:
            img1_path: 1つ目の画像パス
            img2_path: 2つ目の画像パス

        Returns:
            -1: img1が先, 0: 同順, 1: img2が先
        """
        # キャッシュチェック
        cache_key = (img1_path, img2_path)
        reverse_cache_key = (img2_path, img1_path)

        if Config.ENABLE_COMPARISON_CACHE:
            if cache_key in self.comparison_cache:
                logger.debug(f"Using cached comparison result for {Path(img1_path).name} vs {Path(img2_path).name}")
                return self.comparison_cache[cache_key]

            if reverse_cache_key in self.comparison_cache:
                logger.debug(f"Using reversed cached comparison result for {Path(img1_path).name} vs {Path(img2_path).name}")
                return -self.comparison_cache[reverse_cache_key]

        logger.info(f"Comparing: {Path(img1_path).name} vs {Path(img2_path).name}")

        prompt = """これら2つの画像を比較して、時系列的にどちらが先に来るべきか判定してください。

漫画のページや書籍の内容として、物語の流れを考慮して判定してください。

回答は以下のいずれかの数字のみで答えてください:
-1: 最初の画像が先
0: 順序が不明または同順
1: 2番目の画像が先

数字のみで回答してください。"""

        try:
            # 両画像をbase64エンコード
            img1_uri = self._image_to_data_uri(img1_path)
            img2_uri = self._image_to_data_uri(img2_path)

            response = self.llm.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": img1_uri}},
                            {"type": "image_url", "image_url": {"url": img2_uri}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                temperature=0.1,  # より決定論的に
                max_tokens=10
            )

            # レスポンスから数値を抽出
            content = response['choices'][0]['message']['content'].strip()
            logger.info(f"Comparison result: {content}")

            # 数値の抽出を試みる
            result = 0
            if '-1' in content:
                result = -1
            elif '1' in content and '-1' not in content:
                result = 1
            else:
                result = 0

            # キャッシュに保存
            if Config.ENABLE_COMPARISON_CACHE:
                self.comparison_cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            return 0  # エラー時はデフォルトで同順

    def sort_images_by_content(self, image_paths: List[str],
                                progress_callback: Optional[Callable[[int, int], None]] = None) -> List[str]:
        """
        ペア比較に基づいて画像を時系列順にソート

        Args:
            image_paths: 画像パスのリスト
            progress_callback: 進捗コールバック (current, total)

        Returns:
            ソート済み画像パスのリスト
        """
        logger.info(f"Sorting {len(image_paths)} images by content...")

        if len(image_paths) <= 1:
            return image_paths

        # 比較回数の概算
        total_comparisons = (len(image_paths) * (len(image_paths) - 1)) // 2
        logger.info(f"Estimated comparisons: {total_comparisons}")

        current_comparison = [0]  # リスト内に入れて参照を共有

        def compare_func(img1, img2):
            """比較関数"""
            current_comparison[0] += 1

            if progress_callback:
                progress_callback(current_comparison[0], total_comparisons)

            return self.compare_images_order(img1, img2)

        # カスタム比較関数でソート
        sorted_paths = sorted(image_paths, key=cmp_to_key(compare_func))

        logger.info("Sorting complete")
        return sorted_paths

    def _image_to_data_uri(self, image_path: str) -> str:
        """
        画像をData URIに変換

        Args:
            image_path: 画像パス

        Returns:
            Data URI文字列
        """
        try:
            with Image.open(image_path) as img:
                # RGB変換（RGBA等の場合）
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # 画像サイズを最適化 (メモリ節約)
                img.thumbnail(Config.IMAGE_RESIZE_MAX, Image.Resampling.LANCZOS)

                # BytesIOにJPEG形式で保存
                buffered = BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                return f"data:image/jpeg;base64,{img_base64}"

        except Exception as e:
            logger.error(f"Failed to convert image to data URI: {e}")
            raise

    def clear_cache(self):
        """比較結果のキャッシュをクリア"""
        self.comparison_cache.clear()
        logger.info("Comparison cache cleared")

    def get_cache_size(self) -> int:
        """キャッシュサイズを取得"""
        return len(self.comparison_cache)
