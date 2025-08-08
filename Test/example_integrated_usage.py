#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of Research Map Integrated Scraper

統合スクレイパーの使用例
"""

from researchmap_integrated_scraper import ResearchMapIntegratedScraper
import json

def example_basic_usage():
    """
    基本的な使用例
    """
    print("=== 基本的な使用例 ===")

    # Enhanced modeでスクレイパーを初期化
    scraper = ResearchMapIntegratedScraper(mode="enhanced")

    # 研究者と競争的研究課題を取得（テスト用に最初の3人のみ）
    results = scraper.scrape_all_researchers_and_projects(
        search_url="https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE",
        max_researchers=3
    )

    print(f"取得した研究者数: {results['processed_researchers']}")
    print(f"競争的研究課題数: {results['total_competitive_projects']}")

    # 結果を保存
    scraper.save_results(results, "example_results.json")
    scraper.export_to_excel(results, "example_results.xlsx")

    print("結果を example_results.json と example_results.xlsx に保存しました")

def example_different_modes():
    """
    異なるモードの使用例
    """
    print("\n=== 異なるモードの使用例 ===")

    # Basic mode
    print("Basic mode:")
    basic_scraper = ResearchMapIntegratedScraper(mode="basic")
    basic_results = basic_scraper.scrape_all_researchers_and_projects(
        max_researchers=2
    )
    print(f"  Basic mode: 研究者{basic_results['processed_researchers']}人, "
          f"競争的研究課題{basic_results['total_competitive_projects']}件")

    # Enhanced mode
    print("Enhanced mode:")
    enhanced_scraper = ResearchMapIntegratedScraper(mode="enhanced")
    enhanced_results = enhanced_scraper.scrape_all_researchers_and_projects(
        max_researchers=2
    )
    print(f"  Enhanced mode: 研究者{enhanced_results['processed_researchers']}人, "
          f"競争的研究課題{enhanced_results['total_competitive_projects']}件")

    # HTML mode
    print("HTML mode:")
    html_scraper = ResearchMapIntegratedScraper(mode="html")
    html_results = html_scraper.scrape_all_researchers_and_projects(
        max_researchers=2
    )
    print(f"  HTML mode: 研究者{html_results['processed_researchers']}人, "
          f"競争的研究課題{html_results['total_competitive_projects']}件")

def example_custom_search():
    """
    カスタム検索の例
    """
    print("\n=== カスタム検索の例 ===")

    scraper = ResearchMapIntegratedScraper(mode="enhanced")

    # 異なる検索条件でスクレイピング
    search_urls = [
        "https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE",
        "https://researchmap.jp/researchers?affiliation=%E5%A4%A7%E5%AD%A6",
        "https://researchmap.jp/researchers?affiliation=%E7%A0%94%E7%A9%B6%E6%A9%9F%E9%96%A2"
    ]

    for i, search_url in enumerate(search_urls, 1):
        print(f"\n検索 {i}: {search_url}")

        results = scraper.scrape_all_researchers_and_projects(
            search_url=search_url,
            max_researchers=1  # テスト用に1人のみ
        )

        print(f"  取得した研究者数: {results['processed_researchers']}")
        print(f"  競争的研究課題数: {results['total_competitive_projects']}")

def example_data_analysis():
    """
    取得したデータの分析例
    """
    print("\n=== データ分析の例 ===")

    # Enhanced modeでデータを取得
    scraper = ResearchMapIntegratedScraper(mode="enhanced")
    results = scraper.scrape_all_researchers_and_projects(
        max_researchers=5
    )

    # 統計情報の表示
    print(f"総研究者数: {results['total_researchers']}")
    print(f"処理済み研究者数: {results['processed_researchers']}")
    print(f"競争的研究課題総数: {results['total_competitive_projects']}")

    # 研究者ごとの詳細情報
    print("\n研究者詳細:")
    for i, researcher in enumerate(results['researchers'], 1):
        print(f"\n{i}. {researcher.get('name', 'Unknown')}")
        print(f"   所属: {researcher.get('affiliation', 'N/A')}")
        print(f"   職名: {researcher.get('position', 'N/A')}")
        print(f"   ORCID: {researcher.get('orcid_id', 'N/A')}")
        print(f"   研究キーワード数: {len(researcher.get('research_keywords', []))}")
        print(f"   研究分野数: {len(researcher.get('research_areas', []))}")
        print(f"   競争的研究課題数: {researcher.get('competitive_project_count', 0)}")

        # 競争的研究課題の詳細
        competitive_projects = researcher.get('competitive_projects', [])
        if competitive_projects:
            print("   競争的研究課題:")
            for j, project in enumerate(competitive_projects, 1):
                print(f"     {j}. {project.get('title', 'Unknown')}")
                if project.get('funding_system'):
                    print(f"        支援システム: {project['funding_system']}")
                if project.get('period'):
                    print(f"        期間: {project['period']}")

def example_error_handling():
    """
    エラーハンドリングの例
    """
    print("\n=== エラーハンドリングの例 ===")

    try:
        # 無効なURLでテスト
        scraper = ResearchMapIntegratedScraper(mode="enhanced")
        results = scraper.scrape_all_researchers_and_projects(
            search_url="https://researchmap.jp/invalid-url",
            max_researchers=1
        )
        print("無効なURLでもエラーハンドリングが機能しました")

    except Exception as e:
        print(f"エラーが適切に処理されました: {e}")

def main():
    """
    メイン実行関数
    """
    print("Research Map Integrated Scraper - 使用例")
    print("=" * 50)

    # 各例を実行
    examples = [
        ("基本的な使用例", example_basic_usage),
        ("異なるモードの使用例", example_different_modes),
        ("カスタム検索の例", example_custom_search),
        ("データ分析の例", example_data_analysis),
        ("エラーハンドリングの例", example_error_handling)
    ]

    for example_name, example_func in examples:
        try:
            example_func()
            print(f"\n✅ {example_name} が正常に完了しました")
        except Exception as e:
            print(f"\n❌ {example_name} でエラーが発生しました: {e}")

        print("-" * 50)

    print("\n🎉 すべての例が完了しました！")
    print("生成されたファイルを確認してください:")
    print("- example_results.json")
    print("- example_results.xlsx")

if __name__ == "__main__":
    main()
