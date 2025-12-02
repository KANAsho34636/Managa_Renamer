"""
メインGUIウィンドウ
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
from typing import List, Dict, Optional
from PIL import Image, ImageTk

from core.image_scanner import ImageScanner
from core.vlm_analyzer import VLMAnalyzer
from core.renamer import ImageRenamer
from core.sequence_detector import SequenceDetector
from models.downloader import ModelDownloader
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


class MangaRenamerGUI:
    """メインGUIアプリケーション"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("漫画・書籍画像ファイル連番管理ツール")
        self.root.geometry("1200x800")

        # 状態管理
        self.current_folder = tk.StringVar()
        self.image_files: List[Path] = []
        self.sorted_paths: List[str] = []
        self.analysis_in_progress = False

        # コンポーネント初期化
        self.scanner = ImageScanner()
        self.downloader = ModelDownloader()
        self.vlm_analyzer: Optional[VLMAnalyzer] = None
        self.renamer = ImageRenamer(dry_run=False)
        self.sequence_detector = SequenceDetector()

        # プレビュー用
        self.current_preview_image = None

        # UI構築
        self._setup_ui()

        # モデルの利用可能性をチェック
        self.root.after(500, self._check_model_availability)

    def _setup_ui(self):
        """UI構築"""
        # フォルダ選択フレーム
        folder_frame = ttk.Frame(self.root, padding=10)
        folder_frame.pack(fill=tk.X)

        ttk.Label(folder_frame, text="フォルダ:").pack(side=tk.LEFT)
        ttk.Entry(folder_frame, textvariable=self.current_folder, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(folder_frame, text="参照...", command=self._browse_folder).pack(side=tk.LEFT)
        ttk.Button(folder_frame, text="スキャン", command=self._scan_folder).pack(side=tk.LEFT, padx=5)

        # メインコンテンツフレーム
        content_frame = ttk.Frame(self.root, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左側: 画像リスト
        left_frame = ttk.Frame(content_frame, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(left_frame, text="画像リスト").pack()

        # Treeview for image list
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.image_tree = ttk.Treeview(
            tree_frame,
            columns=('filename', 'order', 'status'),
            show='headings',
            height=20
        )
        self.image_tree.heading('filename', text='ファイル名')
        self.image_tree.heading('order', text='順序')
        self.image_tree.heading('status', text='状態')

        self.image_tree.column('filename', width=250)
        self.image_tree.column('order', width=50)
        self.image_tree.column('status', width=80)

        # スクロールバー
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.image_tree.yview)
        self.image_tree.configure(yscrollcommand=scrollbar.set)

        self.image_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # アイテム選択時のイベント
        self.image_tree.bind('<<TreeviewSelect>>', self._on_image_select)

        # 右側: プレビュー
        right_frame = ttk.Frame(content_frame, width=600)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        ttk.Label(right_frame, text="プレビュー").pack()

        # Canvas for image preview
        self.preview_canvas = tk.Canvas(right_frame, bg='gray', width=400, height=500)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, pady=5)

        # Text for description
        desc_frame = ttk.Frame(right_frame)
        desc_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(desc_frame, text="分析結果:").pack(anchor=tk.W)

        self.description_text = tk.Text(desc_frame, height=8, wrap=tk.WORD)
        self.description_text.pack(fill=tk.BOTH, expand=True)

        desc_scrollbar = ttk.Scrollbar(desc_frame, orient=tk.VERTICAL, command=self.description_text.yview)
        self.description_text.configure(yscrollcommand=desc_scrollbar.set)

        # 進捗バー
        progress_frame = ttk.Frame(self.root, padding=10)
        progress_frame.pack(fill=tk.X)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(progress_frame, text="待機中...")
        self.status_label.pack()

        # ボタンフレーム
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(fill=tk.X)

        self.btn_analyze = ttk.Button(button_frame, text="VLM分析", command=self._analyze_images)
        self.btn_analyze.pack(side=tk.LEFT, padx=5)

        self.btn_rename = ttk.Button(button_frame, text="リネーム実行", command=self._execute_rename)
        self.btn_rename.pack(side=tk.LEFT, padx=5)

        self.btn_model = ttk.Button(button_frame, text="モデル管理", command=self._manage_models)
        self.btn_model.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="ヘルプ", command=self._show_help).pack(side=tk.RIGHT, padx=5)

    def _check_model_availability(self):
        """モデルの利用可能性をチェック"""
        model_key = Config.MODEL_KEY

        if not self.downloader.is_model_downloaded(model_key):
            response = messagebox.askyesno(
                "モデル未ダウンロード",
                f"VLMモデル ({model_key}) がダウンロードされていません。\n"
                f"推定サイズ: {self.downloader.get_model_info(model_key)['size_gb']} GB\n\n"
                "今すぐダウンロードしますか?"
            )
            if response:
                self._download_model()
        else:
            self._load_model()

    def _download_model(self):
        """モデルをダウンロード (別スレッド)"""
        def download_thread():
            try:
                self.status_label.config(text="モデルをダウンロード中...")
                self.btn_analyze.config(state=tk.DISABLED)

                paths = self.downloader.download_model(Config.MODEL_KEY)

                self.status_label.config(text="ダウンロード完了!")
                self._load_model()

            except Exception as e:
                logger.error(f"Model download failed: {e}")
                messagebox.showerror("エラー", f"ダウンロード失敗: {e}")
                self.status_label.config(text="ダウンロード失敗")

            finally:
                self.btn_analyze.config(state=tk.NORMAL)

        threading.Thread(target=download_thread, daemon=True).start()

    def _load_model(self):
        """モデルをロード"""
        try:
            paths = self.downloader.get_model_paths(Config.MODEL_KEY)
            if paths:
                self.status_label.config(text="モデルをロード中...")

                self.vlm_analyzer = VLMAnalyzer(
                    model_path=paths['model_path'],
                    mmproj_path=paths['mmproj_path']
                )

                self.status_label.config(text="モデルロード完了")
                logger.info("VLM model loaded successfully")
        except ImportError as e:
            logger.error(f"llama-cpp-python not installed: {e}")
            messagebox.showerror(
                "依存関係エラー",
                "llama-cpp-python がインストールされていません。\n\n"
                "以下のいずれかを実行してください:\n"
                "  GPU版: install.bat または install_gpu_latest.bat\n"
                "  CPU版: install_cpu.bat\n\n"
                "詳細: README.md を参照してください"
            )
            self.status_label.config(text="llama-cpp-python 未インストール")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            messagebox.showerror("エラー", f"モデルロード失敗: {e}")
            self.status_label.config(text="モデルロード失敗")

    def _browse_folder(self):
        """フォルダ選択ダイアログ"""
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder.set(folder)
            logger.info(f"Selected folder: {folder}")

    def _scan_folder(self):
        """フォルダをスキャンして画像ファイルを検出"""
        folder = self.current_folder.get()
        if not folder:
            messagebox.showwarning("警告", "フォルダを選択してください")
            return

        try:
            self.image_files = self.scanner.scan_folder(
                folder,
                extensions=Config.SUPPORTED_FORMATS
            )

            # Treeviewに表示
            self.image_tree.delete(*self.image_tree.get_children())

            for idx, img in enumerate(self.image_files, start=1):
                self.image_tree.insert('', tk.END, values=(img.name, '-', '未分析'))

            self.status_label.config(text=f"{len(self.image_files)}枚の画像を検出")
            logger.info(f"Scanned {len(self.image_files)} images")

            # 連番チェック
            validation = self.sequence_detector.validate_sequence(self.image_files)
            if not validation['is_valid']:
                msg = f"欠番: {validation['missing_numbers']}\n重複: {validation['duplicate_numbers']}"
                messagebox.showinfo("連番チェック", msg)

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            messagebox.showerror("エラー", f"スキャン失敗: {e}")

    def _analyze_images(self):
        """VLM分析を実行 (別スレッド)"""
        if not self.vlm_analyzer:
            messagebox.showerror("エラー", "モデルがロードされていません")
            return

        if not self.image_files:
            messagebox.showwarning("警告", "画像をスキャンしてください")
            return

        if self.analysis_in_progress:
            messagebox.showwarning("警告", "分析中です。しばらくお待ちください")
            return

        def analysis_thread():
            self.analysis_in_progress = True
            self.btn_analyze.config(state=tk.DISABLED)

            try:
                image_paths = [str(img) for img in self.image_files]
                total = len(image_paths)

                def progress_callback(current, total_comparisons):
                    progress = (current / total_comparisons) * 100
                    self.progress_var.set(progress)
                    self.status_label.config(text=f"分析中... {current}/{total_comparisons} 比較")

                logger.info("Starting VLM analysis...")
                self.sorted_paths = self.vlm_analyzer.sort_images_by_content(
                    image_paths,
                    progress_callback=progress_callback
                )

                # Treeview更新
                self.image_tree.delete(*self.image_tree.get_children())
                for idx, path in enumerate(self.sorted_paths, start=1):
                    filename = Path(path).name
                    self.image_tree.insert('', tk.END, values=(filename, idx, '分析完了'))

                self.status_label.config(text=f"分析完了! ({len(self.sorted_paths)}枚)")
                self.progress_var.set(100)

                messagebox.showinfo("完了", "VLM分析が完了しました")

            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                messagebox.showerror("エラー", f"分析失敗: {e}")
                self.status_label.config(text="分析失敗")

            finally:
                self.analysis_in_progress = False
                self.btn_analyze.config(state=tk.NORMAL)
                self.progress_var.set(0)

        threading.Thread(target=analysis_thread, daemon=True).start()

    def _execute_rename(self):
        """リネームを実行"""
        if not self.sorted_paths:
            messagebox.showwarning("警告", "先にVLM分析を実行してください")
            return

        response = messagebox.askyesno(
            "確認",
            f"{len(self.sorted_paths)}枚の画像をリネームします。\n"
            f"プレフィックス: '{Config.DEFAULT_PREFIX}'\n"
            f"連番桁数: {Config.DEFAULT_DIGITS}\n"
            f"バックアップ: {Config.AUTO_BACKUP}\n\n"
            "よろしいですか?"
        )

        if not response:
            return

        try:
            rename_log = self.renamer.rename_by_order(
                ordered_paths=self.sorted_paths,
                prefix=Config.DEFAULT_PREFIX,
                digits=Config.DEFAULT_DIGITS,
                backup=Config.AUTO_BACKUP
            )

            success_count = sum(1 for log in rename_log if log['success'])
            messagebox.showinfo("完了", f"{success_count}/{len(rename_log)}枚のリネームが完了しました")

            # 再スキャン
            self._scan_folder()

        except Exception as e:
            logger.error(f"Rename failed: {e}")
            messagebox.showerror("エラー", f"リネーム失敗: {e}")

    def _on_image_select(self, event):
        """画像選択時のイベント"""
        selection = self.image_tree.selection()
        if not selection:
            return

        item = self.image_tree.item(selection[0])
        filename = item['values'][0]

        # ファイルパスを検索
        folder = Path(self.current_folder.get())
        image_path = folder / filename

        if image_path.exists():
            self._show_preview(image_path)

    def _show_preview(self, image_path: Path):
        """画像プレビューを表示"""
        try:
            # 画像をロード
            img = Image.open(image_path)

            # アスペクト比を維持してリサイズ
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            if canvas_width <= 1:
                canvas_width = 400
            if canvas_height <= 1:
                canvas_height = 500

            img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)

            # PhotoImageに変換
            self.current_preview_image = ImageTk.PhotoImage(img)

            # Canvasに表示
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.current_preview_image,
                anchor=tk.CENTER
            )

            # 説明テキストをクリア
            self.description_text.delete(1.0, tk.END)
            self.description_text.insert(tk.END, f"ファイル: {image_path.name}\n")
            self.description_text.insert(tk.END, f"サイズ: {image_path.stat().st_size // 1024} KB\n")

        except Exception as e:
            logger.error(f"Preview failed: {e}")

    def _manage_models(self):
        """モデル管理ダイアログ"""
        dialog = tk.Toplevel(self.root)
        dialog.title("モデル管理")
        dialog.geometry("400x300")

        ttk.Label(dialog, text="利用可能なモデル:").pack(pady=10)

        for model_key in self.downloader.list_available_models():
            info = self.downloader.get_model_info(model_key)
            is_downloaded = self.downloader.is_model_downloaded(model_key)

            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.X, padx=10, pady=5)

            status = "✓ ダウンロード済み" if is_downloaded else "未ダウンロード"
            ttk.Label(frame, text=f"{model_key} ({info['size_gb']}GB) - {status}").pack(side=tk.LEFT)

        ttk.Button(dialog, text="閉じる", command=dialog.destroy).pack(pady=10)

    def _show_help(self):
        """ヘルプを表示"""
        help_text = """漫画・書籍画像ファイル連番管理ツール

使い方:
1. [参照] ボタンで画像フォルダを選択
2. [スキャン] で画像ファイルを検出
3. [VLM分析] で画像の内容を分析して適切な順序を決定
4. [リネーム実行] で連番でリネーム

注意:
- リネーム前に自動でバックアップが作成されます
- VLM分析には時間がかかる場合があります
- GPU使用時はより高速に処理されます
"""
        messagebox.showinfo("ヘルプ", help_text)
