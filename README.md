# 漫画・書籍画像ファイル連番管理ツール

VLM（Vision Language Model）を使用して、漫画や書籍の画像ファイルを時系列順に分析し、適切な連番でリネームするGUIアプリケーションです。

## 特徴

- **VLMによる画像内容分析**: Qwen3-VL-4B-Instruct-GGUFモデルを使用
- **ペア比較アルゴリズム**: 画像同士を比較して物語の時系列順序を自動判定
- **GUI操作**: Tkinterによる使いやすいインターフェース
- **自動バックアップ**: リネーム前に自動でバックアップを作成
- **CPU/GPU対応**: CUDA対応GPUで高速処理が可能

## 必要要件

- Python 3.8以上
- 推奨: CUDA対応GPU（CPU専用でも動作可能）
- ディスク空き容量: 約3GB（モデルファイル用）

## インストール

### 1. リポジトリのクローン/ダウンロード

```bash
cd D:\
# または既にダウンロード済みの場合はそのまま使用
```

### 2. 依存関係のインストール

#### GPU版（推奨）

Windows (PowerShell):
```powershell
cd D:\manga_renamer
$env:CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
pip install -r requirements.txt
```

Linux/Mac:
```bash
cd /path/to/manga_renamer
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
pip install -r requirements.txt
```

#### CPU専用版

```bash
cd D:\manga_renamer
pip install -r requirements.txt
```

## 使い方

### 1. アプリケーションの起動

```bash
cd D:\manga_renamer
python main.py
```

### 2. 基本操作フロー

1. **フォルダ選択**
   - [参照] ボタンをクリック
   - 画像が保存されているフォルダを選択

2. **画像スキャン**
   - [スキャン] ボタンをクリック
   - JPG/JPEG, PNG, WebP形式の画像を自動検出
   - 欠番や重複がある場合は通知されます

3. **VLM分析**（初回起動時はモデルダウンロードが必要）
   - [VLM分析] ボタンをクリック
   - モデルが未ダウンロードの場合、ダウンロード確認ダイアログが表示されます
   - 分析が開始され、画像の内容を比較して時系列順序を判定
   - 進捗バーで進行状況を確認できます

4. **順序確認**
   - 分析完了後、画像リストに推奨順序が表示されます
   - リスト内の画像をクリックしてプレビュー確認

5. **リネーム実行**
   - [リネーム実行] ボタンをクリック
   - 確認ダイアログで設定を確認
   - 実行するとバックアップが作成され、連番でリネームされます

## 設定のカスタマイズ

`config.py`ファイルを編集することで、以下の設定をカスタマイズできます:

```python
class Config:
    # リネーム設定
    DEFAULT_PREFIX = 'page_'  # ファイル名プレフィックス
    DEFAULT_DIGITS = 3        # 連番桁数（例: 001, 002, ...）
    AUTO_BACKUP = True        # 自動バックアップ

    # VLM設定
    TEMPERATURE = 0.3         # 生成温度（0.0-1.0、低いほど決定論的）
    N_GPU_LAYERS = -1         # GPU使用レイヤー数（-1で全て、0でCPU専用）

    # 画像設定
    IMAGE_RESIZE_MAX = (1024, 1024)  # VLMに送信する前のリサイズサイズ
```

## トラブルシューティング

### Q: モデルのダウンロードに時間がかかりすぎる
A: モデルファイルは約2.8GBあります。インターネット接続速度によっては時間がかかる場合があります。ダウンロードは中断しても再開可能です。

### Q: GPU版のインストールに失敗する
A: CUDA Toolkitがインストールされているか確認してください。または、CPU専用版をインストールしてください。

### Q: VLM分析が遅い
A: 以下を確認してください:
- GPU版を使用しているか（`Config.USE_GPU`がTrueか確認）
- 画像数が多い場合は時間がかかります（ペア比較のため）
- CPU専用の場合は特に時間がかかります

### Q: 分析結果の順序が正しくない
A: VLMの判定は完璧ではありません。以下を試してください:
- 画像の画質を確認（低画質だと判定精度が下がります）
- 手動で順序を調整する機能は今後追加予定です

### Q: リネーム後に元に戻したい
A: バックアップフォルダ（`.backup_YYYYMMDD_HHMMSS`）から復元できます。

## プロジェクト構造

```
D:\manga_renamer\
├── main.py                  # エントリーポイント
├── config.py                # 設定ファイル
├── requirements.txt         # 依存関係
├── README.md                # このファイル
├── models/                  # モデルファイル保存先
│   ├── downloader.py        # モデルダウンロード機能
│   └── (ダウンロードされたGGUFファイル)
├── gui/                     # GUI関連
│   └── main_window.py       # メインウィンドウ
├── core/                    # コアロジック
│   ├── image_scanner.py     # 画像スキャン
│   ├── vlm_analyzer.py      # VLM分析エンジン
│   ├── sequence_detector.py # 連番検出
│   └── renamer.py           # リネーム実行
├── utils/                   # ユーティリティ
│   └── logger.py            # ロギング
└── logs/                    # ログファイル出力先
```

## 技術詳細

### 使用モデル

- **モデル名**: Qwen3-VL-4B-Instruct-GGUF (Q4_K_M)
- **提供元**: unsloth (Hugging Face)
- **サイズ**: 約2.8GB
- **特徴**: Vision Language Modelで画像とテキストの両方を理解可能

### ペア比較アルゴリズム

画像をペアで比較し、「どちらが先に来るべきか」をVLMに判定させます。全ペアの比較結果を元にソートアルゴリズムで最終的な順序を確定します。

**利点**:
- 個別分析よりも相対的な順序判定が正確
- 物語の流れを考慮した順序付けが可能

**欠点**:
- 比較回数が多い（n枚の画像でO(n²)回の比較）
- 処理時間がかかる場合がある

### GPU/CPU対応

- llama-cpp-pythonを使用してGGUFモデルを実行
- CUDA対応GPUがあれば自動的に使用
- CPU専用でも動作可能（ただし低速）

## ライセンス

このプロジェクトは個人利用・商用利用ともに自由に使用できます。

## 今後の拡張予定

- [ ] 手動順序調整UI
- [ ] 複数モデル対応
- [ ] バッチ処理モード（複数フォルダ一括処理）
- [ ] カスタムプロンプト編集機能
- [ ] OCRによるページ番号自動検出
- [ ] 実行ファイル化（PyInstaller）

## サポート

問題が発生した場合は、`logs/`フォルダ内のログファイルを確認してください。

---

**開発**: Claude Code
**バージョン**: 1.0.0
**最終更新**: 2025-12-02
