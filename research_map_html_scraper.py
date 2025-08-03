#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Research Map HTML Scraper

Research MapのHTMLページから研究者情報をスクレイピングし、
名前、競争的資金の研究課題リスト、URLなどを含んだデータを取得するツール
"""

import requests
import json
import csv
import time
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import logging
from bs4 import BeautifulSoup
import pandas as pd

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResearchMapHTMLScraper:
    """
    Research MapのHTMLページから研究者情報をスクレイピングするクラス
    """

    def __init__(self, base_url: str = "https://researchmap.jp"):
        """
        Research Map HTML Scraperの初期化

        Args:
            base_url (str): Research MapのベースURL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_researcher_profile(self, researcher_id: str) -> Dict[str, Any]:
        """
        研究者のプロフィール情報を取得

        Args:
            researcher_id (str): 研究者ID（例: m-kudo）

        Returns:
            Dict[str, Any]: 研究者のプロフィール情報
        """
        try:
            # 研究者のホームページを取得
            profile_url = f"{self.base_url}/{researcher_id}"
            logger.info(f"研究者プロフィールを取得中: {profile_url}")

            response = self.session.get(profile_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # 研究者名を取得
            name = self._extract_researcher_name(soup)

            # 所属情報を取得
            organization = self._extract_organization(soup)

            # 研究課題ページのURLを取得
            research_projects_url = f"{self.base_url}/{researcher_id}/research_projects"

            # 研究課題を取得
            research_projects = self.get_research_projects(researcher_id)

            return {
                'researcher_id': researcher_id,
                'name': name,
                'organization': organization,
                'profile_url': profile_url,
                'research_projects_url': research_projects_url,
                'research_projects': research_projects,
                'total_projects': len(research_projects)
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"研究者プロフィール取得エラー (ID: {researcher_id}): {e}")
            return {}

    def _extract_researcher_name(self, soup: BeautifulSoup) -> str:
        """
        HTMLから研究者名を抽出

        Args:
            soup (BeautifulSoup): BeautifulSoupオブジェクト

        Returns:
            str: 研究者名
        """
        try:
            # タイトルから研究者名を抽出
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # "工藤 正俊 (Masatoshi Kudo) - ..." の形式から名前を抽出
                match = re.search(r'^([^(]+)', title_text)
                if match:
                    return match.group(1).strip()

            # 代替方法: ページ内の研究者名を探す
            name_elements = soup.find_all(['h1', 'h2', 'h3'], class_=re.compile(r'.*name.*'))
            for element in name_elements:
                name = element.get_text().strip()
                if name and len(name) > 0:
                    return name

            return "不明"

        except Exception as e:
            logger.error(f"研究者名抽出エラー: {e}")
            return "不明"

    def _extract_organization(self, soup: BeautifulSoup) -> str:
        """
        HTMLから所属情報を抽出

        Args:
            soup (BeautifulSoup): BeautifulSoupオブジェクト

        Returns:
            str: 所属情報
        """
        try:
            # 所属情報を含む要素を探す
            org_elements = soup.find_all(['div', 'span', 'p'], string=re.compile(r'.*大学.*|.*研究所.*|.*病院.*|.*企業.*'))
            for element in org_elements:
                org_text = element.get_text().strip()
                if org_text and len(org_text) > 0:
                    return org_text

            return "不明"

        except Exception as e:
            logger.error(f"所属情報抽出エラー: {e}")
            return "不明"

    def get_research_projects(self, researcher_id: str) -> List[Dict[str, Any]]:
        """
        研究者の研究課題一覧を取得

        Args:
            researcher_id (str): 研究者ID

        Returns:
            List[Dict[str, Any]]: 研究課題のリスト
        """
        try:
            projects_url = f"{self.base_url}/{researcher_id}/research_projects"
            logger.info(f"研究課題を取得中: {projects_url}")

            response = self.session.get(projects_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            projects = []

            # 研究課題のリストを取得
            project_elements = soup.find_all('li', class_=re.compile(r'.*rm-cv.*'))

            for element in project_elements:
                project = self._extract_project_info(element)
                if project:
                    projects.append(project)

            return projects

        except requests.exceptions.RequestException as e:
            logger.error(f"研究課題取得エラー (ID: {researcher_id}): {e}")
            return []

    def _extract_project_info(self, element) -> Optional[Dict[str, Any]]:
        """
        HTML要素から研究課題情報を抽出

        Args:
            element: BeautifulSoup要素

        Returns:
            Optional[Dict[str, Any]]: 研究課題情報
        """
        try:
            # 研究課題タイトルを取得
            title_element = element.find('a', class_=re.compile(r'.*rm-cv-list-title.*'))
            title = title_element.get_text().strip() if title_element else ""

            # 研究課題URLを取得
            project_url = ""
            if title_element and title_element.get('href'):
                project_url = urljoin(self.base_url, title_element['href'])

            # 研究課題IDを取得
            project_id = ""
            if project_url:
                match = re.search(r'/research_projects/(\d+)', project_url)
                if match:
                    project_id = match.group(1)

            # 研究期間と資金情報を取得
            period_info = ""
            funding_info = ""

            # 研究期間と資金情報を含む要素を探す
            info_elements = element.find_all('div')
            for info_element in info_elements:
                text = info_element.get_text().strip()
                if text and not title in text:
                    if re.search(r'\d{4}年.*\d{4}年|\d{4}年.*月', text):
                        period_info = text
                    elif re.search(r'科学研究費|基盤研究|挑戦的|若手|特別研究員|助成', text):
                        funding_info = text

            # 研究者名を取得
            authors = ""
            author_element = element.find('div', class_=re.compile(r'.*rm-cv-list-author.*'))
            if author_element:
                authors = author_element.get_text().strip()

            return {
                'project_id': project_id,
                'title': title,
                'project_url': project_url,
                'period': period_info,
                'funding': funding_info,
                'authors': authors
            }

        except Exception as e:
            logger.error(f"研究課題情報抽出エラー: {e}")
            return None

    def search_researchers_by_organization(self, organization_name: str) -> List[str]:
        """
        組織名で研究者を検索（簡易版）

        Args:
            organization_name (str): 検索する組織名

        Returns:
            List[str]: 研究者IDのリスト
        """
        # 注意: Research Mapの検索機能はAPIを使用する必要があります
        # この実装は簡易版で、既知の研究者IDリストを使用します
        logger.warning("組織名での検索は簡易版です。既知の研究者IDリストを使用します。")

        # サンプルの研究者IDリスト（実際の使用時は適切なリストに置き換えてください）
        sample_researchers = [
            "m-kudo",  # 工藤 正俊
            # 他の研究者IDを追加
        ]

        return sample_researchers

    def scrape_portfolio_researchers(self, portfolio_file: str = "portfolio_results.json") -> List[Dict[str, Any]]:
        """
        ポートフォリオ企業の研究者情報をスクレイピング

        Args:
            portfolio_file (str): ポートフォリオ結果のJSONファイル

        Returns:
            List[Dict[str, Any]]: 研究者情報のリスト
        """
        try:
            # ポートフォリオファイルを読み込み
            with open(portfolio_file, 'r', encoding='utf-8') as f:
                portfolio_data = json.load(f)

            all_researchers = []

            # 各企業の研究者を検索（簡易版）
            for company in portfolio_data.get('companies', []):
                company_name = company.get('name', '')
                logger.info(f"企業 '{company_name}' の研究者を検索中...")

                # 簡易版のため、サンプル研究者を使用
                researcher_ids = self.search_researchers_by_organization(company_name)

                for researcher_id in researcher_ids:
                    logger.info(f"研究者 {researcher_id} の情報を取得中...")

                    researcher_info = self.get_researcher_profile(researcher_id)
                    if researcher_info:
                        researcher_info['company'] = company_name
                        all_researchers.append(researcher_info)

                    # API制限を避けるため少し待機
                    time.sleep(1)

            return all_researchers

        except FileNotFoundError:
            logger.error(f"ポートフォリオファイル '{portfolio_file}' が見つかりません")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSONファイルの解析エラー: {e}")
            return []

    def export_to_csv(self, researchers_data: List[Dict[str, Any]], output_file: str = "researchers_data.csv"):
        """
        研究者データをCSVファイルにエクスポート

        Args:
            researchers_data (List[Dict[str, Any]]): 研究者データ
            output_file (str): 出力ファイル名
        """
        try:
            # フラット化されたデータを作成
            flat_data = []

            for researcher in researchers_data:
                if not researcher.get('research_projects'):
                    # 研究課題がない場合
                    flat_data.append({
                        '研究者ID': researcher.get('researcher_id', ''),
                        '研究者名': researcher.get('name', ''),
                        '所属組織': researcher.get('organization', ''),
                        '企業': researcher.get('company', ''),
                        'プロフィールURL': researcher.get('profile_url', ''),
                        '研究課題URL': researcher.get('research_projects_url', ''),
                        '研究課題ID': '',
                        '研究課題タイトル': '',
                        '研究期間': '',
                        '資金情報': '',
                        '研究者': '',
                        '総研究課題数': researcher.get('total_projects', 0)
                    })
                else:
                    # 研究課題がある場合
                    for project in researcher['research_projects']:
                        flat_data.append({
                            '研究者ID': researcher.get('researcher_id', ''),
                            '研究者名': researcher.get('name', ''),
                            '所属組織': researcher.get('organization', ''),
                            '企業': researcher.get('company', ''),
                            'プロフィールURL': researcher.get('profile_url', ''),
                            '研究課題URL': researcher.get('research_projects_url', ''),
                            '研究課題ID': project.get('project_id', ''),
                            '研究課題タイトル': project.get('title', ''),
                            '研究期間': project.get('period', ''),
                            '資金情報': project.get('funding', ''),
                            '研究者': project.get('authors', ''),
                            '総研究課題数': researcher.get('total_projects', 0)
                        })

            # CSVファイルに書き込み
            if flat_data:
                df = pd.DataFrame(flat_data)
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                logger.info(f"研究者データを '{output_file}' にエクスポートしました")
            else:
                logger.warning("エクスポートするデータがありません")

        except Exception as e:
            logger.error(f"CSVエクスポートエラー: {e}")

    def export_to_json(self, researchers_data: List[Dict[str, Any]], output_file: str = "researchers_data.json"):
        """
        研究者データをJSONファイルにエクスポート

        Args:
            researchers_data (List[Dict[str, Any]]): 研究者データ
            output_file (str): 出力ファイル名
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(researchers_data, f, ensure_ascii=False, indent=2)

            logger.info(f"研究者データを '{output_file}' にエクスポートしました")

        except Exception as e:
            logger.error(f"JSONエクスポートエラー: {e}")

    def generate_summary_report(self, researchers_data: List[Dict[str, Any]], output_file: str = "researchers_summary.txt"):
        """
        研究者データのサマリーレポートを生成

        Args:
            researchers_data (List[Dict[str, Any]]): 研究者データ
            output_file (str): 出力ファイル名
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== Research Map 研究者情報サマリーレポート ===\n\n")

                # 概要統計
                total_researchers = len(researchers_data)
                total_projects = sum(r.get('total_projects', 0) for r in researchers_data)

                f.write(f"総研究者数: {total_researchers}人\n")
                f.write(f"総研究課題数: {total_projects}件\n\n")

                # 企業別統計
                company_stats = {}
                for researcher in researchers_data:
                    company = researcher.get('company', '不明')
                    if company not in company_stats:
                        company_stats[company] = {'researchers': 0, 'projects': 0}
                    company_stats[company]['researchers'] += 1
                    company_stats[company]['projects'] += researcher.get('total_projects', 0)

                f.write("【企業別統計】\n")
                for company, stats in company_stats.items():
                    f.write(f"- {company}: {stats['researchers']}人, {stats['projects']}件の研究課題\n")
                f.write("\n")

                # 研究者詳細
                f.write("【研究者詳細】\n")
                for researcher in researchers_data:
                    f.write(f"\n研究者: {researcher.get('name', '')}\n")
                    f.write(f"ID: {researcher.get('researcher_id', '')}\n")
                    f.write(f"所属: {researcher.get('organization', '')}\n")
                    f.write(f"企業: {researcher.get('company', '')}\n")
                    f.write(f"研究課題数: {researcher.get('total_projects', 0)}件\n")
                    f.write(f"プロフィール: {researcher.get('profile_url', '')}\n")

                    if researcher.get('research_projects'):
                        f.write("研究課題:\n")
                        for project in researcher['research_projects']:
                            f.write(f"  - {project.get('title', '')}\n")
                            f.write(f"    期間: {project.get('period', '')}\n")
                            f.write(f"    資金: {project.get('funding', '')}\n")
                            f.write(f"    研究者: {project.get('authors', '')}\n")

                    f.write("-" * 50 + "\n")

            logger.info(f"サマリーレポートを '{output_file}' に生成しました")

        except Exception as e:
            logger.error(f"サマリーレポート生成エラー: {e}")


def main():
    """
    メイン実行関数
    """
    # Research Map HTML Scraperの初期化
    scraper = ResearchMapHTMLScraper()

    # ポートフォリオ企業の研究者情報をスクレイピング
    logger.info("ポートフォリオ企業の研究者情報をスクレイピング中...")
    researchers_data = scraper.scrape_portfolio_researchers()

    if researchers_data:
        # 結果をCSVファイルにエクスポート
        scraper.export_to_csv(researchers_data, "researchers_data.csv")

        # 結果をJSONファイルにエクスポート
        scraper.export_to_json(researchers_data, "researchers_data.json")

        # サマリーレポートを生成
        scraper.generate_summary_report(researchers_data, "researchers_summary.txt")

        logger.info("スクレイピングが完了しました")
        logger.info(f"取得した研究者数: {len(researchers_data)}人")
    else:
        logger.error("スクレイピングに失敗しました")


if __name__ == "__main__":
    main()
