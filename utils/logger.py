"""
ロギング機能
"""
import logging
from pathlib import Path
from datetime import datetime
from config import Config

def setup_logger(name: str, log_dir: str = None) -> logging.Logger:
    """
    ロガーをセットアップ

    Args:
        name: ロガー名
        log_dir: ログディレクトリ (Noneの場合はConfig.LOG_DIRを使用)

    Returns:
        設定済みのロガー
    """
    # ログディレクトリ作成
    if log_dir is None:
        log_dir = Config.LOG_DIR
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)

    # ログファイル名 (日付ベース)
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

    # ロガー設定
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 既存のハンドラーをクリア（重複防止）
    if logger.hasHandlers():
        logger.handlers.clear()

    # ファイルハンドラー
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    # コンソールハンドラー
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # フォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    既存のロガーを取得（存在しない場合は新規作成）

    Args:
        name: ロガー名

    Returns:
        ロガー
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        return setup_logger(name)
    return logger
