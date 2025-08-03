# Portfolio Scraper Tool (Improved Version)

ポートフォリオページから会社名を自動抽出するスクレイピングツールの改善版です。画像ベースの会社名にも対応し、OCR機能を備えています。

## 主な改善点

### 1. 多様なポートフォリオタブ名に対応
- `portfolio`, `investment`, `partners`, `companies` など様々な名前のタブを自動検出
- 日本語と英語の両方に対応

### 2. 画像ベースの会社名抽出
- OCR（光学文字認識）機能により、画像に含まれるテキストを自動抽出
- EasyOCR と Tesseract の両方に対応
- 日本語と英語のテキスト認識

### 3. 画像クリックによる詳細ページ取得
- 画像をクリックして詳細ページに移動し、会社名を取得
- 動的なコンテンツにも対応

### 4. より高精度な会社名抽出
- 複数のCSSセレクターに対応
- 正規表現パターンマッチングの改善
- フィルタリング機能の強化

## インストール

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. OCR機能のセットアップ（オプション）

#### EasyOCR（推奨）
```bash
pip install easyocr
```

#### Tesseract（代替）
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-jpn

# macOS
brew install tesseract tesseract-lang

# Windows
# https://github.com/UB-Mannheim/tesseract/wiki からダウンロード

pip install pytesseract
```

## 使用方法

### 1. URLリストファイルの準備

`urls.txt` ファイルを作成し、スクレイピング対象のURLを1行に1つずつ記述します：

```
https://example-vc1.com
https://example-vc2.com/portfolio
https://example-vc3.com/investment
```

### 2. スクレイピングの実行

```bash
python portfolio_scraper.py
```

### 3. 結果の確認

実行後、以下のファイルが生成されます：

- `portfolio_results.json`: 詳細な結果（JSON形式）
- `portfolio_results.csv`: 表形式の結果（CSV形式）
- `scraper.log`: 実行ログ

## 設定オプション

### スクレイパーの初期化

```python
from portfolio_scraper import PortfolioScraper

# 基本設定
scraper = PortfolioScraper(
    headless=True,      # ヘッドレスモード（True推奨）
    timeout=20,         # タイムアウト時間（秒）
    use_ocr=True        # OCR機能の使用（True推奨）
)
```

### 個別URLのスクレイピング

```python
result = scraper.scrape_url("https://example.com")
print(f"抽出された会社数: {len(result['companies'])}")
print(f"会社名: {result['companies']}")
```

## 出力形式

### JSON出力例

```json
{
  "url": "https://example.com",
  "portfolio_url": "https://example.com/portfolio",
  "companies": ["株式会社サンプル", "Sample Corp Inc"],
  "error": null,
  "method": "selenium",
  "ocr_used": true
}
```

### CSV出力例

| url | portfolio_url | company_name | method | ocr_used | error |
|-----|---------------|--------------|--------|----------|-------|
| https://example.com | https://example.com/portfolio | 株式会社サンプル | selenium | true | |

## 対応しているサイト構造

### 1. ジェネシア・ベンチャーズ
- URL: `https://www.genesiaventures.com/partners/`
- 特徴: 画像ベースの会社ロゴ、クリック可能な詳細ページ

### 2. DEEPCORE
- URL: `https://deepcore.jp/investment`
- 特徴: 動的コンテンツ、JavaScript生成

### 3. サムライインキュベート
- URL: `https://www.samurai-incubate.co.jp/portfolio/`
- 特徴: フィルタリング機能付きポートフォリオ

### 4. その他のVCサイト
- 一般的なポートフォリオページ構造に対応
- カスタムCSSクラス名にも対応

## トラブルシューティング

### よくある問題

1. **OCRが動作しない**
   - EasyOCRまたはTesseractが正しくインストールされているか確認
   - 画像のURLがアクセス可能か確認

2. **会社名が抽出されない**
   - サイトの構造が変更されている可能性
   - CSSセレクターの追加が必要な場合があります

3. **タイムアウトエラー**
   - `timeout` パラメータを増やす
   - ネットワーク接続を確認

### ログの確認

```bash
tail -f scraper.log
```

## カスタマイズ

### 新しいCSSセレクターの追加

```python
# portfolio_selectors リストに追加
portfolio_selectors = [
    '.your-custom-class',
    '[class*="your-pattern"]',
    # 既存のセレクター...
]
```

### 新しいポートフォリオキーワードの追加

```python
# portfolio_keywords リストに追加
portfolio_keywords = [
    'your-custom-keyword',
    # 既存のキーワード...
]
```

## 注意事項

1. **利用規約の遵守**: 各サイトの利用規約を確認し、適切に使用してください
2. **アクセス頻度**: サーバーに負荷をかけないよう、適切な間隔を設けてください
3. **データの使用**: 取得したデータの使用目的を明確にし、適切に管理してください

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能改善の提案は歓迎します。プルリクエストも受け付けています。
