# Research Map Scraper

Research MapのAPIを使用して投資先企業の研究者情報を取得し、研究課題とキーワードを分析するツールです。

## 機能

- 組織名による研究者検索
- 研究者の詳細情報取得（研究課題、キーワード、研究分野）
- 研究者の論文情報取得
- ポートフォリオ企業の研究者分析
- Excelファイルへの結果エクスポート
- 研究レポートの自動生成

## インストール

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 基本的な使用方法

```python
from research_map_scraper import ResearchMapScraper

# Scraperの初期化
scraper = ResearchMapScraper()

# 特定の企業の研究者を検索
researchers = scraper.search_researchers_by_organization("東京大学")
print(f"見つかった研究者数: {len(researchers)}人")

# 研究者の詳細情報を取得
if researchers:
    researcher_id = researchers[0]['id']
    details = scraper.get_researcher_details(researcher_id)
    print(f"研究者名: {details['name']}")
    print(f"研究課題: {details['research_topics']}")
    print(f"キーワード: {details['keywords']}")
```

### 2. ポートフォリオ企業の分析

```python
# ポートフォリオ企業の研究者分析
analysis_result = scraper.analyze_portfolio_companies("portfolio_result.json")

if analysis_result:
    print(f"総研究者数: {analysis_result['total_researchers']}人")

    # 企業別集計
    for company, researchers in analysis_result['company_researchers'].items():
        print(f"{company}: {len(researchers)}人")

    # Excelファイルにエクスポート
    scraper.export_to_excel(analysis_result, "researchers_analysis.xlsx")

    # 研究レポートを生成
    scraper.generate_research_report(analysis_result, "research_report.txt")
```

### 3. サンプル実行

```bash
python research_map_example.py
```

## 入力ファイル形式

### portfolio_result.json

```json
{
  "companies": [
    {"name": "株式会社ジェネシア・ベンチャーズ"},
    {"name": "DEEPCORE Inc."},
    {"name": "Abies Ventures"}
  ]
}
```

## 出力ファイル

### 1. Excelファイル (researchers_analysis.xlsx)

以下のシートが含まれます：

- **研究者詳細**: 各研究者の基本情報、研究課題、キーワード
- **企業別集計**: 企業ごとの研究者数
- **キーワード分析**: キーワードの出現頻度

### 2. テキストレポート (research_report.txt)

以下の内容が含まれます：

- 総研究者数
- 企業別研究者数
- 主要研究キーワード（出現頻度順）
- 各研究者の詳細情報

## API制限について

Research MapのAPIには以下の制限があります：

- リクエスト間隔: 1秒以上
- 1回の検索で最大100件の研究者を取得
- 論文情報は最新50件まで取得

## エラーハンドリング

- API接続エラー
- ファイル読み込みエラー
- JSON解析エラー
- Excel出力エラー

すべてのエラーはログに記録されます。

## カスタマイズ

### APIキーの設定

```python
scraper = ResearchMapScraper(api_key="your_api_key_here")
```

### 検索パラメータの調整

```python
# 検索結果の制限を変更
researchers = scraper.search_researchers_by_organization("企業名", limit=50)

# 論文取得数を変更
publications = scraper.get_researcher_publications(researcher_id, limit=100)
```

## 注意事項

1. **API利用規約**: Research Mapの利用規約に従ってください
2. **レート制限**: API制限を超えないよう適切な間隔でリクエストしてください
3. **データの正確性**: 取得したデータは参考情報として使用し、必要に応じて手動で確認してください
4. **個人情報**: 研究者の個人情報を適切に取り扱ってください

## トラブルシューティング

### よくある問題

1. **API接続エラー**
   - インターネット接続を確認
   - APIキーが正しく設定されているか確認

2. **ファイルが見つからない**
   - ファイルパスが正しいか確認
   - ファイルの文字エンコーディングを確認

3. **Excel出力エラー**
   - openpyxlライブラリがインストールされているか確認
   - 出力先ディレクトリの書き込み権限を確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要望は、GitHubのIssueでお知らせください。
