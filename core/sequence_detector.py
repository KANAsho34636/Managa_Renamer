"""
連番・欠番検出機能
"""
import re
from pathlib import Path
from typing import List, Dict, Set
from utils.logger import get_logger

logger = get_logger(__name__)


class SequenceDetector:
    """ファイル名の連番や欠番を検出"""

    def __init__(self, pattern: str = r'\d+'):
        """
        Args:
            pattern: ファイル名から番号を抽出する正規表現パターン
        """
        self.pattern = pattern
        logger.info(f"SequenceDetector initialized with pattern: {pattern}")

    def extract_numbers(self, file_paths: List[Path]) -> List[Dict]:
        """
        ファイル名から番号を抽出

        Args:
            file_paths: ファイルパスのリスト

        Returns:
            [{
                'path': Path,
                'number': int or None,
                'name': str
            }, ...]
        """
        results = []

        for file_path in file_paths:
            match = re.search(self.pattern, file_path.stem)

            if match:
                number = int(match.group())
            else:
                number = None

            results.append({
                'path': file_path,
                'number': number,
                'name': file_path.name
            })

        return results

    def detect_missing(self, file_paths: List[Path]) -> List[int]:
        """
        欠番を検出

        Args:
            file_paths: ファイルパスのリスト

        Returns:
            欠番のリスト
        """
        numbers = []

        for file_path in file_paths:
            match = re.search(self.pattern, file_path.stem)
            if match:
                numbers.append(int(match.group()))

        if not numbers:
            logger.warning("No numbers found in file names")
            return []

        numbers.sort()
        expected = set(range(min(numbers), max(numbers) + 1))
        actual = set(numbers)
        missing = sorted(expected - actual)

        if missing:
            logger.info(f"Missing numbers detected: {missing}")
        else:
            logger.info("No missing numbers detected")

        return missing

    def detect_duplicates(self, file_paths: List[Path]) -> Dict[int, List[str]]:
        """
        重複番号を検出

        Args:
            file_paths: ファイルパスのリスト

        Returns:
            {番号: [ファイル名のリスト], ...}
        """
        number_files = {}

        for file_path in file_paths:
            match = re.search(self.pattern, file_path.stem)
            if match:
                number = int(match.group())
                if number not in number_files:
                    number_files[number] = []
                number_files[number].append(file_path.name)

        # 重複のみを抽出
        duplicates = {num: files for num, files in number_files.items() if len(files) > 1}

        if duplicates:
            logger.warning(f"Duplicate numbers detected: {duplicates}")
        else:
            logger.info("No duplicate numbers detected")

        return duplicates

    def validate_sequence(self, file_paths: List[Path]) -> Dict:
        """
        連番を検証

        Args:
            file_paths: ファイルパスのリスト

        Returns:
            {
                'is_valid': bool,  # 完全な連番か
                'missing_numbers': List[int],  # 欠番
                'duplicate_numbers': Dict[int, List[str]],  # 重複
                'total_files': int,  # ファイル総数
                'min_number': int or None,  # 最小番号
                'max_number': int or None  # 最大番号
            }
        """
        missing = self.detect_missing(file_paths)
        duplicates = self.detect_duplicates(file_paths)

        numbers = []
        for file_path in file_paths:
            match = re.search(self.pattern, file_path.stem)
            if match:
                numbers.append(int(match.group()))

        result = {
            'is_valid': len(missing) == 0 and len(duplicates) == 0,
            'missing_numbers': missing,
            'duplicate_numbers': duplicates,
            'total_files': len(file_paths),
            'min_number': min(numbers) if numbers else None,
            'max_number': max(numbers) if numbers else None
        }

        logger.info(f"Sequence validation result: {result}")
        return result

    def get_sequence_gaps(self, file_paths: List[Path]) -> List[tuple]:
        """
        連番のギャップ（連続していない部分）を検出

        Args:
            file_paths: ファイルパスのリスト

        Returns:
            [(開始番号, 終了番号), ...] のリスト
        """
        numbers = []
        for file_path in file_paths:
            match = re.search(self.pattern, file_path.stem)
            if match:
                numbers.append(int(match.group()))

        if not numbers:
            return []

        numbers.sort()
        gaps = []

        for i in range(len(numbers) - 1):
            if numbers[i + 1] - numbers[i] > 1:
                gaps.append((numbers[i], numbers[i + 1]))

        logger.info(f"Sequence gaps detected: {gaps}")
        return gaps

    def suggest_renaming(self, file_paths: List[Path], start_number: int = 1) -> List[Dict]:
        """
        リネーム提案を生成

        Args:
            file_paths: ファイルパスのリスト（既にソート済みを想定）
            start_number: 開始番号

        Returns:
            [{
                'old_path': Path,
                'old_name': str,
                'suggested_number': int,
                'suggested_name': str
            }, ...]
        """
        suggestions = []

        for idx, file_path in enumerate(file_paths, start=start_number):
            suggestions.append({
                'old_path': file_path,
                'old_name': file_path.name,
                'suggested_number': idx,
                'suggested_name': f"{str(idx).zfill(3)}{file_path.suffix}"
            })

        logger.info(f"Generated {len(suggestions)} renaming suggestions")
        return suggestions
