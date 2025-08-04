#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Research Map Integrated Scraper

Research Mapから研究者情報と競争的研究課題を取得する統合スクレイパー
複数のスクレイピングモード（HTML、Enhanced）をサポート
"""

import requests
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Union
import logging
import re
from urllib.parse import urljoin, urlparse
import random
import argparse
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('researchmap_integrated_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ResearchMapIntegratedScraper:
    """
    Research Mapから研究者情報と競争的研究課題を取得する統合クラス
    複数のスクレイピングモードをサポート
    """

    def __init__(self, mode: str = "enhanced"):
        """
        Research Map Integrated Scraperの初期化

        Args:
            mode (str): スクレイピングモード ("basic", "enhanced", "html")
        """
        self.mode = mode
        self.base_url = "https://researchmap.jp"
        self.session = requests.Session()

        # ヘッダー設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        logger.info(f"ResearchMap Integrated Scraper initialized in {mode} mode")

    def get_total_pages(self, search_url: str) -> int:
        """
        検索結果の総ページ数を取得

        Args:
            search_url (str): 検索URL

        Returns:
            int: 総ページ数
        """
        try:
            logger.info(f"総ページ数を取得中: {search_url}")
            response = self.session.get(search_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # 総件数を取得
            total_count_elements = soup.find_all(string=lambda text: text and '総件数' in text)
            if total_count_elements:
                for element in total_count_elements:
                    match = re.search(r'総件数\s*(\d+)', element)
                    if match:
                        total_count = int(match.group(1))
                        total_pages = (total_count + 59) // 60  # 1ページあたり60件
                        logger.info(f"総件数: {total_count}, 総ページ数: {total_pages}")
                        return total_pages

            # ページネーションから取得
            pagination = soup.find('ul', class_='pagination')
            if pagination:
                page_links = pagination.find_all('a')
                if page_links:
                    page_numbers = []
                    for link in page_links:
                        text = link.get_text().strip()
                        if text.isdigit():
                            page_numbers.append(int(text))
                    if page_numbers:
                        max_page = max(page_numbers)
                        logger.info(f"ページネーションから総ページ数: {max_page}")
                        return max_page

            logger.warning("ページ数が取得できませんでした。デフォルト値を使用します。")
            return 1

        except Exception as e:
            logger.error(f"ページ数取得エラー: {e}")
            return 1

    def extract_researchers_from_page(self, html_content: str) -> List[Dict[str, Any]]:
        """
        ページから研究者情報を抽出

        Args:
            html_content (str): HTMLコンテンツ

        Returns:
            List[Dict[str, Any]]: 研究者情報のリスト
        """
        researchers = []
        soup = BeautifulSoup(html_content, 'html.parser')

        researcher_items = soup.find_all('li')

        for item in researcher_items:
            try:
                card_outer = item.find('div', class_='rm-cv-card-outer')
                if not card_outer:
                    continue

                researcher_info = {}

                # 名前を取得
                name_element = card_outer.find('div', class_='rm-cv-card-name')
                if name_element:
                    name_link = name_element.find('a')
                    if name_link:
                        researcher_info['name'] = name_link.get_text().strip()
                        researcher_url = name_link['href']
                        if not researcher_url.startswith('http'):
                            researcher_url = urljoin(self.base_url, researcher_url)
                        researcher_info['researcher_url'] = researcher_url

                        # 研究者IDを抽出
                        match = re.search(r'/([^/]+)$', researcher_url)
                        if match:
                            researcher_info['researcher_id'] = match.group(1)

                # 英語名を取得
                english_name_element = card_outer.find('div', class_='rm-cv-card-name-en')
                if english_name_element:
                    researcher_info['english_name'] = english_name_element.get_text().strip()

                # 所属を取得
                affiliation_element = card_outer.find('div', class_='rm-cv-card-name-affiliation')
                if affiliation_element:
                    researcher_info['affiliation'] = affiliation_element.get_text().strip()

                # 職名を取得
                position_element = card_outer.find('div', class_='rm-cv-card-name-section')
                if position_element:
                    researcher_info['position'] = position_element.get_text().strip()

                # カナ名を取得
                kana_element = card_outer.find('div', class_='rm-cv-card-kana')
                if kana_element:
                    researcher_info['kana_name'] = kana_element.get_text().strip()

                if researcher_info and researcher_info.get('name'):
                    researchers.append(researcher_info)

            except Exception as e:
                logger.error(f"研究者情報抽出エラー: {e}")
                continue

        logger.info(f"{len(researchers)}人の研究者情報を抽出しました")
        return researchers

    def get_researchers_from_all_pages(self, base_search_url: str) -> List[Dict[str, Any]]:
        """
        全ページから研究者情報を取得

        Args:
            base_search_url (str): 基本検索URL

        Returns:
            List[Dict[str, Any]]: 全研究者の情報
        """
        all_researchers = []
        total_pages = self.get_total_pages(base_search_url)

        logger.info(f"全{total_pages}ページから研究者情報を取得開始")

        for page in range(1, total_pages + 1):
            try:
                if page == 1:
                    page_url = base_search_url
                else:
                    start_index = (page - 1) * 60 + 1
                    page_url = f"{base_search_url}&start={start_index}"

                logger.info(f"ページ {page}/{total_pages} を処理中: {page_url}")

                response = self.session.get(page_url)
                response.raise_for_status()

                page_researchers = self.extract_researchers_from_page(response.content)
                all_researchers.extend(page_researchers)

                logger.info(f"ページ {page} で {len(page_researchers)} 人の研究者を取得")

                time.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.error(f"ページ {page} の処理エラー: {e}")
                continue

        logger.info(f"全ページ処理完了。総計 {len(all_researchers)} 人の研究者を取得")
        return all_researchers

    def get_researcher_detailed_info(self, researcher_url: str) -> Dict[str, Any]:
        """
        研究者の詳細情報を取得（Enhanced mode用）

        Args:
            researcher_url (str): 研究者のURL

        Returns:
            Dict[str, Any]: 研究者の詳細情報
        """
        try:
            logger.info(f"研究者詳細情報を取得中: {researcher_url}")

            response = self.session.get(researcher_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            detailed_info = {}

            # ORCID iDを取得
            orcid_element = soup.find('dt', string='ORCID iD')
            if orcid_element:
                orcid_dd = orcid_element.find_next_sibling('dd')
                if orcid_dd:
                    orcid_link = orcid_dd.find('a')
                    if orcid_link:
                        detailed_info['orcid_id'] = orcid_link.get_text().strip()

            # J-GLOBAL IDを取得
            jglobal_element = soup.find('dt', string='J-GLOBAL ID')
            if jglobal_element:
                jglobal_dd = jglobal_element.find_next_sibling('dd')
                if jglobal_dd:
                    jglobal_link = jglobal_dd.find('a')
                    if jglobal_link:
                        detailed_info['jglobal_id'] = jglobal_link.get_text().strip()

            # researchmap会員IDを取得
            member_id_element = soup.find('dt', string='researchmap会員ID')
            if member_id_element:
                member_id_dd = member_id_element.find_next_sibling('dd')
                if member_id_dd:
                    detailed_info['researchmap_member_id'] = member_id_dd.get_text().strip()

            # 研究キーワードを取得
            keywords = []
            keywords_section = soup.find('h2', string='研究キーワード')
            if keywords_section:
                keywords_container = keywords_section.find_next('div', class_='row')
                if keywords_container:
                    keyword_elements = keywords_container.find_all('span', class_='label')
                    keywords = [kw.get_text().strip() for kw in keyword_elements]
            detailed_info['research_keywords'] = keywords

            # 研究分野を取得
            research_areas = []
            areas_section = soup.find('h2', string='研究分野')
            if areas_section:
                areas_container = areas_section.find_next('div', class_='row')
                if areas_container:
                    area_elements = areas_container.find_all('span', class_='label')
                    research_areas = [area.get_text().strip() for area in area_elements]
            detailed_info['research_areas'] = research_areas

            # 所属情報を詳細取得
            affiliations = []
            affiliation_section = soup.find('h2', string='所属')
            if affiliation_section:
                affiliation_container = affiliation_section.find_next('div', class_='row')
                if affiliation_container:
                    affiliation_items = affiliation_container.find_all('div', class_='col-xs-12')
                    for item in affiliation_items:
                        affiliation_text = item.get_text().strip()
                        if affiliation_text:
                            affiliations.append(affiliation_text)
            detailed_info['all_affiliations'] = affiliations

            logger.info(f"詳細情報取得完了: ORCID={detailed_info.get('orcid_id', 'N/A')}, "
                       f"キーワード数={len(keywords)}, 研究分野数={len(research_areas)}")

            return detailed_info

        except Exception as e:
            logger.error(f"研究者詳細情報取得エラー: {e}")
            return {}

    def get_research_projects_basic(self, researcher_url: str) -> List[Dict[str, Any]]:
        """
        研究者の競争的研究課題を取得（Basic mode用）

        Args:
            researcher_url (str): 研究者のURL

        Returns:
            List[Dict[str, Any]]: 研究課題のリスト
        """
        try:
            logger.info(f"研究課題を取得中: {researcher_url}")

            response = self.session.get(researcher_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            projects = []

            all_links = soup.find_all('a', href=True)
            research_project_links = [link for link in all_links if 'research_projects' in link['href'] and link['href'].endswith('/research_projects') == False]

            for link in research_project_links:
                try:
                    project_info = {}

                    project_title = link.get_text().strip()
                    if project_title and project_title != "もっとみる":
                        project_info['title'] = project_title

                        project_url = link['href']
                        if not project_url.startswith('http'):
                            project_url = urljoin(self.base_url, project_url)
                        project_info['project_url'] = project_url

                        match = re.search(r'/research_projects/(\d+)$', project_url)
                        if match:
                            project_info['project_id'] = match.group(1)

                        # 競争的資金の判定は詳細ページで行うため、ここでは一時的にFalseに設定
                        project_info['is_competitive'] = False

                        if project_info:
                            projects.append(project_info)

                except Exception as e:
                    logger.error(f"研究課題情報抽出エラー: {e}")
                    continue

            logger.info(f"{len(projects)}件の研究課題を取得しました")
            return projects

        except Exception as e:
            logger.error(f"研究課題取得エラー: {e}")
            return []

    def get_research_projects_enhanced(self, researcher_url: str) -> List[Dict[str, Any]]:
        """
        研究者の競争的研究課題を詳細情報付きで取得（Enhanced mode用）

        Args:
            researcher_url (str): 研究者のURL

        Returns:
            List[Dict[str, Any]]: 研究課題のリスト（詳細情報付き）
        """
        try:
            logger.info(f"研究課題詳細を取得中: {researcher_url}")

            all_projects = []
            page = 1
            start_index = 1

            while True:
                if page == 1:
                    projects_url = researcher_url + "/research_projects"
                else:
                    projects_url = f"{researcher_url}/research_projects?limit=20&start={start_index}"

                logger.info(f"研究課題ページ {page} を取得中: {projects_url}")

                response = self.session.get(projects_url)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                project_items = soup.find_all('li')

                page_projects = []
                for item in project_items:
                    try:
                        title_element = item.find('a', href=lambda x: x and 'research_projects' in x)
                        if not title_element or title_element.get_text().strip() == "もっとみる":
                            continue

                        project_info = {}
                        project_title = title_element.get_text().strip()
                        project_info['title'] = project_title

                        project_url = title_element['href']
                        if not project_url.startswith('http'):
                            project_url = urljoin(self.base_url, project_url)
                        project_info['project_url'] = project_url

                        match = re.search(r'/research_projects/(\d+)$', project_url)
                        if match:
                            project_info['project_id'] = match.group(1)

                        project_details = self.get_project_details(project_url)
                        project_info.update(project_details)

                        # 競争的資金かどうかの判定（HTML構成要素ベース）
                        project_info['is_competitive'] = self.is_competitive_funding_by_html_structure(
                            funding_system=project_info.get('funding_system', ''),
                            institution=project_info.get('institution'),
                            project_type=project_info.get('project_type')
                        )

                        page_projects.append(project_info)

                    except Exception as e:
                        logger.error(f"研究課題情報抽出エラー: {e}")
                        continue

                all_projects.extend(page_projects)

                next_link = soup.find('a', string='もっとみる')
                if not next_link or len(page_projects) < 20:
                    break

                page += 1
                start_index = (page - 1) * 20 + 1

                time.sleep(random.uniform(1, 2))

            logger.info(f"{len(all_projects)}件の研究課題を取得しました")
            return all_projects

        except Exception as e:
            logger.error(f"研究課題取得エラー: {e}")
            return []

    def get_project_details(self, project_url: str) -> Dict[str, Any]:
        """
        研究課題の詳細情報を取得（改善版）

        Args:
            project_url (str): 研究課題の詳細ページURL

        Returns:
            Dict[str, Any]: 研究課題の詳細情報
        """
        try:
            response = self.session.get(project_url)
            if response.status_code != 200:
                return {}

            soup = BeautifulSoup(response.content, 'html.parser')

            details = {}

            # 1. 研究課題の説明を取得
            description_element = soup.find('div', class_='research-project-description')
            if description_element:
                details['description'] = description_element.get_text().strip()

            # 2. より包括的な情報抽出
            project_title_element = soup.find('h1') or soup.find('h2') or soup.find('h3')
            if project_title_element:
                # タイトル要素の次の要素から情報を抽出
                next_element = project_title_element.find_next_sibling()
                if next_element:
                    text_content = next_element.get_text().strip()

                    # 2.1 資金システム情報の取得（拡張版）
                    funding_system = self.extract_funding_system(text_content)
                    if funding_system:
                        details['funding_system'] = funding_system

                        # 助成金システムの詳細解析
                        funding_details = self.analyze_funding_system(funding_system)
                        details.update(funding_details)

                    # 2.2 期間情報の取得（拡張版）
                    period = self.extract_period(text_content)
                    if period:
                        details['period'] = period

                    # 2.3 研究者情報の取得（拡張版）
                    researchers = self.extract_researchers(text_content)
                    if researchers:
                        details['researchers'] = researchers

                    # 2.4 予算情報の取得
                    budget = self.extract_budget(text_content)
                    if budget:
                        details['budget'] = budget

                    # 2.5 研究種目・カテゴリの取得
                    research_category = self.extract_research_category(text_content)
                    if research_category:
                        details['research_category'] = research_category

            # 3. ページ全体から追加情報を抽出
            full_text = soup.get_text()

            # 3.1 キーワードの抽出
            keywords = self.extract_keywords(full_text)
            if keywords:
                details['keywords'] = keywords

            # 3.2 研究機関・組織の抽出
            organizations = self.extract_organizations(full_text)
            if organizations:
                details['organizations'] = organizations

            return details

        except Exception as e:
            logger.error(f"研究課題詳細取得エラー: {e}")
            return {}

    def extract_funding_system(self, text: str) -> str:
        """
        資金システム情報を抽出（拡張版）
        """
        # 既存のパターン
        funding_patterns = [
            r'(日本学術振興会\s+科学研究費補助金[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(JST[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(文部科学省[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(厚生労働省[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(経済産業省[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(基盤研究[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(挑戦的研究[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(新学術領域[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(特別研究員[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(若手研究[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(萌芽研究[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'(特別推進研究[^,]*?)(?:\s+\d{4}年|\s*$)'
        ]

        # 新しいパターンを追加
        extended_patterns = [
            r'([^,]*?研究費[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'([^,]*?助成金[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'([^,]*?補助金[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'([^,]*?事業[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'([^,]*?プロジェクト[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'([^,]*?基金[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'([^,]*?財団[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'([^,]*?協会[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'([^,]*?機構[^,]*?)(?:\s+\d{4}年|\s*$)',
            r'([^,]*?センター[^,]*?)(?:\s+\d{4}年|\s*$)'
        ]

        all_patterns = funding_patterns + extended_patterns

        for pattern in all_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return ""

    def extract_period(self, text: str) -> str:
        """
        期間情報を抽出（拡張版）
        """
        # 既存のパターン
        period_patterns = [
            r'(\d{4}年\d{1,2}月\s*-\s*\d{4}年\d{1,2}月)',
            r'(\d{4}年\d{1,2}月\s*～\s*\d{4}年\d{1,2}月)',
            r'(\d{4}年\d{1,2}月\s*から\s*\d{4}年\d{1,2}月)',
            r'(\d{4}\.\d{1,2}\s*-\s*\d{4}\.\d{1,2})',
            r'(\d{4}-\d{4})',
            r'(FY\d{4}-FY\d{4})',
            r'(平成\d{1,2}年度\s*-\s*平成\d{1,2}年度)',
            r'(令和\d{1,2}年度\s*-\s*令和\d{1,2}年度)',
            r'(\d{4}年度\s*-\s*\d{4}年度)',
            r'(\d{4}年度から\d{4}年度)'
        ]

        for pattern in period_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return ""

    def extract_researchers(self, text: str) -> str:
        """
        研究者情報を抽出（拡張版）
        """
        # 複数のパターンで研究者情報を抽出
        researcher_patterns = [
            r'研究代表者[：:]\s*([^,\n]+)',
            r'研究責任者[：:]\s*([^,\n]+)',
            r'代表者[：:]\s*([^,\n]+)',
            r'責任者[：:]\s*([^,\n]+)',
            r'([^,\n]+(?:教授|准教授|助教|研究員|博士|Ph\.D)[^,\n]*)',
            r'([^,\n]+(?:,\s*[^,\n]+)*?)(?:\s*$)'
        ]

        for pattern in researcher_patterns:
            match = re.search(pattern, text)
            if match:
                researchers_text = match.group(1).strip()
                # 年号や数字のみの場合は除外
                if researchers_text and not re.search(r'\d{4}年', researchers_text) and len(researchers_text) > 2:
                    return researchers_text

        return ""

    def extract_budget(self, text: str) -> str:
        """
        予算情報を抽出
        """
        budget_patterns = [
            r'予算[：:]\s*([^,\n]+)',
            r'助成金額[：:]\s*([^,\n]+)',
            r'補助金額[：:]\s*([^,\n]+)',
            r'([0-9,]+万円)',
            r'([0-9,]+千円)',
            r'([0-9,]+円)',
            r'([0-9,]+ドル)',
            r'([0-9,]+ユーロ)'
        ]

        for pattern in budget_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return ""

    def extract_research_category(self, text: str) -> str:
        """
        研究種目・カテゴリを抽出
        """
        category_patterns = [
            r'研究種目[：:]\s*([^,\n]+)',
            r'カテゴリ[：:]\s*([^,\n]+)',
            r'分野[：:]\s*([^,\n]+)',
            r'領域[：:]\s*([^,\n]+)',
            r'(基盤研究[ABC])',
            r'(若手研究[ABC])',
            r'(萌芽研究[ABC])',
            r'(挑戦的萌芽研究)',
            r'(特別推進研究)',
            r'(新学術領域研究)'
        ]

        for pattern in category_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return ""

    def extract_keywords(self, text: str) -> List[str]:
        """
        キーワードを抽出
        """
        keywords = []

        # キーワード関連のパターン
        keyword_patterns = [
            r'キーワード[：:]\s*([^,\n]+)',
            r'研究キーワード[：:]\s*([^,\n]+)',
            r'技術キーワード[：:]\s*([^,\n]+)'
        ]

        for pattern in keyword_patterns:
            match = re.search(pattern, text)
            if match:
                keywords_text = match.group(1).strip()
                # カンマ区切りで分割
                keywords.extend([kw.strip() for kw in keywords_text.split(',') if kw.strip()])

        return keywords

    def extract_organizations(self, text: str) -> List[str]:
        """
        研究機関・組織を抽出
        """
        organizations = []

        # 組織関連のパターン
        org_patterns = [
            r'研究機関[：:]\s*([^,\n]+)',
            r'実施機関[：:]\s*([^,\n]+)',
            r'協力機関[：:]\s*([^,\n]+)',
            r'連携機関[：:]\s*([^,\n]+)',
            r'([^,\n]*?大学[^,\n]*)',
            r'([^,\n]*?研究所[^,\n]*)',
            r'([^,\n]*?センター[^,\n]*)',
            r'([^,\n]*?財団[^,\n]*)',
            r'([^,\n]*?協会[^,\n]*)'
        ]

        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match.strip() and match.strip() not in organizations:
                    organizations.append(match.strip())

        return organizations

    def extract_research_projects_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """
        HTMLパターンに基づいて研究課題情報を抽出（改善版）

        Args:
            html_content (str): HTMLコンテンツ

        Returns:
            List[Dict[str, Any]]: 研究課題のリスト
        """
        projects = []
        soup = BeautifulSoup(html_content, 'html.parser')

        # 研究課題リストの取得 - 実際のHTML構造に合わせて修正
        research_items = soup.find_all('li', class_=lambda x: x and 'list-group-item' in x and 'rm-cv-disclosed' in x)

        logger.info(f"研究課題アイテム数: {len(research_items)}")

        for i, item in enumerate(research_items):
            try:
                logger.info(f"研究課題 {i+1} を処理中...")
                project_info = {}

                # 1. タイトルとURLの取得
                title_element = item.find('a', class_='rm-cv-list-title')
                if title_element:
                    project_info['title'] = title_element.get_text().strip()
                    project_url = title_element['href']
                    if not project_url.startswith('http'):
                        project_url = urljoin(self.base_url, project_url)
                    project_info['project_url'] = project_url

                    # プロジェクトIDの抽出
                    match = re.search(r'/research_projects/(\d+)$', project_url)
                    if match:
                        project_info['project_id'] = match.group(1)

                    logger.info(f"  タイトル: {project_info['title']}")
                    logger.info(f"  URL: {project_info['project_url']}")

                # 2. 助成金情報の取得（rm-cv-list-content内の2番目のdiv）
                content_div = item.find('div', class_='rm-cv-list-content')
                if content_div:
                    content_divs = content_div.find_all('div')
                    if len(content_divs) > 1:
                        # 2番目のdivが助成金情報（最初のdivはタイトル、3番目は研究者）
                        funding_div = content_divs[1]  # 2番目のdivが助成金情報
                        funding_text = funding_div.get_text().strip()
                        logger.info(f"  助成金情報: {funding_text}")

                        # 助成金情報と期間を分離
                        funding_parts = self.parse_funding_info(funding_text)
                        project_info.update(funding_parts)

                # 3. 研究者情報の取得
                author_div = content_div.find('div', class_='rm-cv-list-author') if content_div else None
                if author_div:
                    project_info['researchers'] = author_div.get_text().strip()
                    logger.info(f"  研究者: {project_info['researchers']}")

                # 4. 競争的資金かどうかの判定（HTML構成要素ベース）
                project_info['is_competitive'] = self.is_competitive_funding_by_html_structure(
                    funding_system=project_info.get('funding_system', ''),
                    institution=project_info.get('institution'),
                    project_type=project_info.get('project_type')
                )

                logger.info(f"  競争的資金: {project_info['is_competitive']}")

                if project_info.get('title'):
                    projects.append(project_info)
                    logger.info(f"  研究課題を追加: {project_info['title']}")
                else:
                    logger.warning(f"  タイトルが見つからないためスキップ")

            except Exception as e:
                logger.error(f"研究課題情報抽出エラー: {e}")
                continue

        logger.info(f"{len(projects)}件の研究課題を抽出しました")
        return projects

    def parse_funding_info(self, funding_text: str) -> Dict[str, Any]:
        """
        助成金情報テキストを解析して構造化データに変換

        Args:
            funding_text (str): 助成金情報のテキスト

        Returns:
            Dict[str, Any]: 構造化された助成金情報
        """
        result = {}

        logger.info(f"助成金情報解析開始: {funding_text}")

        # 期間パターンの抽出
        period_patterns = [
            r'(\d{4}年\d{1,2}月\s*-\s*\d{4}年\d{1,2}月)',
            r'(\d{4}年\d{1,2}月\s*～\s*\d{4}年\d{1,2}月)',
            r'(\d{4}年\d{1,2}月\s*から\s*\d{4}年\d{1,2}月)',
            r'(\d{4}\.\d{1,2}\s*-\s*\d{4}\.\d{1,2})',
            r'(\d{4}-\d{4})',
            r'(FY\d{4}-FY\d{4})',
            r'(平成\d{1,2}年度\s*-\s*平成\d{1,2}年度)',
            r'(令和\d{1,2}年度\s*-\s*令和\d{1,2}年度)',
            r'(\d{4}年度\s*-\s*\d{4}年度)',
            r'(\d{4}年度から\d{4}年度)',
            r'(\d{4}年\d{1,2}月\s*-\s*\d{4}年\d{1,2}月)',
            r'(\d{4}年\s*-\s*\d{4}年)'
        ]

        period = ""
        for pattern in period_patterns:
            match = re.search(pattern, funding_text)
            if match:
                period = match.group(1)
                break

        if period:
            result['period'] = period
            logger.info(f"  期間抽出: {period}")

        # 機関名と事業名の抽出
        # 実際のHTMLでは "日本学術振興会 科学研究費助成事業 基盤研究(C) 2023年4月 - 2026年3月" のような形式
        # 期間を除いた部分が助成金情報
        if period:
            funding_info = funding_text.replace(period, '').strip()
        else:
            funding_info = funding_text.strip()

        # 機関名と事業名を分離（最初のスペースで分割）
        if ' ' in funding_info:
            parts = funding_info.split(' ', 1)
            if len(parts) >= 2:
                institution = parts[0].strip()
                project_type = parts[1].strip()

                result['institution'] = institution
                result['project_type'] = project_type
                result['funding_system'] = funding_info

                logger.info(f"  機関名: {institution}")
                logger.info(f"  事業名: {project_type}")
                logger.info(f"  助成金システム: {funding_info}")
            else:
                result['funding_system'] = funding_info
                logger.info(f"  助成金システム: {funding_info}")
        else:
            result['funding_system'] = funding_info
            logger.info(f"  助成金システム: {funding_info}")

        return result

    def analyze_funding_system(self, funding_system: str) -> Dict[str, Any]:
        """
        助成金システム情報を詳細解析

        Args:
            funding_system (str): 助成金システム情報

        Returns:
            Dict[str, Any]: 詳細解析結果
        """
        result = {}

        # 機関名の抽出
        institutions = [
            '日本学術振興会', 'JST', '国立研究開発法人科学技術振興機構',
            'NEDO', '国立研究開発法人新エネルギー・産業技術総合開発機構',
            '独立行政法人新エネルギー・産業技術総合開発機構',
            '鉄鋼環境基金', '文部科学省', '厚生労働省', '経済産業省'
        ]

        for institution in institutions:
            if institution in funding_system:
                result['institution'] = institution
                break

        # 事業名の抽出
        project_types = [
            '科学研究費助成事業', '科学研究費', '科学研究費補助金',
            '基盤研究', '若手研究', '萌芽研究', '挑戦的研究',
            '特別推進研究', '新学術領域研究', '特別研究員',
            '地熱発電技術研究開発', '新エネルギーベンチャー技術革新事業',
            '環境研究'
        ]

        for project_type in project_types:
            if project_type in funding_system:
                result['project_type'] = project_type
                break

        # 研究種目の抽出
        research_categories = [
            '基盤研究(A)', '基盤研究(B)', '基盤研究(C)',
            '若手研究(A)', '若手研究(B)', '若手研究(C)',
            '萌芽研究', '挑戦的萌芽研究', '特別推進研究',
            '新学術領域研究', '特別研究員'
        ]

        for category in research_categories:
            if category in funding_system:
                result['research_category'] = category
                break

        return result

    def is_competitive_funding_by_html_structure(self, funding_system: str, institution: str = None, project_type: str = None) -> bool:
        """
        HTMLの構成要素に基づいて競争的資金かどうかを判定

        Args:
            funding_system (str): 資金システム情報
            institution (str): 機関名
            project_type (str): 事業タイプ

        Returns:
            bool: 競争的資金の場合True
        """
        logger.info(f"競争的資金判定開始 - 機関: {institution}, 事業: {project_type}, システム: {funding_system}")

        # 競争的資金と判定される機関名
        competitive_institutions = [
            '日本学術振興会',
            'JST',
            '国立研究開発法人科学技術振興機構',
            '文部科学省',
            '厚生労働省',
            '経済産業省',
            '国立研究開発法人新エネルギー・産業技術総合開発機構',
            'NEDO',
            '独立行政法人新エネルギー・産業技術総合開発機構'
        ]

        # 競争的資金と判定される事業タイプ
        competitive_project_types = [
            '科学研究費助成事業',
            '科学研究費',
            '科学研究費補助金',
            '基盤研究',
            '若手研究',
            '萌芽研究',
            '挑戦的研究',
            '特別推進研究',
            '新学術領域研究',
            '特別研究員',
            '挑戦的萌芽研究',
            '地熱発電技術研究開発',
            '新エネルギーベンチャー技術革新事業'
        ]

        # 機関名による判定
        if institution and institution in competitive_institutions:
            logger.info(f"  機関名による判定: True ({institution})")
            return True

        # 事業タイプによる判定
        if project_type:
            for competitive_type in competitive_project_types:
                if competitive_type in project_type:
                    logger.info(f"  事業タイプによる判定: True ({competitive_type} in {project_type})")
                    return True

        # 資金システム情報による判定（フォールバック）
        if funding_system:
            funding_lower = funding_system.lower()
            competitive_indicators = [
                '科研費', '科学研究費', '基盤研究', '若手研究', '萌芽研究',
                '挑戦的研究', '特別推進研究', '新学術領域研究', '特別研究員',
                '助成事業', '補助金', '挑戦的萌芽研究', '地熱発電技術研究開発',
                '新エネルギーベンチャー技術革新事業'
            ]
            for indicator in competitive_indicators:
                if indicator in funding_lower:
                    logger.info(f"  助成金システムによる判定: True ({indicator} in {funding_system})")
                    return True

        logger.info(f"  競争的資金ではないと判定")
        return False

    def scrape_all_researchers_and_projects(self, search_url: str = None,
                                          max_researchers: int = None) -> Dict[str, Any]:
        """
        全研究者とその競争的研究課題を取得

        Args:
            search_url (str): 検索URL
            max_researchers (int): 処理する最大研究者数（テスト用）

        Returns:
            Dict[str, Any]: 全データ
        """
        logger.info(f"研究者と競争的研究課題の取得を開始（モード: {self.mode}）")

        if not search_url:
            search_url = "https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE"

        all_researchers = self.get_researchers_from_all_pages(search_url)

        if max_researchers and max_researchers < len(all_researchers):
            all_researchers = all_researchers[:max_researchers]
            logger.info(f"テストモード: 最初の{max_researchers}人の研究者のみ処理します")

        researchers_with_projects = []
        total_competitive_projects = 0

        for i, researcher in enumerate(all_researchers, 1):
            try:
                logger.info(f"研究者 {i}/{len(all_researchers)} を処理中: {researcher.get('name', 'Unknown')}")

                researcher_url = researcher.get('researcher_url')
                if not researcher_url:
                    logger.warning(f"研究者 {researcher.get('name', 'Unknown')} のURLが見つかりません")
                    continue

                if self.mode == "enhanced":
                    detailed_info = self.get_researcher_detailed_info(researcher_url)
                    projects = self.get_research_projects_enhanced(researcher_url)
                else:
                    detailed_info = {}
                    projects = self.get_research_projects_basic(researcher_url)

                competitive_projects = [p for p in projects if p.get('is_competitive', False)]
                total_competitive_projects += len(competitive_projects)

                researcher_data = researcher.copy()
                researcher_data.update(detailed_info)
                researcher_data['all_projects'] = projects
                researcher_data['competitive_projects'] = competitive_projects
                researcher_data['competitive_project_count'] = len(competitive_projects)

                researchers_with_projects.append(researcher_data)

                logger.info(f"研究者 {researcher.get('name', 'Unknown')}: "
                          f"全{len(projects)}件、競争的{len(competitive_projects)}件 "
                          f"(累計: {total_competitive_projects}件)")

                time.sleep(random.uniform(2, 5))

            except Exception as e:
                logger.error(f"研究者 {researcher.get('name', 'Unknown')} の処理エラー: {e}")
                continue

        result = {
            'total_researchers': len(all_researchers),
            'processed_researchers': len(researchers_with_projects),
            'total_competitive_projects': total_competitive_projects,
            'researchers': researchers_with_projects,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mode': self.mode,
            'search_url': search_url
        }

        logger.info(f"取得完了: 研究者{result['processed_researchers']}人、"
                   f"競争的研究課題{result['total_competitive_projects']}件")

        return result

    def save_results(self, data: Dict[str, Any], output_file: str = None):
        """
        結果をJSONファイルに保存

        Args:
            data (Dict[str, Any]): 保存するデータ
            output_file (str): 出力ファイル名
        """
        if not output_file:
            output_file = f"researchmap_{self.mode}_results.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"結果を {output_file} に保存しました")
        except Exception as e:
            logger.error(f"ファイル保存エラー: {e}")

    def export_to_excel(self, data: Dict[str, Any], output_file: str = None):
        """
        結果をExcelファイルにエクスポート

        Args:
            data (Dict[str, Any]): エクスポートするデータ
            output_file (str): 出力ファイル名
        """
        if not output_file:
            output_file = f"researchmap_{self.mode}_results.xlsx"

        try:
            researchers_data = []
            for researcher in data['researchers']:
                base_info = {
                    'name': researcher.get('name', ''),
                    'english_name': researcher.get('english_name', ''),
                    'kana_name': researcher.get('kana_name', ''),
                    'affiliation': researcher.get('affiliation', ''),
                    'position': researcher.get('position', ''),
                    'researcher_id': researcher.get('researcher_id', ''),
                    'researcher_url': researcher.get('researcher_url', ''),
                    'competitive_project_count': researcher.get('competitive_project_count', 0)
                }

                if self.mode == "enhanced":
                    base_info.update({
                        'orcid_id': researcher.get('orcid_id', ''),
                        'jglobal_id': researcher.get('jglobal_id', ''),
                        'researchmap_member_id': researcher.get('researchmap_member_id', ''),
                        'research_keywords': '; '.join(researcher.get('research_keywords', [])),
                        'research_areas': '; '.join(researcher.get('research_areas', [])),
                        'all_affiliations': '; '.join(researcher.get('all_affiliations', []))
                    })

                if not researcher.get('competitive_projects'):
                    researchers_data.append(base_info)
                else:
                    for project in researcher['competitive_projects']:
                        row = base_info.copy()
                        row.update({
                            'project_title': project.get('title', ''),
                            'project_url': project.get('project_url', ''),
                            'project_id': project.get('project_id', ''),
                            'is_competitive': project.get('is_competitive', False)
                        })

                        if self.mode == "enhanced":
                            row.update({
                                'funding_system': project.get('funding_system', ''),
                                'period': project.get('period', ''),
                                'researchers': project.get('researchers', ''),
                                'description': project.get('description', ''),
                                'budget': project.get('budget', ''),
                                'research_category': project.get('research_category', ''),
                                'keywords': '; '.join(project.get('keywords', [])),
                                'organizations': '; '.join(project.get('organizations', []))
                            })

                        researchers_data.append(row)

            df = pd.DataFrame(researchers_data)

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='競争的研究課題', index=False)

                summary_data = {
                    '項目': [
                        '総研究者数',
                        '処理済み研究者数',
                        '競争的研究課題総数',
                        '競争的研究課題を持つ研究者数',
                        '取得日時',
                        'スクレイピングモード',
                        '検索URL'
                    ],
                    '値': [
                        data['total_researchers'],
                        data['processed_researchers'],
                        data['total_competitive_projects'],
                        len([r for r in data['researchers'] if r.get('competitive_project_count', 0) > 0]),
                        data['scraped_at'],
                        data['mode'],
                        data['search_url']
                    ]
                }

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='サマリー', index=False)

            logger.info(f"結果を {output_file} にエクスポートしました")

        except Exception as e:
            logger.error(f"Excelエクスポートエラー: {e}")

def main():
    """
    メイン実行関数
    """
    parser = argparse.ArgumentParser(description='Research Map統合スクレイパー')
    parser.add_argument('--mode', type=str, choices=['basic', 'enhanced', 'html'],
                       default='enhanced', help='スクレイピングモード')
    parser.add_argument('--search-url', type=str,
                       default='https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE',
                       help='検索URL')
    parser.add_argument('--test', type=int, help='テストモード: 指定した数の研究者のみ処理')
    parser.add_argument('--output-prefix', type=str, default='researchmap_integrated',
                       help='出力ファイルのプレフィックス')

    args = parser.parse_args()

    # スクレイパーを初期化
    scraper = ResearchMapIntegratedScraper(mode=args.mode)

    try:
        results = scraper.scrape_all_researchers_and_projects(
            search_url=args.search_url,
            max_researchers=args.test
        )

        # 結果を保存
        if args.test:
            output_prefix = f"{args.output_prefix}_{args.mode}_test_{args.test}"
        else:
            output_prefix = f"{args.output_prefix}_{args.mode}"

        scraper.save_results(results, f"{output_prefix}_results.json")
        scraper.export_to_excel(results, f"{output_prefix}_results.xlsx")

        logger.info("処理が完了しました")

    except Exception as e:
        logger.error(f"メイン処理エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
