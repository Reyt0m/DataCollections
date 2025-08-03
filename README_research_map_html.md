# Research Map HTML Scraper

Research MapのHTMLページから研究者情報をスクレイピングし、名前、競争的資金の研究課題リスト、URLなどを含んだデータを取得するツールです。

## 機能

- 研究者のプロフィール情報取得（名前、所属組織）
- 研究課題一覧の取得（タイトル、期間、資金情報、研究者）
- ポートフォリオ企業の研究者情報スクレイピング
- CSVファイルへの結果エクスポート
- JSONファイルへの結果エクスポート
- サマリーレポートの自動生成

## インストール

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 基本的な使用方法

```python
from research_map_html_scraper import ResearchMapHTMLScraper

# Scraperの初期化
scraper = ResearchMapHTMLScraper()

# 特定の研究者の情報を取得
researcher_id = "m-kudo"  # 工藤 正俊
researcher_info = scraper.get_researcher_profile(researcher_id)

if researcher_info:
    print(f"研究者名: {researcher_info['name']}")
    print(f"所属組織: {researcher_info['organization']}")
    print(f"研究課題数: {researcher_info['total_projects']}件")

    # 研究課題の詳細を表示
    for project in researcher_info['research_projects']:
        print(f"- {project['title']}")
        print(f"  期間: {project['period']}")
        print(f"  資金: {project['funding']}")
```

### 2. 複数研究者の情報取得

```python
# 研究者IDリスト
researcher_ids = ["m-kudo", "researcher2", "researcher3"]

all_researchers = []
for researcher_id in researcher_ids:
    researcher_info = scraper.get_researcher_profile(researcher_id)
    if researcher_info:
        all_researchers.append(researcher_info)

# 結果をファイルにエクスポート
scraper.export_to_csv(all_researchers, "researchers_data.csv")
scraper.export_to_json(all_researchers, "researchers_data.json")
scraper.generate_summary_report(all_researchers, "researchers_summary.txt")
```

### 3. サンプル実行

```bash
python research_map_html_example.py
```

## 出力ファイル

### 1. CSVファイル (researchers_data.csv)

以下の列が含まれます：

- **研究者ID**: 研究者の一意識別子
- **研究者名**: 研究者の名前
- **所属組織**: 研究者の所属組織
- **企業**: 関連する企業名
- **プロフィールURL**: 研究者のプロフィールページURL
- **研究課題URL**: 研究課題一覧ページURL
- **研究課題ID**: 研究課題の一意識別子
- **研究課題タイトル**: 研究課題のタイトル
- **研究期間**: 研究期間
- **資金情報**: 資金の種類と情報
- **研究者**: 研究課題に関連する研究者
- **総研究課題数**: 研究者の総研究課題数

### 2. JSONファイル (researchers_data.json)

研究者ごとの詳細情報が構造化されたJSON形式で保存されます。

### 3. テキストレポート (researchers_summary.txt)

以下の内容が含まれます：

- 総研究者数と総研究課題数
- 企業別統計
- 各研究者の詳細情報と研究課題リスト

## データ構造

### 研究者情報

```json
{
  "researcher_id": "m-kudo",
  "name": "工藤 正俊",
  "organization": "東京大学",
  "profile_url": "https://researchmap.jp/m-kudo",
  "research_projects_url": "https://researchmap.jp/m-kudo/research_projects",
  "research_projects": [...],
  "total_projects": 25
}
```

### 研究課題情報

```json
{
  "project_id": "45306181",
  "title": "免疫チェックポイント阻害剤投与に伴う急速な腫瘍増大(HPD)の発症機序の解析",
  "project_url": "https://researchmap.jp/m-kudo/research_projects/45306181",
  "period": "2022年4月 - 2025年3月",
  "funding": "日本学術振興会 科学研究費助成事業 基盤研究(C)",
  "authors": "萩原 智, 工藤 正俊, 西田 直生志"
}
```

## 注意事項

1. **利用規約**: Research Mapの利用規約に従ってください
2. **レート制限**: サーバーに負荷をかけないよう適切な間隔でリクエストしてください
3. **データの正確性**: 取得したデータは参考情報として使用し、必要に応じて手動で確認してください
4. **研究者ID**: 研究者IDは事前に把握している必要があります

## 制限事項

- 組織名での研究者検索は簡易版です（既知の研究者IDリストを使用）
- 完全な検索機能を使用するには、Research MapのAPIを利用する必要があります
- HTMLの構造変更により、スクレイピングが正常に動作しない可能性があります

## エラーハンドリング

- ネットワーク接続エラー
- HTML解析エラー
- ファイル出力エラー

すべてのエラーはログに記録されます。

## カスタマイズ

### 研究者IDリストの設定

```python
# 研究者IDリストをカスタマイズ
researcher_ids = [
    "m-kudo",      # 工藤 正俊
    "researcher2", # 他の研究者
    "researcher3"  # 他の研究者
]
```

### 出力ファイル名の変更

```python
# 出力ファイル名をカスタマイズ
scraper.export_to_csv(researchers_data, "custom_researchers.csv")
scraper.export_to_json(researchers_data, "custom_researchers.json")
scraper.generate_summary_report(researchers_data, "custom_summary.txt")
```

## トラブルシューティング

### よくある問題

1. **研究者情報が取得できない**
   - 研究者IDが正しいか確認
   - ネットワーク接続を確認
   - Research Mapのサイトが正常に動作しているか確認

2. **研究課題が取得できない**
   - 研究者の研究課題ページが存在するか確認
   - HTMLの構造が変更されていないか確認

3. **ファイル出力エラー**
   - 出力先ディレクトリの書き込み権限を確認
   - ファイルが他のプロセスで使用されていないか確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要望は、GitHubのIssueでお知らせください。
