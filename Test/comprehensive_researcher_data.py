#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一人の研究者について取得できるすべてのデータを取得する包括的スクリプト
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from researchmap_integrated_scraper import ResearchMapIntegratedScraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_comprehensive_researcher_data(researcher_url: str) -> Dict[str, Any]:
    """
    一人の研究者について取得できるすべてのデータを取得

    Args:
        researcher_url (str): 研究者のURL

    Returns:
        Dict[str, Any]: 研究者の包括的なデータ
    """

    # スクレイパーの初期化（Enhanced mode）
    scraper = ResearchMapIntegratedScraper(mode="enhanced")

    comprehensive_data = {
        'researcher_url': researcher_url,
        'basic_info': {},
        'detailed_info': {},
        'research_keywords': [],
        'research_areas': [],
        'all_affiliations': [],
        'education': [],
        'research_projects': {
            'enhanced_mode': [],
            'basic_mode': []
        },
        'summary': {}
    }

    try:
        logger.info(f"研究者の包括的データ取得開始: {researcher_url}")

        # 1. 研究者の基本情報を取得（検索結果ページから）
        logger.info("=== 1. 研究者の基本情報を取得 ===")
        basic_info = get_researcher_basic_info(scraper, researcher_url)
        comprehensive_data['basic_info'] = basic_info
        logger.info(f"基本情報取得完了: {basic_info.get('name', 'Unknown')}")

        # 2. 研究者の詳細情報を取得
        logger.info("=== 2. 研究者の詳細情報を取得 ===")
        detailed_info = scraper.get_researcher_detailed_info(researcher_url)
        comprehensive_data['detailed_info'] = detailed_info
        logger.info(f"詳細情報取得完了: ORCID={detailed_info.get('orcid_id', 'N/A')}")

        # 3. 研究キーワードを取得
        logger.info("=== 3. 研究キーワードを取得 ===")
        keywords = scraper.get_researcher_keywords(researcher_url)
        comprehensive_data['research_keywords'] = keywords
        logger.info(f"研究キーワード取得完了: {len(keywords)}件")

        # 4. 研究分野を取得
        logger.info("=== 4. 研究分野を取得 ===")
        areas = scraper.get_researcher_areas(researcher_url)
        comprehensive_data['research_areas'] = areas
        logger.info(f"研究分野取得完了: {len(areas)}件")

        # 5. すべての所属先を取得
        logger.info("=== 5. すべての所属先を取得 ===")
        affiliations = scraper.get_researcher_affiliations(researcher_url)
        comprehensive_data['all_affiliations'] = affiliations
        logger.info(f"所属先取得完了: {len(affiliations)}件")

        # 6. 学歴を取得
        logger.info("=== 6. 学歴を取得 ===")
        education = scraper.get_researcher_education(researcher_url)
        comprehensive_data['education'] = education
        logger.info(f"学歴取得完了: {len(education)}件")

        # 7. Enhanced modeで研究課題を取得
        logger.info("=== 7. Enhanced modeで研究課題を取得 ===")
        enhanced_projects = scraper.get_research_projects_enhanced(researcher_url)
        comprehensive_data['research_projects']['enhanced_mode'] = enhanced_projects
        logger.info(f"Enhanced mode研究課題取得完了: {len(enhanced_projects)}件")

        # 8. Basic modeで研究課題を取得
        logger.info("=== 8. Basic modeで研究課題を取得 ===")
        basic_projects = scraper.get_research_projects_basic(researcher_url)
        comprehensive_data['research_projects']['basic_mode'] = basic_projects
        logger.info(f"Basic mode研究課題取得完了: {len(basic_projects)}件")

        # 9. サマリー情報を生成
        logger.info("=== 9. サマリー情報を生成 ===")
        summary = generate_summary(comprehensive_data)
        comprehensive_data['summary'] = summary
        logger.info(f"サマリー生成完了: {summary}")

        logger.info("=== 包括的データ取得完了 ===")
        return comprehensive_data

    except Exception as e:
        logger.error(f"包括的データ取得中にエラーが発生しました: {e}")
        return comprehensive_data

def get_researcher_basic_info(scraper: ResearchMapIntegratedScraper, researcher_url: str) -> Dict[str, Any]:
    """
    研究者の基本情報を取得（検索結果ページから）

    Args:
        scraper: スクレイパーインスタンス
        researcher_url (str): 研究者のURL

    Returns:
        Dict[str, Any]: 研究者の基本情報
    """
    try:
        # 研究者IDを抽出
        researcher_id = researcher_url.split('/')[-1]

        # 検索URLを構築（研究者名で検索）
        search_url = f"https://researchmap.jp/search?q={researcher_id}&lang=ja"

        response = scraper.session.get(search_url)
        response.raise_for_status()

        # 検索結果から研究者情報を抽出
        researchers = scraper.extract_researchers_from_page(response.content)

        # 該当する研究者を探す
        for researcher in researchers:
            if researcher.get('researcher_url') == researcher_url:
                return researcher

        # 見つからない場合は空の辞書を返す
        return {}

    except Exception as e:
        logger.error(f"基本情報取得エラー: {e}")
        return {}

def generate_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    データのサマリー情報を生成

    Args:
        data (Dict[str, Any]): 包括的データ

    Returns:
        Dict[str, Any]: サマリー情報
    """
    summary = {}

    # 基本情報のサマリー
    basic_info = data.get('basic_info', {})
    summary['researcher_name'] = basic_info.get('name', 'Unknown')
    summary['researcher_id'] = basic_info.get('researcher_id', 'Unknown')
    summary['affiliation'] = basic_info.get('affiliation', 'Unknown')
    summary['position'] = basic_info.get('position', 'Unknown')

    # 詳細情報のサマリー
    detailed_info = data.get('detailed_info', {})
    summary['orcid_id'] = detailed_info.get('orcid_id', 'N/A')
    summary['researcher_id'] = detailed_info.get('researcher_id', 'N/A')
    summary['research_keywords_count'] = len(data.get('research_keywords', []))
    summary['research_areas_count'] = len(data.get('research_areas', []))
    summary['affiliations_count'] = len(data.get('all_affiliations', []))
    summary['education_count'] = len(data.get('education', []))

    # 研究課題のサマリー
    enhanced_projects = data.get('research_projects', {}).get('enhanced_mode', [])
    basic_projects = data.get('research_projects', {}).get('basic_mode', [])

    summary['total_projects_enhanced'] = len(enhanced_projects)
    summary['total_projects_basic'] = len(basic_projects)

    # 競争的研究課題の統計
    competitive_enhanced = [p for p in enhanced_projects if p.get('is_competitive', False)]
    competitive_basic = [p for p in basic_projects if p.get('is_competitive', False)]

    summary['competitive_projects_enhanced'] = len(competitive_enhanced)
    summary['competitive_projects_basic'] = len(competitive_basic)

    # 助成金機関の統計
    institutions = {}
    for project in enhanced_projects:
        institution = project.get('institution', 'Unknown')
        if institution in institutions:
            institutions[institution] += 1
        else:
            institutions[institution] = 1

    summary['funding_institutions'] = institutions
    summary['unique_institutions_count'] = len(institutions)

    # 研究期間の統計
    periods = [p.get('period', 'Unknown') for p in enhanced_projects if p.get('period')]
    summary['research_periods'] = list(set(periods))

    return summary

def save_comprehensive_data(data: Dict[str, Any], researcher_id: str = None) -> str:
    """
    包括的データをJSONファイルに保存

    Args:
        data (Dict[str, Any]): 包括的データ
        researcher_id (str): 研究者ID

    Returns:
        str: 保存されたファイル名
    """
    if not researcher_id:
        researcher_id = data.get('basic_info', {}).get('researcher_id', 'unknown')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comprehensive_researcher_data_{researcher_id}_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"包括的データを保存しました: {filename}")
    return filename

def main():
    """メイン関数"""

    # テスト用研究者URL
    researcher_url = "https://researchmap.jp/hidekanematsu"

    logger.info("一人の研究者の包括的データ取得を開始")

    # 包括的データを取得
    comprehensive_data = get_comprehensive_researcher_data(researcher_url)

    # データを保存
    filename = save_comprehensive_data(comprehensive_data)

    # サマリーを表示
    summary = comprehensive_data.get('summary', {})
    logger.info(f"\n=== 取得結果サマリー ===")
    logger.info(f"研究者名: {summary.get('name', 'Unknown')}")
    logger.info(f"所属: {summary.get('affiliation', 'Unknown')}")
    logger.info(f"研究キーワード数: {summary.get('research_keywords_count', 0)}")
    logger.info(f"研究分野数: {summary.get('research_areas_count', 0)}")
    logger.info(f"所属先数: {summary.get('affiliations_count', 0)}")
    logger.info(f"学歴数: {summary.get('education_count', 0)}")
    logger.info(f"総研究課題数 (Enhanced): {summary.get('total_projects_enhanced', 0)}")
    logger.info(f"総研究課題数 (Basic): {summary.get('total_projects_basic', 0)}")
    logger.info(f"競争的研究課題数 (Enhanced): {summary.get('competitive_projects_enhanced', 0)}")
    logger.info(f"競争的研究課題数 (Basic): {summary.get('competitive_projects_basic', 0)}")
    logger.info(f"助成金機関数: {summary.get('unique_institutions_count', 0)}")

    logger.info(f"\n詳細データは {filename} に保存されました")
    logger.info("包括的データ取得完了")

if __name__ == "__main__":
    main()
