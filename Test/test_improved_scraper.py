#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved Portfolio Scraper Test Script
実際のHTMLファイルを使用して改善されたスクレイピング機能をテストします
"""

import os
import sys
from bs4 import BeautifulSoup
from portfolio_scraper import PortfolioScraper
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_html_file_scraping():
    """HTMLファイルを使用したスクレイピングテスト"""

    # テスト用HTMLファイルのリスト
    test_files = [
        "COMPANIES _ 株式会社ジェネシア・ベンチャーズ（Genesia Ventures, Inc.）.html",
        "INVESTMENT _ DEEPCORE Inc. - 株式会社ディープコア.html",
        "PORTFOLIO - 株式会社サムライインキュベート.html",
        "株式会社デフタ・キャピタル.html",
        "インキュベイトファンド株式会社.html"
    ]

    # スクレイパーの初期化（OCR機能なしでテスト）
    scraper = PortfolioScraper(headless=True, timeout=10, use_ocr=False)

    results = []

    for html_file in test_files:
        if not os.path.exists(html_file):
            logger.warning(f"HTMLファイルが見つかりません: {html_file}")
            continue

        logger.info(f"テスト開始: {html_file}")

        try:
            # HTMLファイルを読み込み
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # BeautifulSoupでパース
            soup = BeautifulSoup(html_content, 'lxml')

            # ポートフォリオタブを探す
            portfolio_url = scraper.find_portfolio_tab(soup, f"file://{html_file}")

            # 会社名を抽出
            companies = scraper.extract_companies_from_page(soup, f"file://{html_file}")

            result = {
                'file': html_file,
                'portfolio_url': portfolio_url,
                'companies': list(companies),
                'company_count': len(companies),
                'error': None
            }

            results.append(result)

            logger.info(f"結果: {len(companies)}社の会社名を抽出")
            if companies:
                logger.info(f"会社名例: {list(companies)[:5]}")  # 最初の5社を表示

        except Exception as e:
            logger.error(f"エラーが発生しました: {html_file} - {e}")
            results.append({
                'file': html_file,
                'portfolio_url': None,
                'companies': [],
                'company_count': 0,
                'error': str(e)
            })

    # 結果の表示
    print("\n" + "="*80)
    print("テスト結果サマリー")
    print("="*80)

    total_companies = 0
    successful_files = 0

    for result in results:
        print(f"\nファイル: {result['file']}")
        print(f"  ポートフォリオURL: {result['portfolio_url']}")
        print(f"  抽出された会社数: {result['company_count']}")
        print(f"  エラー: {result['error']}")

        if result['companies']:
            print(f"  会社名例: {result['companies'][:3]}")  # 最初の3社を表示
            total_companies += result['company_count']
            successful_files += 1

    print(f"\n" + "="*80)
    print(f"総合結果:")
    print(f"  処理したファイル数: {len(results)}")
    print(f"  成功したファイル数: {successful_files}")
    print(f"  総抽出会社数: {total_companies}")
    print("="*80)

    return results

def test_ocr_functionality():
    """OCR機能のテスト（実際の画像URLがある場合）"""

    logger.info("OCR機能のテストを開始します...")

    # スクレイパーの初期化（OCR機能付きでテスト）
    scraper = PortfolioScraper(headless=True, timeout=10, use_ocr=True)

    if not scraper.use_ocr:
        logger.warning("OCR機能が利用できません。easyocrまたはpytesseractをインストールしてください。")
        return

    # テスト用の画像URL（実際のURLに置き換えてください）
    test_image_urls = [
        # "https://example.com/logo1.png",
        # "https://example.com/logo2.jpg",
    ]

    if not test_image_urls:
        logger.info("テスト用の画像URLが設定されていません。")
        return

    for img_url in test_image_urls:
        try:
            logger.info(f"画像からテキスト抽出テスト: {img_url}")
            extracted_text = scraper.extract_text_from_image(img_url)

            if extracted_text:
                logger.info(f"抽出されたテキスト: {extracted_text}")
            else:
                logger.warning("テキストの抽出に失敗しました")

        except Exception as e:
            logger.error(f"画像処理エラー: {e}")

def test_portfolio_keywords():
    """ポートフォリオキーワード検出のテスト"""

    logger.info("ポートフォリオキーワード検出のテストを開始します...")

    scraper = PortfolioScraper()

    # テスト用URL
    test_urls = [
        "https://example.com/portfolio",
        "https://example.com/investment",
        "https://example.com/partners",
        "https://example.com/companies",
        "https://example.com/investments",
        "https://example.com/portfolio-companies",
        "https://example.com/投資先",
        "https://example.com/ポートフォリオ",
        "https://example.com/random-page"
    ]

    for url in test_urls:
        # モックHTMLを作成
        mock_html = f"""
        <html>
        <body>
            <nav>
                <a href="/portfolio">Portfolio</a>
                <a href="/investment">Investment</a>
                <a href="/partners">Partners</a>
            </nav>
            <div>
                <a href="{url}">Current Page</a>
            </div>
        </body>
        </html>
        """

        soup = BeautifulSoup(mock_html, 'lxml')
        portfolio_url = scraper.find_portfolio_tab(soup, url)

        logger.info(f"URL: {url}")
        logger.info(f"  検出されたポートフォリオURL: {portfolio_url}")

def main():
    """メイン関数"""

    print("改善されたポートフォリオスクレイパーのテストを開始します...")
    print("="*80)

    # 1. HTMLファイルを使用したスクレイピングテスト
    print("\n1. HTMLファイルを使用したスクレイピングテスト")
    print("-" * 50)
    results = test_html_file_scraping()

    # 2. ポートフォリオキーワード検出テスト
    print("\n2. ポートフォリオキーワード検出テスト")
    print("-" * 50)
    test_portfolio_keywords()

    # 3. OCR機能テスト（オプション）
    print("\n3. OCR機能テスト")
    print("-" * 50)
    test_ocr_functionality()

    print("\n" + "="*80)
    print("テスト完了")
    print("="*80)

    # 結果の保存
    import json
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nテスト結果を test_results.json に保存しました。")

if __name__ == "__main__":
    main()
