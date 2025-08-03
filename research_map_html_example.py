#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Research Map HTML Scraper 使用例

このスクリプトは、Research MapのHTMLページから研究者情報をスクレイピングし、
研究課題とキーワードを分析する例を示します。
"""

from research_map_html_scraper import ResearchMapHTMLScraper
import json

def example_usage():
    """
    Research Map HTML Scraperの使用例
    """

    # 1. 基本的な使用方法
    print("=== Research Map HTML Scraper 使用例 ===\n")

    # Scraperの初期化
    scraper = ResearchMapHTMLScraper()

    # 2. 特定の研究者の情報を取得
    print("1. 特定研究者の情報取得例")
    researcher_id = "m-kudo"  # 工藤 正俊

    researcher_info = scraper.get_researcher_profile(researcher_id)

    if researcher_info:
        print(f"研究者名: {researcher_info.get('name', '')}")
        print(f"所属組織: {researcher_info.get('organization', '')}")
        print(f"プロフィールURL: {researcher_info.get('profile_url', '')}")
        print(f"研究課題数: {researcher_info.get('total_projects', 0)}件")

        # 研究課題の詳細を表示
        if researcher_info.get('research_projects'):
            print("\n研究課題:")
            for i, project in enumerate(researcher_info['research_projects'][:3], 1):  # 最新3件
                print(f"  {i}. {project.get('title', '')}")
                print(f"     期間: {project.get('period', '')}")
                print(f"     資金: {project.get('funding', '')}")
                print(f"     研究者: {project.get('authors', '')}")

    print("\n" + "="*50 + "\n")

    # 3. 複数の研究者の情報を取得
    print("2. 複数研究者の情報取得例")

    # サンプルの研究者IDリスト
    researcher_ids = [
        "m-kudo",  # 工藤 正俊
        # 他の研究者IDを追加
    ]

    all_researchers = []
    for researcher_id in researcher_ids:
        print(f"研究者 {researcher_id} の情報を取得中...")
        researcher_info = scraper.get_researcher_profile(researcher_id)
        if researcher_info:
            all_researchers.append(researcher_info)

    print(f"\n取得した研究者数: {len(all_researchers)}人")

    # 4. 結果をファイルにエクスポート
    if all_researchers:
        print("\n3. 結果のエクスポート")

        # CSVファイルにエクスポート
        scraper.export_to_csv(all_researchers, "sample_researchers_data.csv")

        # JSONファイルにエクスポート
        scraper.export_to_json(all_researchers, "sample_researchers_data.json")

        # サマリーレポートを生成
        scraper.generate_summary_report(all_researchers, "sample_researchers_summary.txt")

        print("以下のファイルが生成されました:")
        print("- sample_researchers_data.csv")
        print("- sample_researchers_data.json")
        print("- sample_researchers_summary.txt")

    print("\n" + "="*50 + "\n")

    # 5. 研究課題の詳細分析
    print("4. 研究課題の詳細分析")

    if all_researchers:
        # 資金情報の分析
        funding_types = {}
        for researcher in all_researchers:
            for project in researcher.get('research_projects', []):
                funding = project.get('funding', '')
                if funding:
                    # 資金タイプを分類
                    if '基盤研究' in funding:
                        funding_types['基盤研究'] = funding_types.get('基盤研究', 0) + 1
                    elif '挑戦的' in funding:
                        funding_types['挑戦的研究'] = funding_types.get('挑戦的研究', 0) + 1
                    elif '若手' in funding:
                        funding_types['若手研究'] = funding_types.get('若手研究', 0) + 1
                    else:
                        funding_types['その他'] = funding_types.get('その他', 0) + 1

        print("資金タイプ別研究課題数:")
        for funding_type, count in funding_types.items():
            print(f"  {funding_type}: {count}件")

def custom_analysis():
    """
    カスタム分析の例
    """
    print("\n=== カスタム分析例 ===\n")

    scraper = ResearchMapHTMLScraper()

    # 特定の研究者の研究課題を詳細分析
    researcher_id = "m-kudo"
    researcher_info = scraper.get_researcher_profile(researcher_id)

    if researcher_info and researcher_info.get('research_projects'):
        print(f"研究者: {researcher_info.get('name', '')}")
        print(f"研究課題数: {len(researcher_info['research_projects'])}件\n")

        # 研究期間の分析
        periods = []
        for project in researcher_info['research_projects']:
            period = project.get('period', '')
            if period:
                periods.append(period)

        print("研究期間の分布:")
        for period in periods[:5]:  # 最新5件
            print(f"  - {period}")

        # 研究分野の分析（タイトルから推測）
        research_fields = {}
        for project in researcher_info['research_projects']:
            title = project.get('title', '')
            if '癌' in title or '腫瘍' in title:
                research_fields['がん研究'] = research_fields.get('がん研究', 0) + 1
            elif '免疫' in title:
                research_fields['免疫学'] = research_fields.get('免疫学', 0) + 1
            elif '超音波' in title:
                research_fields['超音波診断'] = research_fields.get('超音波診断', 0) + 1
            elif '肝' in title:
                research_fields['肝臓研究'] = research_fields.get('肝臓研究', 0) + 1

        print("\n研究分野の分布:")
        for field, count in research_fields.items():
            print(f"  {field}: {count}件")

def main():
    """
    メイン実行関数
    """
    try:
        # 基本的な使用例
        example_usage()

        # カスタム分析例
        custom_analysis()

        print("\n=== 実行完了 ===")
        print("生成されたファイル:")
        print("- sample_researchers_data.csv: 研究者データ（CSV）")
        print("- sample_researchers_data.json: 研究者データ（JSON）")
        print("- sample_researchers_summary.txt: 研究者サマリー（テキスト）")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
