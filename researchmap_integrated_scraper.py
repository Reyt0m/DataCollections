#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Research Map Integrated Scraper

Research Mapから研究者情報と競争的研究課題を取得する統合スクレイパー
包括的な研究者データ取得機能を含む
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
from dataclasses import dataclass
from enum import Enum

# =============================================================================
# 定数と設定
# =============================================================================

class ScrapingConfig:
    """スクレイピング設定"""
    BASE_URL = "https://researchmap.jp"
    ITEMS_PER_PAGE = 60
    REQUEST_DELAY_MIN = 1
    REQUEST_DELAY_MAX = 3
    TIMEOUT = 30

    # ヘッダー設定
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

class CompetitiveFundingPatterns:
    """競争的資金判定パターン"""
    COMPETITIVE_INSTITUTIONS = [
        '日本学術振興会', 'JST', '国立研究開発法人科学技術振興機構',
        'NEDO', '国立研究開発法人新エネルギー・産業技術総合開発機構',
        '独立行政法人新エネルギー・産業技術総合開発機構',
        '鉄鋼環境基金', '文部科学省', '厚生労働省', '経済産業省'
    ]

    COMPETITIVE_PROJECT_TYPES = [
        '科学研究費助成事業', '科学研究費', '科学研究費補助金',
        '基盤研究', '若手研究', '萌芽研究', '挑戦的研究',
        '特別推進研究', '新学術領域研究', '特別研究員',
        '挑戦的萌芽研究', '地熱発電技術研究開発',
        '新エネルギーベンチャー技術革新事業'
    ]

    COMPETITIVE_INDICATORS = [
        '科研費', '科学研究費', '基盤研究', '若手研究', '萌芽研究',
        '挑戦的研究', '特別推進研究', '新学術領域研究', '特別研究員',
        '助成事業', '補助金', '挑戦的萌芽研究', '地熱発電技術研究開発',
        '新エネルギーベンチャー技術革新事業'
    ]

# =============================================================================
# データクラス
# =============================================================================

@dataclass
class ResearcherInfo:
    """研究者情報データクラス"""
    name: str = ""
    english_name: str = ""
    kana_name: str = ""
    affiliation: str = ""
    position: str = ""
    researcher_id: str = ""
    researcher_url: str = ""
    orcid_id: str = ""
    jglobal_id: str = ""
    researchmap_member_id: str = ""
    research_keywords: List[str] = None
    research_areas: List[str] = None
    all_affiliations: List[str] = None

    def __post_init__(self):
        if self.research_keywords is None:
            self.research_keywords = []
        if self.research_areas is None:
            self.research_areas = []
        if self.all_affiliations is None:
            self.all_affiliations = []

@dataclass
class ProjectInfo:
    """研究課題情報データクラス"""
    title: str = ""
    project_url: str = ""
    project_id: str = ""
    is_competitive: bool = False
    funding_system: str = ""
    period: str = ""
    institution: str = ""
    project_type: str = ""
    researchers: str = ""
    description: str = ""
    budget: str = ""
    research_category: str = ""
    keywords: List[str] = None
    organizations: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.organizations is None:
            self.organizations = []

# =============================================================================
# ログ設定
# =============================================================================

def setup_logging():
    """ログ設定を初期化"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('researchmap_integrated_scraper.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# =============================================================================
# ユーティリティクラス
# =============================================================================

class URLHelper:
    """URL操作ヘルパークラス"""

    @staticmethod
    def extract_researcher_id(url: str) -> str:
        """研究者IDをURLから抽出"""
        return url.split('/')[-1]

    @staticmethod
    def build_search_url(researcher_id: str) -> str:
        """検索URLを構築"""
        return f"{ScrapingConfig.BASE_URL}/search?q={researcher_id}&lang=ja"

    @staticmethod
    def build_projects_url(researcher_url: str) -> str:
        """研究課題ページURLを構築"""
        return f"{researcher_url}/research_projects"

    @staticmethod
    def ensure_absolute_url(url: str, base_url: str = ScrapingConfig.BASE_URL) -> str:
        """絶対URLを保証"""
        if not url.startswith('http'):
            return urljoin(base_url, url)
        return url

class DataExtractor:
    """データ抽出ヘルパークラス"""

    @staticmethod
    def extract_funding_system(text: str) -> str:
        """資金システム情報を抽出"""
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
            r'(特別推進研究[^,]*?)(?:\s+\d{4}年|\s*$)',
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

        for pattern in funding_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return ""

    @staticmethod
    def extract_period(text: str) -> str:
        """期間情報を抽出"""
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

        for pattern in period_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return ""

    @staticmethod
    def extract_researchers(text: str) -> str:
        """研究者情報を抽出"""
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
                if researchers_text and not re.search(r'\d{4}年', researchers_text) and len(researchers_text) > 2:
                    return researchers_text
        return ""

    @staticmethod
    def extract_budget(text: str) -> str:
        """予算情報を抽出"""
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

    @staticmethod
    def extract_research_category(text: str) -> str:
        """研究種目・カテゴリを抽出"""
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

    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """キーワードを抽出"""
        keywords = []
        keyword_patterns = [
            r'キーワード[：:]\s*([^,\n]+)',
            r'研究キーワード[：:]\s*([^,\n]+)',
            r'技術キーワード[：:]\s*([^,\n]+)'
        ]

        for pattern in keyword_patterns:
            match = re.search(pattern, text)
            if match:
                keywords_text = match.group(1).strip()
                keywords.extend([kw.strip() for kw in keywords_text.split(',') if kw.strip()])
        return keywords

    @staticmethod
    def extract_organizations(text: str) -> List[str]:
        """研究機関・組織を抽出"""
        organizations = []
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

# =============================================================================
# メインスクレイパークラス
# =============================================================================

class ResearchMapIntegratedScraper:
    """
    Research Mapから研究者情報と競争的研究課題を取得する統合クラス
    包括的な研究者データ取得機能を含む
    """

    def __init__(self):
        """Research Map Integrated Scraperの初期化"""
        self.session = requests.Session()
        self.session.headers.update(ScrapingConfig.HEADERS)
        logger.info("ResearchMap Integrated Scraper initialized")

    def _make_request(self, url: str) -> requests.Response:
        """HTTPリクエストを実行（エラーハンドリング付き）"""
        try:
            response = self.session.get(url, timeout=ScrapingConfig.TIMEOUT)
            response.raise_for_status()
            time.sleep(random.uniform(ScrapingConfig.REQUEST_DELAY_MIN, ScrapingConfig.REQUEST_DELAY_MAX))
            return response
        except requests.RequestException as e:
            logger.error(f"リクエストエラー {url}: {e}")
            raise

    def get_total_pages(self, search_url: str) -> int:
        """検索結果の総ページ数を取得"""
        try:
            logger.info(f"総ページ数を取得中: {search_url}")
            response = self._make_request(search_url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # 総件数から計算
            total_count_elements = soup.find_all(string=lambda text: text and '総件数' in text)
            if total_count_elements:
                for element in total_count_elements:
                    match = re.search(r'総件数\s*(\d+)', element)
                    if match:
                        total_count = int(match.group(1))
                        total_pages = (total_count + ScrapingConfig.ITEMS_PER_PAGE - 1) // ScrapingConfig.ITEMS_PER_PAGE
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
        """ページから研究者情報を抽出"""
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
                        researcher_info['researcher_url'] = URLHelper.ensure_absolute_url(researcher_url)
                        researcher_info['researcher_id'] = URLHelper.extract_researcher_id(researcher_info['researcher_url'])

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
        """全ページから研究者情報を取得"""
        all_researchers = []
        total_pages = self.get_total_pages(base_search_url)

        logger.info(f"全{total_pages}ページから研究者情報を取得開始")

        for page in range(1, total_pages + 1):
            try:
                if page == 1:
                    page_url = base_search_url
                else:
                    start_index = (page - 1) * ScrapingConfig.ITEMS_PER_PAGE + 1
                    page_url = f"{base_search_url}&start={start_index}"

                logger.info(f"ページ {page}/{total_pages} を処理中: {page_url}")

                response = self._make_request(page_url)
                page_researchers = self.extract_researchers_from_page(response.content)
                all_researchers.extend(page_researchers)

                logger.info(f"ページ {page} で {len(page_researchers)} 人の研究者を取得")

            except Exception as e:
                logger.error(f"ページ {page} の処理エラー: {e}")
                continue

        logger.info(f"全ページ処理完了。総計 {len(all_researchers)} 人の研究者を取得")
        return all_researchers

    def get_researcher_detailed_info(self, researcher_url: str) -> Dict[str, Any]:
        """研究者の詳細情報を取得"""
        try:
            logger.info(f"研究者詳細情報を取得中: {researcher_url}")
            response = self._make_request(researcher_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            detailed_info = {}

            # ORCID iDを取得
            detailed_info['orcid_id'] = self._extract_orcid_id(soup)

            # J-GLOBAL IDを取得
            detailed_info['jglobal_id'] = self._extract_jglobal_id(soup)

            # researchmap会員IDを取得
            detailed_info['researchmap_member_id'] = self._extract_member_id(soup)

            # 研究キーワードを取得
            detailed_info['research_keywords'] = self._extract_research_keywords(soup)

            # 研究分野を取得
            detailed_info['research_areas'] = self._extract_research_areas(soup)

            # 所属情報を詳細取得
            detailed_info['all_affiliations'] = self._extract_affiliations(soup)

            logger.info(f"詳細情報取得完了: ORCID={detailed_info.get('orcid_id', 'N/A')}, "
                       f"キーワード数={len(detailed_info['research_keywords'])}, "
                       f"研究分野数={len(detailed_info['research_areas'])}")

            return detailed_info

        except Exception as e:
            logger.error(f"研究者詳細情報取得エラー: {e}")
            return {}

    def _extract_orcid_id(self, soup: BeautifulSoup) -> str:
        """ORCID iDを抽出"""
        orcid_element = soup.find('dt', string='ORCID iD')
        if orcid_element:
            orcid_dd = orcid_element.find_next_sibling('dd')
            if orcid_dd:
                orcid_link = orcid_dd.find('a')
                if orcid_link:
                    return orcid_link.get_text().strip()
        return ""

    def _extract_jglobal_id(self, soup: BeautifulSoup) -> str:
        """J-GLOBAL IDを抽出"""
        jglobal_element = soup.find('dt', string='J-GLOBAL ID')
        if jglobal_element:
            jglobal_dd = jglobal_element.find_next_sibling('dd')
            if jglobal_dd:
                jglobal_link = jglobal_dd.find('a')
                if jglobal_link:
                    return jglobal_link.get_text().strip()
        return ""

    def _extract_member_id(self, soup: BeautifulSoup) -> str:
        """researchmap会員IDを抽出"""
        member_id_element = soup.find('dt', string='researchmap会員ID')
        if member_id_element:
            member_id_dd = member_id_element.find_next_sibling('dd')
            if member_id_dd:
                return member_id_dd.get_text().strip()
        return ""

    def _extract_research_keywords(self, soup: BeautifulSoup) -> List[str]:
        """研究キーワードを抽出（改善版）"""
        keywords = []

        # 方法1: 研究キーワードセクションから抽出
        keywords_section = soup.find('h2', string='研究キーワード')
        if keywords_section:
            # セクション内のul要素を探す
            keywords_list = keywords_section.find_next('ul', class_='rm-cv-research-interests')
            if keywords_list:
                keyword_links = keywords_list.find_all('a', class_='rm-cv-list-title')
                keywords = [link.get_text().strip() for link in keyword_links]

        # 方法2: パネルボディから直接抽出
        if not keywords:
            keywords_panel = soup.find('div', {'id': 'research_interests'})
            if keywords_panel:
                panel_body = keywords_panel.find_next('div', class_='research_interests-body')
                if panel_body:
                    keyword_links = panel_body.find_all('a', class_='rm-cv-list-title')
                    keywords = [link.get_text().strip() for link in keyword_links]

        return keywords

    def _extract_research_areas(self, soup: BeautifulSoup) -> List[str]:
        """研究分野を抽出（改善版）"""
        areas = []

        # 方法1: 研究分野セクションから抽出
        areas_section = soup.find('h2', string='研究分野')
        if areas_section:
            # セクション内のul要素を探す
            areas_list = areas_section.find_next('ul', class_='rm-cv-research-areas')
            if areas_list:
                area_links = areas_list.find_all('a', class_='rm-cv-list-title')
                areas = [link.get_text().strip() for link in area_links]

        # 方法2: パネルボディから直接抽出
        if not areas:
            areas_panel = soup.find('div', {'id': 'research_areas'})
            if areas_panel:
                panel_body = areas_panel.find_next('div', class_='research_areas-body')
                if panel_body:
                    area_links = panel_body.find_all('a', class_='rm-cv-list-title')
                    areas = [link.get_text().strip() for link in area_links]

        return areas

    def _extract_affiliations(self, soup: BeautifulSoup) -> List[str]:
        """所属情報を抽出（改善版）"""
        affiliations = []

        # 基本情報セクションから所属を抽出
        profile_section = soup.find('div', {'id': 'profile'})
        if profile_section:
            # 所属のdt要素を探す
            affiliation_dt = profile_section.find('dt', string='所属')
            if affiliation_dt:
                # 対応するdd要素を取得
                affiliation_dd = affiliation_dt.find_next_sibling('dd')
                if affiliation_dd:
                    # すべてのdd要素を取得（複数の所属がある場合）
                    current_dd = affiliation_dd
                    while current_dd:
                        affiliation_text = current_dd.get_text().strip()
                        if affiliation_text and affiliation_text != '所属':
                            affiliations.append(affiliation_text)

                        # 次のdt要素を確認
                        next_dt = current_dd.find_next_sibling('dt')
                        if next_dt and next_dt.get_text().strip() == '':
                            # 空のdtの場合は次のddを取得
                            current_dd = next_dt.find_next_sibling('dd')
                        else:
                            break

        # 方法2: dl要素から直接抽出
        if not affiliations:
            dl_elements = soup.find_all('dl', class_='rm-cv-basic-dl')
            for dl in dl_elements:
                dt_elements = dl.find_all('dt')
                for dt in dt_elements:
                    if dt.get_text().strip() == '所属':
                        dd = dt.find_next_sibling('dd')
                        if dd:
                            affiliation_text = dd.get_text().strip()
                            if affiliation_text:
                                affiliations.append(affiliation_text)

                        # 空のdt要素の後のdd要素も取得
                        current_dt = dt
                        while current_dt:
                            next_dt = current_dt.find_next_sibling('dt')
                            if next_dt and next_dt.get_text().strip() == '':
                                next_dd = next_dt.find_next_sibling('dd')
                                if next_dd:
                                    affiliation_text = next_dd.get_text().strip()
                                    if affiliation_text:
                                        affiliations.append(affiliation_text)
                                current_dt = next_dt
                            else:
                                break

        return affiliations

    def _extract_all_projects(self, researcher_url: str) -> List[Dict[str, Any]]:
        """研究者のすべての研究課題を抽出（改善版）"""
        try:
            projects_url = URLHelper.build_projects_url(researcher_url)
            response = self._make_request(projects_url)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            projects = []

            # 研究課題リストを探す（正しいHTML構造）
            project_items = soup.find_all('li', class_='list-group-item')

            for item in project_items:
                project = {}

                # タイトルを抽出
                title_link = item.find('a', class_='rm-cv-list-title')
                if title_link:
                    project['title'] = title_link.get_text().strip()
                    project['project_url'] = URLHelper.ensure_absolute_url(title_link.get('href'))

                # 資金システムと期間を抽出
                divs = item.find_all('div')
                for div in divs:
                    # タイトルリンクを含まないdivを探す
                    if not div.find('a') and (not div.get('class') or 'rm-cv-list-author' not in div.get('class', [])):
                        funding_text = div.get_text().strip()
                        if funding_text and funding_text != project.get('title', ''):
                            # 研究者情報を含まないように調整
                            lines = funding_text.split('\n')
                            funding_lines = []
                            for line in lines:
                                line = line.strip()
                                if line and not any(keyword in line for keyword in ['兼松', '平井', '小川', '生貝', '田路', '小林', '岡田', '内海', '三浦', '加藤', '鈴木', '秋元', '岩田', '矢島', '中平', 'Colligon', '枡田', '小川', '亜希子', '玉内']):
                                    funding_lines.append(line)
                            if funding_lines:
                                project['funding_system'] = ' '.join(funding_lines)
                            break

                # 研究者を抽出
                author_div = item.find('div', class_='rm-cv-list-author')
                if author_div:
                    project['researchers'] = author_div.get_text().strip()

                # 競争的資金かどうかを判定
                project['is_competitive'] = self.is_competitive_funding_by_html_structure(
                    project.get('funding_system', ''),
                    project.get('institution', ''),
                    project.get('project_type', '')
                )

                if project.get('title'):  # タイトルがある場合のみ追加
                    projects.append(project)

            return projects

        except Exception as e:
            logger.error(f"研究課題抽出エラー: {e}")
            return []

    def _extract_competitive_projects(self, all_projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """競争的研究課題を抽出"""
        competitive_projects = []

        for project in all_projects:
            if project.get('is_competitive', False):
                competitive_projects.append(project)

        return competitive_projects

    def get_research_projects(self, researcher_url: str) -> List[Dict[str, Any]]:
        """研究者の競争的研究課題を詳細情報付きで取得"""
        try:
            logger.info(f"研究課題詳細を取得中: {researcher_url}")
            projects_url = URLHelper.build_projects_url(researcher_url)
            logger.info(f"研究課題ページURL: {projects_url}")

            response = self._make_request(projects_url)
            projects = self.extract_research_projects_from_html(response.text)

            logger.info(f"{len(projects)}件の研究課題を取得しました")
            return projects

        except Exception as e:
            logger.error(f"研究課題取得エラー: {e}")
            return []

    def get_project_details(self, project_url: str) -> Dict[str, Any]:
        """研究課題の詳細情報を取得（改善版）"""
        try:
            response = self._make_request(project_url)
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
                    funding_system = DataExtractor.extract_funding_system(text_content)
                    if funding_system:
                        details['funding_system'] = funding_system

                        # 助成金システムの詳細解析
                        funding_details = self.analyze_funding_system(funding_system)
                        details.update(funding_details)

                    # 2.2 期間情報の取得（拡張版）
                    period = DataExtractor.extract_period(text_content)
                    if period:
                        details['period'] = period

                    # 2.3 研究者情報の取得（拡張版）
                    researchers = DataExtractor.extract_researchers(text_content)
                    if researchers:
                        details['researchers'] = researchers

                    # 2.4 予算情報の取得
                    budget = DataExtractor.extract_budget(text_content)
                    if budget:
                        details['budget'] = budget

                    # 2.5 研究種目・カテゴリの取得
                    research_category = DataExtractor.extract_research_category(text_content)
                    if research_category:
                        details['research_category'] = research_category

            # 3. ページ全体から追加情報を抽出
            full_text = soup.get_text()

            # 3.1 キーワードの抽出
            keywords = DataExtractor.extract_keywords(full_text)
            if keywords:
                details['keywords'] = keywords

            # 3.2 研究機関・組織の抽出
            organizations = DataExtractor.extract_organizations(full_text)
            if organizations:
                details['organizations'] = organizations

            return details

        except Exception as e:
            logger.error(f"研究課題詳細取得エラー: {e}")
            return {}

    def analyze_funding_system(self, funding_system: str) -> Dict[str, Any]:
        """助成金システム情報を詳細解析"""
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
        """HTMLの構成要素に基づいて競争的資金かどうかを判定"""
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

    def get_researcher_keywords(self, researcher_url: str) -> List[Dict[str, Any]]:
        """研究者の研究キーワードを取得"""
        try:
            logger.info(f"研究キーワードを取得中: {researcher_url}")

            response = self._make_request(researcher_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            keywords = []

            # 研究キーワードセクションを取得
            keywords_section = soup.find('div', class_='research_interests-body')
            if keywords_section:
                keyword_items = keywords_section.find_all('li', class_='rm-cv-disclosed')

                for item in keyword_items:
                    keyword_link = item.find('a', class_='rm-cv-list-title')
                    if keyword_link:
                        keyword_info = {
                            'keyword': keyword_link.get_text().strip(),
                            'url': keyword_link.get('href', ''),
                            'keyword_id': keyword_link.get('href', '').split('/')[-1] if keyword_link.get('href') else ''
                        }
                        keywords.append(keyword_info)
                        logger.info(f"  キーワード: {keyword_info['keyword']}")

            logger.info(f"{len(keywords)}件の研究キーワードを取得しました")
            return keywords

        except Exception as e:
            logger.error(f"研究キーワード取得エラー: {e}")
            return []

    def get_researcher_areas(self, researcher_url: str) -> List[Dict[str, Any]]:
        """研究者の研究分野を取得"""
        try:
            logger.info(f"研究分野を取得中: {researcher_url}")

            response = self._make_request(researcher_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            areas = []

            # 研究分野セクションを取得
            areas_section = soup.find('div', class_='research_areas-body')
            if areas_section:
                area_items = areas_section.find_all('li', class_='rm-cv-disclosed')

                for item in area_items:
                    area_link = item.find('a', class_='rm-cv-list-title')
                    if area_link:
                        area_info = {
                            'area': area_link.get_text().strip(),
                            'url': area_link.get('href', ''),
                            'area_id': area_link.get('href', '').split('/')[-1] if area_link.get('href') else ''
                        }
                        areas.append(area_info)
                        logger.info(f"  研究分野: {area_info['area']}")

            logger.info(f"{len(areas)}件の研究分野を取得しました")
            return areas

        except Exception as e:
            logger.error(f"研究分野取得エラー: {e}")
            return []

    def get_researcher_affiliations(self, researcher_url: str) -> List[Dict[str, Any]]:
        """研究者のすべての所属先を取得"""
        try:
            logger.info(f"所属先を取得中: {researcher_url}")

            response = self._make_request(researcher_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            affiliations = []

            # 基本情報セクションから所属先を取得
            basic_info_sections = soup.find_all('dl', class_='rm-cv-basic-dl')

            for section in basic_info_sections:
                dt_elements = section.find_all('dt')
                dd_elements = section.find_all('dd')

                # 所属セクションを見つける
                for i, dt in enumerate(dt_elements):
                    if dt.get_text().strip() == '所属':
                        # 所属のdd要素を処理（複数のdd要素に分かれている可能性）
                        j = i
                        while j < len(dd_elements):
                            dd = dd_elements[j]
                            affiliation_links = dd.find_all('a')

                            if affiliation_links:
                                for link in affiliation_links:
                                    affiliation_text = link.get_text().strip()
                                    affiliation_url = link.get('href', '')

                                    # 役職情報を取得（リンクの後のテキスト）
                                    position_text = ''
                                    if link.next_sibling:
                                        position_text = link.next_sibling.strip()

                                    affiliation_info = {
                                        'institution': affiliation_text,
                                        'url': affiliation_url,
                                        'position': position_text,
                                        'full_text': link.parent.get_text().strip() if link.parent else ''
                                    }
                                    affiliations.append(affiliation_info)
                                    logger.info(f"  所属先: {affiliation_text} - {position_text}")

                                # 次のdd要素に進む
                                j += 1
                            else:
                                # リンクがない場合は次のdt要素までスキップ
                                break

                        # 所属セクションを処理したので終了
                        break

            logger.info(f"{len(affiliations)}件の所属先を取得しました")
            return affiliations

        except Exception as e:
            logger.error(f"所属先取得エラー: {e}")
            return []

    def get_researcher_education(self, researcher_url: str) -> List[Dict[str, Any]]:
        """研究者の学歴を取得"""
        try:
            logger.info(f"学歴を取得中: {researcher_url}")

            response = self._make_request(researcher_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            education = []

            # 学歴セクションを取得
            education_section = soup.find('div', class_='education-body')
            if education_section:
                education_items = education_section.find_all('li', class_='list-group-item rm-cv-disclosed')

                for item in education_items:
                    content_div = item.find('div', class_='rm-cv-list-content')
                    if content_div:
                        row_div = content_div.find('div', class_='row')
                        if row_div:
                            cols = row_div.find_all('div')
                            if len(cols) >= 2:
                                period = cols[0].get_text().strip()
                                education_link = cols[1].find('a', class_='rm-cv-list-title')

                                if education_link:
                                    education_info = {
                                        'period': period,
                                        'institution': education_link.get_text().strip(),
                                        'url': education_link.get('href', ''),
                                        'education_id': education_link.get('href', '').split('/')[-1] if education_link.get('href') else ''
                                    }
                                    education.append(education_info)
                                    logger.info(f"  学歴: {period} - {education_info['institution']}")

            logger.info(f"{len(education)}件の学歴を取得しました")
            return education

        except Exception as e:
            logger.error(f"学歴取得エラー: {e}")
            return []

    def scrape_all_researchers_and_projects(self, search_url: str = None,
                                          max_researchers: int = None) -> Dict[str, Any]:
        """全研究者とその競争的研究課題を取得"""
        logger.info("研究者と競争的研究課題の取得を開始")

        if not search_url:
            search_url = URLHelper.build_search_url("%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE")

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

                # 詳細情報を取得
                detailed_info = self.get_researcher_detailed_info(researcher_url)

                # すべての研究課題を取得
                all_projects = self._extract_all_projects(researcher_url)

                # 競争的研究課題を抽出
                competitive_projects = self._extract_competitive_projects(all_projects)
                total_competitive_projects += len(competitive_projects)

                researcher_data = researcher.copy()
                researcher_data.update(detailed_info)
                researcher_data['all_projects'] = all_projects
                researcher_data['competitive_projects'] = competitive_projects
                researcher_data['competitive_project_count'] = len(competitive_projects)

                researchers_with_projects.append(researcher_data)

                logger.info(f"研究者 {researcher.get('name', 'Unknown')}: "
                          f"全{len(all_projects)}件、競争的{len(competitive_projects)}件 "
                          f"(累計: {total_competitive_projects}件)")

                time.sleep(random.uniform(ScrapingConfig.REQUEST_DELAY_MIN, ScrapingConfig.REQUEST_DELAY_MAX))

            except Exception as e:
                logger.error(f"研究者 {researcher.get('name', 'Unknown')} の処理エラー: {e}")
                continue

        result = {
            'total_researchers': len(all_researchers),
            'processed_researchers': len(researchers_with_projects),
            'total_competitive_projects': total_competitive_projects,
            'researchers': researchers_with_projects,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'search_url': search_url
        }

        logger.info(f"取得完了: 研究者{result['processed_researchers']}人、"
                   f"競争的研究課題{result['total_competitive_projects']}件")

        return result

    def save_results(self, data: Dict[str, Any], output_file: str = None):
        """結果をJSONファイルに保存"""
        if not output_file:
            output_file = f"researchmap_integrated_results.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"結果を {output_file} に保存しました")
        except Exception as e:
            logger.error(f"ファイル保存エラー: {e}")

    def export_to_excel(self, data: Dict[str, Any], output_file: str = None):
        """結果をExcelファイルにエクスポート"""
        if not output_file:
            output_file = "researchmap_results.xlsx"

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
                    'competitive_project_count': researcher.get('competitive_project_count', 0),
                    'orcid_id': researcher.get('orcid_id', ''),
                    'jglobal_id': researcher.get('jglobal_id', ''),
                    'researchmap_member_id': researcher.get('researchmap_member_id', ''),
                    'research_keywords': '; '.join(researcher.get('research_keywords', [])),
                    'research_areas': '; '.join(researcher.get('research_areas', [])),
                    'all_affiliations': '; '.join(researcher.get('all_affiliations', []))
                }

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
                        '検索URL'
                    ],
                    '値': [
                        data['total_researchers'],
                        data['processed_researchers'],
                        data['total_competitive_projects'],
                        len([r for r in data['researchers'] if r.get('competitive_project_count', 0) > 0]),
                        data['scraped_at'],
                        data['search_url']
                    ]
                }

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='サマリー', index=False)

            logger.info(f"結果を {output_file} にエクスポートしました")

        except Exception as e:
            logger.error(f"Excelエクスポートエラー: {e}")

    def get_comprehensive_researcher_data(self, researcher_url: str) -> Dict[str, Any]:
        """一人の研究者について取得できるすべてのデータを取得"""
        comprehensive_data = self._initialize_comprehensive_data(researcher_url)

        try:
            logger.info(f"研究者の包括的データ取得開始: {researcher_url}")

            # 各データを順次取得
            comprehensive_data.update(self._collect_basic_info(researcher_url))
            comprehensive_data.update(self._collect_detailed_info(researcher_url))
            comprehensive_data.update(self._collect_keywords_and_areas(researcher_url))
            comprehensive_data.update(self._collect_affiliations_and_education(researcher_url))
            comprehensive_data.update(self._collect_research_projects(researcher_url))
            comprehensive_data.update(self._generate_summary(comprehensive_data))

            logger.info("=== 包括的データ取得完了 ===")
            return comprehensive_data

        except Exception as e:
            logger.error(f"包括的データ取得中にエラーが発生しました: {e}")
            return comprehensive_data

    def _initialize_comprehensive_data(self, researcher_url: str) -> Dict[str, Any]:
        """包括的データの初期構造を作成"""
        return {
            'researcher_url': researcher_url,
            'basic_info': {},
            'detailed_info': {},
            'research_keywords': [],
            'research_areas': [],
            'all_affiliations': [],
            'education': [],
            'research_projects': [],
            'summary': {}
        }

    def _collect_basic_info(self, researcher_url: str) -> Dict[str, Any]:
        """基本情報を収集"""
        logger.info("=== 1. 研究者の基本情報を取得 ===")
        basic_info = self.get_researcher_basic_info(researcher_url)
        logger.info(f"基本情報取得完了: {basic_info.get('name', 'Unknown')}")
        return {'basic_info': basic_info}

    def _collect_detailed_info(self, researcher_url: str) -> Dict[str, Any]:
        """詳細情報を収集"""
        logger.info("=== 2. 研究者の詳細情報を取得 ===")
        detailed_info = self.get_researcher_detailed_info(researcher_url)
        logger.info(f"詳細情報取得完了: ORCID={detailed_info.get('orcid_id', 'N/A')}")
        return {'detailed_info': detailed_info}

    def _collect_keywords_and_areas(self, researcher_url: str) -> Dict[str, Any]:
        """研究キーワードと研究分野を収集（改善版）"""
        logger.info("=== 3. 研究キーワードと研究分野を取得 ===")

        # 研究者ページから直接抽出
        response = self._make_request(researcher_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        keywords = self._extract_research_keywords(soup)
        areas = self._extract_research_areas(soup)

        logger.info(f"研究キーワード取得完了: {len(keywords)}件")
        logger.info(f"研究分野取得完了: {len(areas)}件")

        return {
            'research_keywords': keywords,
            'research_areas': areas
        }

    def _collect_affiliations_and_education(self, researcher_url: str) -> Dict[str, Any]:
        """所属先と学歴を収集（改善版）"""
        logger.info("=== 5. 所属先と学歴を取得 ===")

        # 研究者ページから直接抽出
        response = self._make_request(researcher_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        affiliations = self._extract_affiliations(soup)
        logger.info(f"所属先取得完了: {len(affiliations)}件")

        # 学歴は既存の方法を使用
        education = self.get_researcher_education(researcher_url)
        logger.info(f"学歴取得完了: {len(education)}件")

        return {
            'all_affiliations': affiliations,
            'education': education
        }

    def _collect_research_projects(self, researcher_url: str) -> Dict[str, Any]:
        """研究課題を収集（改善版）"""
        logger.info("=== 7. 研究課題を取得 ===")

        # すべての研究課題を取得
        all_projects = self._extract_all_projects(researcher_url)

        # 競争的研究課題を抽出
        competitive_projects = self._extract_competitive_projects(all_projects)

        logger.info(f"研究課題取得完了: 全{len(all_projects)}件、競争的{len(competitive_projects)}件")

        return {
            'research_projects': all_projects,
            'competitive_projects': competitive_projects
        }

    def _generate_summary(self, comprehensive_data: Dict[str, Any]) -> Dict[str, Any]:
        """サマリー情報を生成"""
        logger.info("=== 8. サマリー情報を生成 ===")
        summary = self.generate_summary(comprehensive_data)
        logger.info(f"サマリー生成完了: {summary}")
        return {'summary': summary}

    def get_researcher_basic_info(self, researcher_url: str) -> Dict[str, Any]:
        """研究者の基本情報を取得（検索結果ページから）"""
        try:
            # 研究者IDを抽出
            researcher_id = URLHelper.extract_researcher_id(researcher_url)

            # 検索URLを構築（研究者名で検索）
            search_url = URLHelper.build_search_url(researcher_id)

            response = self._make_request(search_url)
            researchers = self.extract_researchers_from_page(response.content)

            # 該当する研究者を探す
            for researcher in researchers:
                if researcher.get('researcher_url') == researcher_url:
                    return researcher

            # 見つからない場合は空の辞書を返す
            return {}

        except Exception as e:
            logger.error(f"基本情報取得エラー: {e}")
            return {}

    def generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データのサマリー情報を生成"""
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
        projects = data.get('research_projects', [])

        summary['total_projects'] = len(projects)

        # 競争的研究課題の統計
        competitive_projects = [p for p in projects if p.get('is_competitive', False)]

        summary['competitive_projects'] = len(competitive_projects)

        # 助成金機関の統計
        institutions = {}
        for project in projects:
            institution = project.get('institution', 'Unknown')
            if institution in institutions:
                institutions[institution] += 1
            else:
                institutions[institution] = 1

        summary['funding_institutions'] = institutions
        summary['unique_institutions_count'] = len(institutions)

        # 研究期間の統計
        periods = [p.get('period', 'Unknown') for p in projects if p.get('period')]
        summary['research_periods'] = list(set(periods))

        return summary

    def save_comprehensive_data(self, data: Dict[str, Any], researcher_id: str = None) -> str:
        """包括的データをJSONファイルに保存"""
        if not researcher_id:
            researcher_id = data.get('basic_info', {}).get('researcher_id', 'unknown')

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_researcher_data_{researcher_id}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"包括的データを保存しました: {filename}")
        return filename

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='Research Map統合スクレイパー')
    parser.add_argument('--search-url', type=str,
                       default='https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE',
                       help='検索URL')
    parser.add_argument('--researcher-url', type=str,
                       help='包括的データ取得用の研究者URL')
    parser.add_argument('--test', type=int, help='テストモード: 指定した数の研究者のみ処理')
    parser.add_argument('--output-prefix', type=str, default='researchmap_integrated',
                       help='出力ファイルのプレフィックス')

    args = parser.parse_args()

    # スクレイパーを初期化
    scraper = ResearchMapIntegratedScraper()

    try:
        if args.researcher_url:
            # 包括的データ取得モード
            logger.info(f"包括的データ取得を開始: {args.researcher_url}")

            # 包括的データを取得
            comprehensive_data = scraper.get_comprehensive_researcher_data(args.researcher_url)

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

        else:
            # 通常の一括取得モード
            results = scraper.scrape_all_researchers_and_projects(
                search_url=args.search_url,
                max_researchers=args.test
            )

            # 結果を保存
            if args.test:
                output_prefix = f"{args.output_prefix}_test_{args.test}"
            else:
                output_prefix = args.output_prefix

            scraper.save_results(results, f"{output_prefix}_results.json")
            scraper.export_to_excel(results, f"{output_prefix}_results.xlsx")

            logger.info("処理が完了しました")

    except Exception as e:
        logger.error(f"メイン処理エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
