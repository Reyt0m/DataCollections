# Research Map Integrated Scraper

Research Mapから研究者情報と競争的研究課題を取得する統合スクレイパーです。複数のスクレイピングモードをサポートし、様々な用途に対応できます。

## 機能概要

### 機能概要

このスクレイパーは以下の機能を提供します：

1. **包括的データ取得** - 一人の研究者について取得できるすべてのデータを包括的に取得
2. **一括データ取得** - 複数の研究者の情報と競争的研究課題を一括取得
3. **詳細情報取得** - 研究者の詳細情報（ORCID、研究キーワード、研究分野など）と競争的研究課題の詳細取得

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

#### 包括的データ
- 研究者の基本情報（検索結果ページから）
- 研究者の詳細情報（ORCID、J-GLOBAL ID、researchmap会員ID）
- 研究キーワード（詳細情報付き）
- 研究分野（詳細情報付き）
- すべての所属先情報
- 学歴情報
- 研究課題（詳細情報付き）
- 統計サマリー情報

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

# スクレイパーを初期化
scraper = ResearchMapIntegratedScraper()

# 研究者と競争的研究課題を取得
results = scraper.scrape_all_researchers_and_projects(
    search_url="https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE"
)

# 結果を保存
scraper.save_results(results, "results.json")
scraper.export_to_excel(results, "results.xlsx")
```

### コマンドラインからの実行

#### 一括データ取得（デフォルト）
```bash
python researchmap_integrated_scraper.py
```

#### 包括的データ取得（一人の研究者）
```bash
python researchmap_integrated_scraper.py --researcher-url "https://researchmap.jp/hidekanematsu"
```

#### テストモード（最初の5人の研究者のみ処理）
```bash
python researchmap_integrated_scraper.py --test 5
```

#### カスタム検索URL
```bash
python researchmap_integrated_scraper.py --search-url "https://researchmap.jp/researchers?affiliation=京都大学"
```

#### カスタム出力ファイル名
```bash
python researchmap_integrated_scraper.py --output-prefix "my_research"
```

### コマンドラインオプション

| オプション | 説明 | デフォルト値 |
|-----------|------|-------------|
| `--search-url` | 検索URL | 株式会社検索URL |
| `--researcher-url` | 包括的データ取得用の研究者URL | None |
| `--test` | テストモード（指定した数の研究者のみ処理） | None |
| `--output-prefix` | 出力ファイルのプレフィックス | researchmap_integrated |

## 機能詳細

### 一括データ取得
複数の研究者の情報と競争的研究課題を一括で取得します。

**取得情報:**
- 研究者基本情報（名前、所属、職名など）
- 研究者詳細情報（ORCID、研究キーワード、研究分野など）
- 競争的研究課題の詳細情報（支援システム、期間、説明など）

**使用例:**
```python
scraper = ResearchMapIntegratedScraper()
results = scraper.scrape_all_researchers_and_projects()
```

### 包括的データ取得
一人の研究者について取得できるすべてのデータを包括的に取得します。

**取得情報:**
- 研究者の基本情報（検索結果ページから）
- 研究者の詳細情報（ORCID、J-GLOBAL ID、researchmap会員ID）
- 研究キーワード（詳細情報付き）
- 研究分野（詳細情報付き）
- すべての所属先情報
- 学歴情報
- 研究課題（詳細情報付き）
- 統計サマリー情報

**使用例:**
```python
scraper = ResearchMapIntegratedScraper()
comprehensive_data = scraper.get_comprehensive_researcher_data("https://researchmap.jp/hidekanematsu")
filename = scraper.save_comprehensive_data(comprehensive_data)
```

**個別メソッドの使用例:**
```python
scraper = ResearchMapIntegratedScraper()

# 基本情報の取得
basic_info = scraper.get_researcher_basic_info(researcher_url)

# 詳細情報の取得
detailed_info = scraper.get_researcher_detailed_info(researcher_url)

# 研究キーワードの取得
keywords = scraper.get_researcher_keywords(researcher_url)

# 研究分野の取得
areas = scraper.get_researcher_areas(researcher_url)

# 所属先の取得
affiliations = scraper.get_researcher_affiliations(researcher_url)

# 学歴の取得
education = scraper.get_researcher_education(researcher_url)

# 研究課題の取得
projects = scraper.get_research_projects(researcher_url)

# サマリー情報の生成
summary = scraper.generate_summary(comprehensive_data)
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

### 包括的データ出力
一人の研究者の包括的データがJSONファイルに保存されます。

```json
{
  "researcher_url": "https://researchmap.jp/hidekanematsu",
  "basic_info": {
    "name": "兼松 秀行",
    "english_name": "Hideyuki Kanematsu",
    "affiliation": "所属機関",
    "position": "職名",
    "researcher_id": "hidekanematsu",
    "researcher_url": "https://researchmap.jp/hidekanematsu"
  },
  "detailed_info": {
    "orcid_id": "0000-0000-0000-0000",
    "jglobal_id": "202001000000000000",
    "researchmap_member_id": "12345",
    "research_keywords": ["キーワード1", "キーワード2"],
    "research_areas": ["研究分野1", "研究分野2"],
    "all_affiliations": ["所属先1", "所属先2"]
  },
  "research_keywords": [
    {
      "keyword": "キーワード名",
      "url": "https://researchmap.jp/keywords/123",
      "keyword_id": "123"
    }
  ],
  "research_areas": [
    {
      "area": "研究分野名",
      "url": "https://researchmap.jp/areas/456",
      "area_id": "456"
    }
  ],
  "all_affiliations": [
    {
      "institution": "所属機関名",
      "url": "https://researchmap.jp/institutions/789",
      "position": "職名",
      "full_text": "所属機関名 職名"
    }
  ],
  "education": [
    {
      "period": "2010年4月 - 2014年3月",
      "institution": "大学名",
      "url": "https://researchmap.jp/institutions/101",
      "education_id": "101"
    }
  ],
  "research_projects": {
    "enhanced_mode": [
      {
        "title": "研究課題タイトル",
        "project_url": "https://researchmap.jp/hidekanematsu/research_projects/123",
        "project_id": "123",
        "is_competitive": true,
        "funding_system": "日本学術振興会 科学研究費補助金",
        "period": "2020年4月 - 2023年3月",
        "institution": "日本学術振興会",
        "project_type": "科学研究費補助金"
      }
    ],
    "basic_mode": [
      {
        "title": "研究課題タイトル",
        "project_url": "https://researchmap.jp/hidekanematsu/research_projects/123",
        "project_id": "123",
        "is_competitive": true
      }
    ]
  },
  "summary": {
    "researcher_name": "兼松 秀行",
    "researcher_id": "hidekanematsu",
    "affiliation": "所属機関",
    "position": "職名",
    "orcid_id": "0000-0000-0000-0000",
    "research_keywords_count": 5,
    "research_areas_count": 3,
    "affiliations_count": 2,
    "education_count": 1,
    "total_projects_enhanced": 10,
    "total_projects_basic": 10,
    "competitive_projects_enhanced": 8,
    "competitive_projects_basic": 8,
    "funding_institutions": {
      "日本学術振興会": 5,
      "JST": 3
    },
    "unique_institutions_count": 2,
    "research_periods": ["2020年4月 - 2023年3月", "2023年4月 - 2026年3月"]
  }
}
```

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

## 使用例スクリプト

包括的データ取得機能の使用例は `example_comprehensive_usage.py` で確認できます：

```bash
python example_comprehensive_usage.py
```

このスクリプトは以下の機能をデモンストレーションします：

1. **包括的データ取得** - 一人の研究者のすべてのデータを取得
2. **個別メソッドの使用** - 各機能を個別に使用する方法
3. **データ保存** - 取得したデータの保存方法
4. **サマリー表示** - 取得結果の統計情報表示

## 既存スクレイパーとの統合

この統合スクレイパーは以下の既存スクレイパーの機能を統合しています：

- `researchmap_researchers_scraper.py` - 基本機能
- `researchmap_enhanced_scraper.py` - 詳細機能
- `research_map_html_scraper.py` - HTML機能
- `comprehensive_researcher_data.py` - 包括的データ取得機能

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

- v2.0.0: シンプル化と機能統合
  - モード選択を削除し、最も詳細な機能をデフォルトに
  - 包括的データ取得機能の統合
  - 個別メソッドの追加（基本情報、詳細情報、研究キーワード、研究分野、所属先、学歴）
  - サマリー情報生成機能
  - 包括的データ保存機能
  - 使用例スクリプトの追加
- v1.1.0: 包括的データ取得機能の追加
  - Comprehensive Modeの追加
  - 一人の研究者の包括的データ取得機能
  - 個別メソッドの追加（基本情報、詳細情報、研究キーワード、研究分野、所属先、学歴）
  - サマリー情報生成機能
  - 包括的データ保存機能
  - 使用例スクリプトの追加
- v1.0.0: 統合スクレイパーの初回リリース
  - 複数のスクレイピングモードをサポート
  - 詳細なエラーハンドリングとログ機能
  - Excel出力機能の強化
