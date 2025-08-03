#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Research Map Scraper 使用例

このスクリプトは、Research MapのAPIを使用して投資先企業の研究者情報を取得し、
研究課題とキーワードを分析する例を示します。
"""

from research_map_scraper import ResearchMapScraper
import json

def example_usage():
    """
    Research Map Scraperの使用例
    """

    # 1. 基本的な使用方法
    print("=== Research Map Scraper 使用例 ===\n")

    # Scraperの初期化
    scraper = ResearchMapScraper()

    # 2. 特定の企業の研究者を検索
    print("1. 特定企業の研究者検索例")
    company_name = "東京大学"
    researchers = scraper.search_researchers_by_organization(company_name)
    print(f"{company_name}の研究者数: {len(researchers)}人")

    if researchers:
        # 最初の研究者の詳細を取得
        first_researcher = researchers[0]
        researcher_id = first_researcher.get('id')

        if researcher_id:
            details = scraper.get_researcher_details(researcher_id)
            print(f"\n研究者名: {details.get('name', '')}")
            print(f"所属: {details.get('organization', '')}")
            print(f"研究課題: {details.get('research_topics', [])}")
            print(f"キーワード: {details.get('keywords', [])}")

    print("\n" + "="*50 + "\n")

    # 3. ポートフォリオ企業の分析（portfolio_result.jsonがある場合）
    print("2. ポートフォリオ企業の研究者分析")

    # サンプルのポートフォリオデータを作成
    sample_portfolio = {
        "companies": [
            {"name": "株式会社ジェネシア・ベンチャーズ"},
            {"name": "DEEPCORE Inc."},
            {"name": "Abies Ventures"},
            {"name": "Changer Capital ANRI"},
            {"name": "15th Rock"},
            {"name": "株式会社サムライインキュベート"},
            {"name": "インキュベイトファンド株式会社"},
            {"name": "株式会社デフタ・キャピタル"}
        ]
    }

    # サンプルデータをJSONファイルに保存
    with open("sample_portfolio.json", "w", encoding="utf-8") as f:
        json.dump(sample_portfolio, f, ensure_ascii=False, indent=2)

    # 分析実行
    analysis_result = scraper.analyze_portfolio_companies("sample_portfolio.json")

    if analysis_result:
        print(f"総研究者数: {analysis_result.get('total_researchers', 0)}人")

        # 企業別集計を表示
        print("\n企業別研究者数:")
        for company, researchers in analysis_result.get('company_researchers', {}).items():
            print(f"  {company}: {len(researchers)}人")

        # 結果をExcelファイルにエクスポート
        scraper.export_to_excel(analysis_result, "sample_researchers_analysis.xlsx")

        # 研究レポートを生成
        scraper.generate_research_report(analysis_result, "sample_research_report.txt")

        print("\n分析結果を以下のファイルに保存しました:")
        print("- sample_researchers_analysis.xlsx")
        print("- sample_research_report.txt")

    print("\n" + "="*50 + "\n")

    # 4. 特定の研究者の論文情報を取得
    print("3. 研究者の論文情報取得例")

    if researchers and len(researchers) > 0:
        researcher_id = researchers[0].get('id')
        if researcher_id:
            publications = scraper.get_researcher_publications(researcher_id)
            print(f"論文数: {len(publications)}件")

            if publications:
                print("最新論文:")
                for i, pub in enumerate(publications[:3]):  # 最新3件
                    title = pub.get('title', '')
                    year = pub.get('year', '')
                    print(f"  {i+1}. {title} ({year})")

def custom_analysis():
    """
    カスタム分析の例
    """
    print("\n=== カスタム分析例 ===\n")

    scraper = ResearchMapScraper()

    # 特定のキーワードで研究者を検索
    keywords_to_search = ["AI", "機械学習", "ブロックチェーン", "バイオテクノロジー"]

    for keyword in keywords_to_search:
        print(f"キーワード '{keyword}' で研究者を検索中...")
        researchers = scraper.search_researchers_by_organization(keyword)
        print(f"  見つかった研究者数: {len(researchers)}人")

        if researchers:
            # 最初の研究者の詳細を取得
            first_researcher = researchers[0]
            researcher_id = first_researcher.get('id')

            if researcher_id:
                details = scraper.get_researcher_details(researcher_id)
                print(f"  代表研究者: {details.get('name', '')}")
                print(f"  所属: {details.get('organization', '')}")
                print(f"  研究分野: {details.get('research_fields', [])}")
                print()

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
        print("- sample_portfolio.json: サンプルポートフォリオデータ")
        print("- sample_researchers_analysis.xlsx: 研究者分析結果（Excel）")
        print("- sample_research_report.txt: 研究レポート（テキスト）")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
