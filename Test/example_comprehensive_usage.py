#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包括的データ取得機能の使用例

Research Map Integrated Scraperの包括的データ取得機能を使用する例
"""

import sys
import os
import logging
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from researchmap_integrated_scraper import ResearchMapIntegratedScraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def example_comprehensive_data_retrieval():
    """
    包括的データ取得の使用例
    """

    # テスト用研究者URL
    researcher_url = "https://researchmap.jp/hidekanematsu"

    logger.info("=== 包括的データ取得の使用例 ===")

    # スクレイパーの初期化
    scraper = ResearchMapIntegratedScraper()

    try:
        # 包括的データを取得
        logger.info(f"研究者の包括的データを取得中: {researcher_url}")
        comprehensive_data = scraper.get_comprehensive_researcher_data(researcher_url)

        # データを保存
        filename = scraper.save_comprehensive_data(comprehensive_data)

        # サマリーを表示
        summary = comprehensive_data.get('summary', {})
        logger.info(f"\n=== 取得結果サマリー ===")
        logger.info(f"研究者名: {summary.get('researcher_name', 'Unknown')}")
        logger.info(f"所属: {summary.get('affiliation', 'Unknown')}")
        logger.info(f"研究キーワード数: {summary.get('research_keywords_count', 0)}")
        logger.info(f"研究分野数: {summary.get('research_areas_count', 0)}")
        logger.info(f"所属先数: {summary.get('affiliations_count', 0)}")
        logger.info(f"学歴数: {summary.get('education_count', 0)}")
        logger.info(f"総研究課題数: {summary.get('total_projects', 0)}")
        logger.info(f"競争的研究課題数: {summary.get('competitive_projects', 0)}")
        logger.info(f"助成金機関数: {summary.get('unique_institutions_count', 0)}")

        logger.info(f"\n詳細データは {filename} に保存されました")
        logger.info("包括的データ取得完了")

        return comprehensive_data

    except Exception as e:
        logger.error(f"包括的データ取得中にエラーが発生しました: {e}")
        return None

def example_individual_methods():
    """
    個別メソッドの使用例
    """

    researcher_url = "https://researchmap.jp/hidekanematsu"
    scraper = ResearchMapIntegratedScraper()

    logger.info("=== 個別メソッドの使用例 ===")

    try:
        # 1. 基本情報の取得
        logger.info("1. 基本情報を取得中...")
        basic_info = scraper.get_researcher_basic_info(researcher_url)
        logger.info(f"   研究者名: {basic_info.get('name', 'Unknown')}")
        logger.info(f"   所属: {basic_info.get('affiliation', 'Unknown')}")

        # 2. 詳細情報の取得
        logger.info("2. 詳細情報を取得中...")
        detailed_info = scraper.get_researcher_detailed_info(researcher_url)
        logger.info(f"   ORCID: {detailed_info.get('orcid_id', 'N/A')}")

        # 3. 研究キーワードの取得
        logger.info("3. 研究キーワードを取得中...")
        keywords = scraper.get_researcher_keywords(researcher_url)
        logger.info(f"   キーワード数: {len(keywords)}")

        # 4. 研究分野の取得
        logger.info("4. 研究分野を取得中...")
        areas = scraper.get_researcher_areas(researcher_url)
        logger.info(f"   研究分野数: {len(areas)}")

        # 5. 所属先の取得
        logger.info("5. 所属先を取得中...")
        affiliations = scraper.get_researcher_affiliations(researcher_url)
        logger.info(f"   所属先数: {len(affiliations)}")

        # 6. 学歴の取得
        logger.info("6. 学歴を取得中...")
        education = scraper.get_researcher_education(researcher_url)
        logger.info(f"   学歴数: {len(education)}")

        # 7. 研究課題の取得
        logger.info("7. 研究課題を取得中...")
        projects = scraper.get_research_projects(researcher_url)
        competitive_projects = [p for p in projects if p.get('is_competitive', False)]
        logger.info(f"   総研究課題数: {len(projects)}")
        logger.info(f"   競争的研究課題数: {len(competitive_projects)}")

        logger.info("個別メソッドの使用例完了")

    except Exception as e:
        logger.error(f"個別メソッドの使用例でエラーが発生しました: {e}")

def main():
    """
    メイン関数
    """
    logger.info("Research Map Integrated Scraper - 包括的データ取得機能の使用例")

    # 包括的データ取得の使用例
    comprehensive_data = example_comprehensive_data_retrieval()

    if comprehensive_data:
        logger.info("包括的データ取得が成功しました")
    else:
        logger.error("包括的データ取得が失敗しました")

    # 個別メソッドの使用例
    example_individual_methods()

    logger.info("使用例の実行が完了しました")

if __name__ == "__main__":
    main()
