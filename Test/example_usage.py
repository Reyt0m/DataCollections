#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portfolio Scraper Tool 使用例
"""

from portfolio_scraper import PortfolioScraper, load_urls_from_file
import json

def example_basic_usage():
    """基本的な使用方法の例"""
    print("=== 基本的な使用方法 ===")

    # URLリスト
    urls = [
        "https://example.com",
        "https://example.org"
    ]

    # スクレイパーの初期化
    scraper = PortfolioScraper(headless=True, timeout=10)

    try:
        # スクレイピング実行
        results = scraper.scrape_urls(urls)

        # 結果の表示
        for result in results:
            print(f"URL: {result['url']}")
            print(f"Portfolio URL: {result['portfolio_url']}")
            print(f"Companies: {result['companies']}")
            print(f"Method: {result['method']}")
            print(f"Error: {result['error']}")
            print("-" * 50)

        # 結果を保存
        scraper.save_results(results, 'example_results.json')
        scraper.save_results_csv(results, 'example_results.csv')

    finally:
        scraper.close()

def example_file_usage():
    """ファイルからURLを読み込む例"""
    print("=== ファイルからURLを読み込む例 ===")

    # URLファイルから読み込み
    urls = load_urls_from_file('urls.txt')

    if not urls:
        print("URLファイルが見つからないか、空です")
        return

    # スクレイパーの初期化（ブラウザを表示）
    scraper = PortfolioScraper(headless=False, timeout=15)

    try:
        # 最初の3つのURLのみ処理
        limited_urls = urls[:3]
        results = scraper.scrape_urls(limited_urls)

        # 統計情報の表示
        total_companies = sum(len(result['companies']) for result in results)
        successful_scrapes = sum(1 for result in results if not result['error'])

        print(f"処理したURL数: {len(limited_urls)}")
        print(f"成功したURL数: {successful_scrapes}")
        print(f"抽出された会社名数: {total_companies}")

    finally:
        scraper.close()

def example_custom_company_patterns():
    """カスタム会社名パターンの例"""
    print("=== カスタム会社名パターンの例 ===")

    # スクレイパーの初期化
    scraper = PortfolioScraper()

    # カスタムパターンを追加
    custom_patterns = [
        r'([^\s]+)\s*グループ',
        r'([^\s]+)\s*ホールディングス',
        r'([^\s]+)\s*ベンチャーズ',
    ]
    scraper.company_patterns.extend(custom_patterns)

    # テスト用のHTML
    test_html = """
    <html>
        <body>
            <h1>投資先企業</h1>
            <ul>
                <li>株式会社テスト</li>
                <li>サンプルグループ</li>
                <li>ベンチャー企業 Inc.</li>
            </ul>
        </body>
    </html>
    """

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(test_html, 'lxml')
    companies = scraper.extract_companies_from_page(soup)

    print(f"抽出された会社名: {list(companies)}")
    scraper.close()

def example_error_handling():
    """エラーハンドリングの例"""
    print("=== エラーハンドリングの例 ===")

    # 無効なURLを含むリスト
    urls = [
        "https://invalid-url-that-does-not-exist.com",
        "https://httpstat.us/404",
        "https://httpstat.us/500"
    ]

    scraper = PortfolioScraper()

    try:
        results = scraper.scrape_urls(urls)

        for result in results:
            if result['error']:
                print(f"エラーが発生: {result['url']} - {result['error']}")
            else:
                print(f"成功: {result['url']}")

    finally:
        scraper.close()

if __name__ == "__main__":
    print("Portfolio Scraper Tool 使用例")
    print("=" * 50)

    # 各例を実行
    example_basic_usage()
    print()

    example_file_usage()
    print()

    example_custom_company_patterns()
    print()

    example_error_handling()
    print()

    print("使用例の実行が完了しました")
