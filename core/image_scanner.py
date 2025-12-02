"""
画像ファイルスキャン機能
"""
from pathlib import Path
from typing import List, Set
from utils.logger import get_logger

logger = get_logger(__name__)


class ImageScanner:
    """画像ファイルをスキャン"""

    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}

    def __init__(self):
        """画像スキャナーを初期化"""
        logger.info("ImageScanner initialized")

    def scan_folder(self, folder_path: str, extensions: List[str] = None, recursive: bool = False) -> List[Path]:
        """
        フォルダ内の画像ファイルをスキャン

        Args:
            folder_path: スキャン対象フォルダ
            extensions: 対象拡張子リスト (Noneの場合はデフォルト)
            recursive: サブフォルダも再帰的にスキャンするか

        Returns:
            画像ファイルパスのリスト（ファイル名順にソート）

        Raises:
            FileNotFoundError: フォルダが存在しない
        """
        if extensions is None:
            extensions = self.SUPPORTED_EXTENSIONS
        else:
            extensions = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions}

        folder = Path(folder_path)
        if not folder.exists():
            logger.error(f"Folder not found: {folder_path}")
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        if not folder.is_dir():
            logger.error(f"Path is not a directory: {folder_path}")
            raise NotADirectoryError(f"Path is not a directory: {folder_path}")

        logger.info(f"Scanning folder: {folder_path}")
        logger.info(f"Extensions: {extensions}")
        logger.info(f"Recursive: {recursive}")

        image_files = []

        if recursive:
            # 再帰的スキャン
            for file in folder.rglob('*'):
                if file.is_file() and file.suffix.lower() in extensions:
                    image_files.append(file)
        else:
            # 直下のみスキャン
            for file in folder.iterdir():
                if file.is_file() and file.suffix.lower() in extensions:
                    image_files.append(file)

        # ファイル名順にソート
        image_files.sort(key=lambda x: x.name.lower())

        logger.info(f"Found {len(image_files)} image files")
        return image_files

    def get_file_info(self, file_path: Path) -> dict:
        """
        ファイル情報を取得

        Args:
            file_path: ファイルパス

        Returns:
            ファイル情報を含む辞書
            {
                'name': str,
                'path': str,
                'size': int,  # バイト
                'extension': str,
                'modified': float  # タイムスタンプ
            }
        """
        stat = file_path.stat()

        return {
            'name': file_path.name,
            'path': str(file_path.absolute()),
            'size': stat.st_size,
            'extension': file_path.suffix.lower(),
            'modified': stat.st_mtime
        }

    def filter_by_size(self, files: List[Path], min_size: int = None, max_size: int = None) -> List[Path]:
        """
        ファイルサイズでフィルタリング

        Args:
            files: ファイルパスのリスト
            min_size: 最小サイズ（バイト）
            max_size: 最大サイズ（バイト）

        Returns:
            フィルタリング後のファイルリスト
        """
        filtered = []

        for file in files:
            size = file.stat().st_size

            if min_size is not None and size < min_size:
                continue

            if max_size is not None and size > max_size:
                continue

            filtered.append(file)

        logger.info(f"Filtered {len(files)} files to {len(filtered)} files by size")
        return filtered

    def is_supported_format(self, file_path: Path) -> bool:
        """
        サポートされている画像形式かチェック

        Args:
            file_path: ファイルパス

        Returns:
            サポートされていればTrue
        """
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
