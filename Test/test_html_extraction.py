#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTMLファイルから研究課題を抽出するテストスクリプト
"""

import sys
import os
import json
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from researchmap_integrated_scraper import ResearchMapIntegratedScraper

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_html_extraction():
    """HTMLファイルから研究課題を抽出するテスト"""

    # スクレイパーの初期化
    scraper = ResearchMapIntegratedScraper(mode="enhanced")

    # テスト用HTMLファイルのパス
    html_file_path = Path("../samples/兼松 秀行 (Hideyuki Kanematsu) - 共同研究・競争的資金等の研究課題 - researchmap.html")

    if not html_file_path.exists():
        logger.error(f"HTMLファイルが見つかりません: {html_file_path}")
        return

    try:
        # HTMLファイルを読み込み
        logger.info(f"HTMLファイルを読み込み中: {html_file_path}")
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        logger.info(f"HTMLファイル読み込み完了: {len(html_content)} 文字")

        # 研究課題を抽出
        logger.info("研究課題の抽出を開始")
        projects = scraper.extract_research_projects_from_html(html_content)

        # 結果を表示
        logger.info(f"抽出された研究課題数: {len(projects)}")

        competitive_projects = [p for p in projects if p.get('is_competitive', False)]
        logger.info(f"競争的研究課題数: {len(competitive_projects)}")

        # 詳細結果を表示
        for i, project in enumerate(projects, 1):
            logger.info(f"\n研究課題 {i}:")
            logger.info(f"  タイトル: {project.get('title', 'N/A')}")
            logger.info(f"  URL: {project.get('project_url', 'N/A')}")
            logger.info(f"  ID: {project.get('project_id', 'N/A')}")
            logger.info(f"  機関: {project.get('institution', 'N/A')}")
            logger.info(f"  事業: {project.get('project_type', 'N/A')}")
            logger.info(f"  期間: {project.get('period', 'N/A')}")
            logger.info(f"  研究者: {project.get('researchers', 'N/A')}")
            logger.info(f"  競争的資金: {project.get('is_competitive', False)}")

        # 結果をJSONファイルに保存
        output_file = "test_html_extraction_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_projects': len(projects),
                'competitive_projects': len(competitive_projects),
                'projects': projects
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"結果を保存しました: {output_file}")

        return projects

    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {e}")
        return None

if __name__ == "__main__":
    test_html_extraction()
