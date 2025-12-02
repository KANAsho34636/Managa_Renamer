"""
ファイルリネーム機能
"""
import shutil
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class ImageRenamer:
    """画像ファイルをリネーム"""

    def __init__(self, dry_run: bool = True):
        """
        Args:
            dry_run: Trueの場合、実際のリネームは行わずログ出力のみ
        """
        self.dry_run = dry_run
        logger.info(f"ImageRenamer initialized (dry_run={dry_run})")

    def rename_files(
        self,
        file_paths: List[Path],
        target_dir: str = None,
        prefix: str = '',
        digits: int = 3,
        start_number: int = 1,
        backup: bool = True
    ) -> List[Dict]:
        """
        ファイルをリネーム

        Args:
            file_paths: リネーム対象ファイルパスのリスト（既にソート済みを想定）
            target_dir: リネーム先ディレクトリ (Noneの場合は元のディレクトリ)
            prefix: ファイル名プレフィックス (例: 'page_')
            digits: 連番の桁数 (例: 3なら001, 002...)
            start_number: 開始番号
            backup: リネーム前にバックアップを作成

        Returns:
            リネーム操作のログ
            [{
                'original': str,
                'new': str,
                'number': int,
                'success': bool,
                'error': str (失敗時のみ)
            }, ...]
        """
        if not file_paths:
            logger.warning("No files to rename")
            return []

        # ターゲットディレクトリの決定
        if target_dir is None:
            target_dir = file_paths[0].parent
        else:
            target_dir = Path(target_dir)

        logger.info(f"Renaming {len(file_paths)} files in {target_dir}")
        logger.info(f"Prefix: '{prefix}', Digits: {digits}, Start: {start_number}")

        rename_log = []

        # バックアップ作成
        if backup and not self.dry_run:
            backup_dir = self._create_backup(file_paths, target_dir)
            logger.info(f"Backup created: {backup_dir}")

        # 一時的なリネームマップを作成（競合を避けるため）
        temp_renames = []

        for idx, file_path in enumerate(file_paths, start=start_number):
            extension = file_path.suffix
            new_name = f"{prefix}{str(idx).zfill(digits)}{extension}"
            new_path = target_dir / new_name

            temp_renames.append({
                'original_path': file_path,
                'final_path': new_path,
                'number': idx
            })

        # 実際のリネーム実行
        for rename_info in temp_renames:
            original_path = rename_info['original_path']
            final_path = rename_info['final_path']
            number = rename_info['number']

            log_entry = {
                'original': str(original_path),
                'new': str(final_path),
                'number': number,
                'success': False
            }

            if self.dry_run:
                logger.info(f"[DRY RUN] {original_path.name} -> {final_path.name}")
                log_entry['success'] = True
            else:
                try:
                    # ファイル名が同じ場合はスキップ
                    if original_path == final_path:
                        logger.info(f"Skipping (same name): {original_path.name}")
                        log_entry['success'] = True
                    else:
                        # 一時ファイル名を使用して競合を回避
                        if final_path.exists():
                            temp_path = final_path.parent / f".tmp_{final_path.name}"
                            original_path.rename(temp_path)
                            temp_path.rename(final_path)
                        else:
                            original_path.rename(final_path)

                        logger.info(f"Renamed: {original_path.name} -> {final_path.name}")
                        log_entry['success'] = True

                except Exception as e:
                    logger.error(f"Failed to rename {original_path.name}: {e}")
                    log_entry['error'] = str(e)

            rename_log.append(log_entry)

        # 成功数を集計
        success_count = sum(1 for log in rename_log if log['success'])
        logger.info(f"Rename complete: {success_count}/{len(rename_log)} files")

        return rename_log

    def rename_by_order(
        self,
        ordered_paths: List[str],
        target_dir: str = None,
        prefix: str = 'page_',
        digits: int = 3,
        backup: bool = True
    ) -> List[Dict]:
        """
        順序付きパスリストに基づいてリネーム

        Args:
            ordered_paths: 順序付き画像パスのリスト（文字列）
            target_dir: リネーム先ディレクトリ
            prefix: ファイル名プレフィックス
            digits: 連番の桁数
            backup: バックアップ作成

        Returns:
            リネーム操作のログ
        """
        path_objects = [Path(p) for p in ordered_paths]
        return self.rename_files(
            file_paths=path_objects,
            target_dir=target_dir,
            prefix=prefix,
            digits=digits,
            backup=backup
        )

    def _create_backup(self, file_paths: List[Path], target_dir: Path) -> Path:
        """
        バックアップディレクトリを作成してファイルをコピー

        Args:
            file_paths: バックアップ対象ファイル
            target_dir: ターゲットディレクトリ

        Returns:
            バックアップディレクトリのパス
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = target_dir / f'.backup_{timestamp}'
        backup_dir.mkdir(parents=True, exist_ok=True)

        for file_path in file_paths:
            try:
                backup_path = backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                logger.error(f"Failed to backup {file_path.name}: {e}")

        logger.info(f"Backed up {len(file_paths)} files to {backup_dir}")
        return backup_dir

    def restore_from_backup(self, backup_dir: str) -> bool:
        """
        バックアップから復元

        Args:
            backup_dir: バックアップディレクトリのパス

        Returns:
            成功したかどうか
        """
        backup_path = Path(backup_dir)

        if not backup_path.exists():
            logger.error(f"Backup directory not found: {backup_dir}")
            return False

        if self.dry_run:
            logger.info(f"[DRY RUN] Would restore from: {backup_dir}")
            return True

        try:
            # 元のディレクトリ（バックアップの親）
            target_dir = backup_path.parent

            for backup_file in backup_path.iterdir():
                if backup_file.is_file():
                    restore_path = target_dir / backup_file.name
                    shutil.copy2(backup_file, restore_path)
                    logger.info(f"Restored: {backup_file.name}")

            logger.info(f"Restoration complete from {backup_dir}")
            return True

        except Exception as e:
            logger.error(f"Restoration failed: {e}")
            return False

    def set_dry_run(self, dry_run: bool):
        """ドライランモードを設定"""
        self.dry_run = dry_run
        logger.info(f"Dry run mode set to: {dry_run}")
