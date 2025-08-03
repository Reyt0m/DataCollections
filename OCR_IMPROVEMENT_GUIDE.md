# OCR機能改善ガイド

## 概要

画像のOCR（光学文字認識）に失敗する問題を解決するため、以下の改善を実装しました：

## 主な改善点

### 1. 画像品質チェック機能
- **サイズチェック**: 50x50ピクセル未満の画像を除外
- **アスペクト比チェック**: 極端に細長い画像（10:1以上）を除外
- **画像モードチェック**: サポートされていない画像形式を除外

### 2. 画像前処理機能
- **RGB変換**: すべての画像をRGB形式に統一
- **サイズ調整**: 1024ピクセル以上の画像を自動縮小
- **コントラスト向上**: コントラストを1.2倍に調整
- **明度調整**: 明度を1.1倍に調整

### 3. 複数OCRエンジンの使用
- **EasyOCR**: 高精度な日本語・英語認識
- **Tesseract**: バックアップとして使用
- **ファイル名解析**: OCR失敗時の代替手段

### 4. テキスト後処理
- **クリーニング**: 改行、タブ、特殊文字の除去
- **フィルタリング**: 明らかに会社名でないテキストを除外
- **長さチェック**: 短すぎるテキスト（2文字未満）を除外

## 使用方法

### 基本的な使用方法

```python
from portfolio_scraper import PortfolioScraper

# OCR機能付きでスクレイパーを初期化
scraper = PortfolioScraper(use_ocr=True)

# 画像からテキストを抽出
extracted_text = scraper.extract_text_from_image("https://example.com/logo.png")
```

### 高度な設定

```python
# カスタム設定でスクレイパーを初期化
scraper = PortfolioScraper(
    headless=True,      # ヘッドレスモード
    timeout=15,         # タイムアウト時間
    use_ocr=True,       # OCR機能を有効化
    ocr_confidence=0.5  # OCR信頼度閾値
)
```

## トラブルシューティング

### 1. OCRが失敗する場合

**原因**: 画像の品質が低い、またはOCRエンジンが利用できない

**解決策**:
```python
# 画像品質チェックを無効にする（デバッグ用）
scraper._is_image_quality_good = lambda img: True

# ファイル名から推測を試行
text = scraper._extract_text_from_filename(img_url)
```

### 2. 処理速度が遅い場合

**原因**: 大量の画像を処理している

**解決策**:
```python
# 画像処理数を制限
for img in img_elements[:10]:  # 最初の10枚のみ処理
    # 処理を実行
```

### 3. メモリ不足エラー

**原因**: 大きな画像を処理している

**解決策**:
```python
# 画像サイズの制限を調整
max_size = 512  # 1024から512に変更
```

## パフォーマンス最適化

### 1. 並列処理
```python
import concurrent.futures

def process_images_parallel(img_urls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(scraper.extract_text_from_image, url) for url in img_urls]
        results = [future.result() for future in futures]
    return results
```

### 2. キャッシュ機能
```python
import hashlib
import pickle

class CachedOCR:
    def __init__(self, cache_file="ocr_cache.pkl"):
        self.cache_file = cache_file
        self.cache = self.load_cache()

    def load_cache(self):
        try:
            with open(self.cache_file, 'rb') as f:
                return pickle.load(f)
        except:
            return {}

    def save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)

    def get_text(self, img_url):
        img_hash = hashlib.md5(img_url.encode()).hexdigest()
        if img_hash in self.cache:
            return self.cache[img_hash]

        text = scraper.extract_text_from_image(img_url)
        self.cache[img_hash] = text
        self.save_cache()
        return text
```

## 設定パラメータ

### OCR設定
- `ocr_confidence`: OCR信頼度閾値（デフォルト: 0.5）
- `max_image_size`: 最大画像サイズ（デフォルト: 1024）
- `min_image_size`: 最小画像サイズ（デフォルト: 50）

### 画像前処理設定
- `contrast_enhancement`: コントラスト向上率（デフォルト: 1.2）
- `brightness_enhancement`: 明度向上率（デフォルト: 1.1）
- `aspect_ratio_limit`: アスペクト比制限（デフォルト: 10）

## テスト方法

### 1. 単体テスト
```bash
python test_ocr_functionality.py
```

### 2. 統合テスト
```bash
python test_improved_scraper.py
```

### 3. カスタムテスト
```python
# 特定の画像でテスト
test_images = [
    "https://example.com/logo1.png",
    "https://example.com/logo2.jpg"
]

for img_url in test_images:
    result = scraper.extract_text_from_image(img_url)
    print(f"{img_url}: {result}")
```

## よくある質問

### Q: OCRの精度を向上させるには？
A: 以下の方法を試してください：
- 画像の前処理パラメータを調整
- OCR信頼度閾値を下げる（0.3-0.4）
- 複数のOCRエンジンを組み合わせる

### Q: 処理速度を向上させるには？
A: 以下の方法を試してください：
- 並列処理を使用
- 画像サイズ制限を下げる
- キャッシュ機能を使用

### Q: メモリ使用量を削減するには？
A: 以下の方法を試してください：
- 画像サイズ制限を下げる
- バッチ処理を使用
- 不要な画像を事前にフィルタリング

## 今後の改善予定

1. **GPU対応**: CUDAを使用した高速化
2. **AIモデル**: より高精度なOCRモデルの導入
3. **自動学習**: 失敗した画像からの学習機能
4. **クラウドOCR**: Google Vision API等との連携

## サポート

問題が発生した場合は、以下の情報を提供してください：
- エラーメッセージ
- 使用している画像のURL
- スクレイパーの設定
- システム情報（OS、Pythonバージョン等）
