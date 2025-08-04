# Research Map Integrated Scraper

Research Mapから研究者情報と競争的研究課題を取得する統合スクレイパーです。複数のスクレイピングモードをサポートし、様々な用途に対応できます。

## 機能概要

### サポートするスクレイピングモード

1. **Basic Mode** - 基本的な研究者情報と競争的研究課題の取得
2. **Enhanced Mode** - 詳細な研究者情報（ORCID、研究キーワード、研究分野など）と競争的研究課題の詳細取得
3. **HTML Mode** - HTMLページからの研究者情報取得（従来の方式）

### 取得可能な情報

#### 研究者基本情報
- 名前（日本語・英語・カナ）
- 所属機関
- 職名
- 研究者ID
- 研究者URL

#### 研究者詳細情報（Enhanced Mode）
- ORCID iD
- J-GLOBAL ID
- researchmap会員ID
- 研究キーワード
- 研究分野
- 全所属情報

#### 研究課題情報
- 研究課題タイトル
- 研究課題URL
- 研究課題ID
- 競争的研究資金かどうかの判定
- 支援システム（Enhanced Mode）
- 研究期間（Enhanced Mode）
- 研究者情報（Enhanced Mode）
- 研究課題説明（Enhanced Mode）

## インストール

### 必要なパッケージ

```bash
pip install requests beautifulsoup4 pandas openpyxl
```

### 依存関係

- Python 3.7+
- requests
- beautifulsoup4
- pandas
- openpyxl

## 使用方法

### 基本的な使用方法

```python
from researchmap_integrated_scraper import ResearchMapIntegratedScraper

# Enhanced modeでスクレイパーを初期化
scraper = ResearchMapIntegratedScraper(mode="enhanced")

# 研究者と競争的研究課題を取得
results = scraper.scrape_all_researchers_and_projects(
    search_url="https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE"
)

# 結果を保存
scraper.save_results(results, "results.json")
scraper.export_to_excel(results, "results.xlsx")
```

### コマンドラインからの実行

#### Enhanced Mode（デフォルト）
```bash
python researchmap_integrated_scraper.py --mode enhanced
```

#### Basic Mode
```bash
python researchmap_integrated_scraper.py --mode basic
```

#### テストモード（最初の5人の研究者のみ処理）
```bash
python researchmap_integrated_scraper.py --mode enhanced --test 5
```

#### カスタム検索URL
```bash
python researchmap_integrated_scraper.py --mode enhanced --search-url "https://researchmap.jp/researchers?affiliation=京都大学"
```

#### カスタム出力ファイル名
```bash
python researchmap_integrated_scraper.py --mode enhanced --output-prefix "my_research"
```

### コマンドラインオプション

| オプション | 説明 | デフォルト値 |
|-----------|------|-------------|
| `--mode` | スクレイピングモード（basic, enhanced, html） | enhanced |
| `--search-url` | 検索URL | 株式会社検索URL |
| `--test` | テストモード（指定した数の研究者のみ処理） | None |
| `--output-prefix` | 出力ファイルのプレフィックス | researchmap_integrated |

## スクレイピングモード詳細

### Basic Mode
最もシンプルなモードで、基本的な研究者情報と競争的研究課題のみを取得します。

**取得情報:**
- 研究者基本情報（名前、所属、職名など）
- 競争的研究課題の基本情報（タイトル、URL、ID）

**使用例:**
```python
scraper = ResearchMapIntegratedScraper(mode="basic")
results = scraper.scrape_all_researchers_and_projects()
```

### Enhanced Mode
最も詳細な情報を取得するモードです。研究者の詳細情報と研究課題の詳細情報を含みます。

**取得情報:**
- 研究者基本情報
- 研究者詳細情報（ORCID、研究キーワード、研究分野など）
- 競争的研究課題の詳細情報（支援システム、期間、説明など）

**使用例:**
```python
scraper = ResearchMapIntegratedScraper(mode="enhanced")
results = scraper.scrape_all_researchers_and_projects()
```

### HTML Mode
従来のHTMLスクレイピング方式を使用します。Basic Modeと同様の機能です。

**使用例:**
```python
scraper = ResearchMapIntegratedScraper(mode="html")
results = scraper.scrape_all_researchers_and_projects()
```

## 出力形式

### JSON出力
研究者情報と競争的研究課題が構造化されたJSON形式で保存されます。

```json
{
  "total_researchers": 100,
  "processed_researchers": 95,
  "total_competitive_projects": 250,
  "researchers": [
    {
      "name": "研究者名",
      "english_name": "English Name",
      "affiliation": "所属機関",
      "position": "職名",
      "researcher_id": "researcher_id",
      "researcher_url": "https://researchmap.jp/researcher_id",
      "orcid_id": "0000-0000-0000-0000",
      "research_keywords": ["キーワード1", "キーワード2"],
      "research_areas": ["研究分野1", "研究分野2"],
      "competitive_projects": [
        {
          "title": "研究課題タイトル",
          "project_url": "https://researchmap.jp/researcher_id/research_projects/123",
          "project_id": "123",
          "is_competitive": true,
          "funding_system": "日本学術振興会 科学研究費補助金",
          "period": "2020年4月 - 2023年3月",
          "description": "研究課題の説明"
        }
      ],
      "competitive_project_count": 1
    }
  ],
  "scraped_at": "2024-01-01 12:00:00",
  "mode": "enhanced",
  "search_url": "https://researchmap.jp/researchers?affiliation=..."
}
```

### Excel出力
研究者情報と競争的研究課題がExcelファイルに保存されます。

**シート構成:**
1. **競争的研究課題** - 研究者情報と競争的研究課題の詳細
2. **サマリー** - 取得結果の統計情報

## 競争的研究資金の判定

以下のキーワードに基づいて競争的研究資金かどうかを自動判定します：

- 科研費、科学研究費
- JST、AMST
- 文部科学省、厚生労働省、経済産業省
- 基盤研究、挑戦的研究、新学術領域
- 特別研究員、若手研究、萌芽研究
- 特別推進研究、科学研究費補助金

## エラーハンドリング

- ネットワークエラーやタイムアウトに対する自動リトライ
- 個別研究者の処理エラーに対する継続処理
- 詳細なログ出力（ファイルとコンソール）
- エラー発生時のスキップ処理

## レート制限対策

- リクエスト間のランダムな待機時間（1-5秒）
- セッション管理による効率的なリクエスト
- 適切なUser-Agent設定

## ログ機能

スクレイピングの進行状況とエラー情報が以下の形式でログに記録されます：

- ログファイル: `researchmap_integrated_scraper.log`
- ログレベル: INFO, WARNING, ERROR
- 出力先: ファイルとコンソール

## 既存スクレイパーとの統合

この統合スクレイパーは以下の既存スクレイパーの機能を統合しています：

- `researchmap_researchers_scraper.py` - 基本機能
- `researchmap_enhanced_scraper.py` - 詳細機能
- `research_map_html_scraper.py` - HTML機能

## 注意事項

1. **利用規約の遵守**: Research Mapの利用規約を遵守してご利用ください
2. **レート制限**: 過度なリクエストを避けるため、適切な間隔を設けて実行してください
3. **データの正確性**: スクレイピングしたデータの正確性については、必ず手動で確認してください

## トラブルシューティング

### よくある問題

1. **ネットワークエラー**
   - インターネット接続を確認
   - プロキシ設定を確認

2. **HTML構造の変更**
   - Research MapのHTML構造が変更された可能性
   - ログを確認してエラーの詳細を確認

3. **メモリ不足**
   - 大量のデータを処理する場合は、`--test`オプションでテスト実行
   - 処理する研究者数を制限

## ライセンス

このプロジェクトは教育・研究目的で作成されています。商用利用の際は、Research Mapの利用規約を確認してください。

## 更新履歴

- v1.0.0: 統合スクレイパーの初回リリース
- 複数のスクレイピングモードをサポート
- 詳細なエラーハンドリングとログ機能
- Excel出力機能の強化
