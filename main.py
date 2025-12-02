"""
漫画・書籍画像ファイル連番管理ツール
メインエントリーポイント
"""
import tkinter as tk
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import MangaRenamerGUI
from utils.logger import setup_logger
from config import Config

def main():
    """アプリケーションエントリーポイント"""
    # 必要なディレクトリを作成
    Config.ensure_directories()

    # ロガーセットアップ
    logger = setup_logger('manga_renamer')
    logger.info("="*60)
    logger.info("Application started")
    logger.info(f"GPU available: {Config.USE_GPU}")
    logger.info(f"Model: {Config.MODEL_KEY}")
    logger.info("="*60)

    try:
        # Tkinter rootウィンドウ作成
        root = tk.Tk()

        # GUIアプリケーション起動
        app = MangaRenamerGUI(root)

        logger.info("GUI initialized successfully")

        # メインループ
        root.mainloop()

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

    finally:
        logger.info("Application closed")
        logger.info("="*60)


if __name__ == '__main__':
    main()
