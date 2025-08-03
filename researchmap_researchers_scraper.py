import requests
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import logging
import re
from urllib.parse import urljoin, urlparse
import random

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('researchmap_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ResearchMapResearchersScraper:
    """
    Research Mapから研究者情報と競争的研究課題を取得するクラス
    """

    def __init__(self):
        """
        Research Map Researchers Scraperの初期化
        """
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

            # 総件数を取得（実際のHTML構造に基づく）
            total_count_elements = soup.find_all(string=lambda text: text and '総件数' in text)
            if total_count_elements:
                # "総件数 3209" のような形式から数値を抽出
                for element in total_count_elements:
                    match = re.search(r'総件数\s*(\d+)', element)
                    if match:
                        total_count = int(match.group(1))
                        # 1ページあたり60件なので、ページ数を計算
                        total_pages = (total_count + 59) // 60  # 切り上げ
                        logger.info(f"総件数: {total_count}, 総ページ数: {total_pages}")
                        return total_pages

            # ページネーションから取得を試行
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

        # 研究者リストを取得（実際のHTML構造に基づく）
        researcher_items = soup.find_all('li')

        for item in researcher_items:
            try:
                # rm-cv-card-outerクラスを持つ要素を探す
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
                        # 研究者のURLを取得
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
                # ページURLを構築
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

                # レート制限を避けるための待機
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.error(f"ページ {page} の処理エラー: {e}")
                continue

        logger.info(f"全ページ処理完了。総計 {len(all_researchers)} 人の研究者を取得")
        return all_researchers

    def get_research_projects(self, researcher_url: str) -> List[Dict[str, Any]]:
        """
        研究者の競争的研究課題を取得

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

            # 研究課題のリンクを取得（実際のHTML構造に基づく）
            all_links = soup.find_all('a', href=True)
            research_project_links = [link for link in all_links if 'research_projects' in link['href'] and link['href'].endswith('/research_projects') == False]

            for link in research_project_links:
                try:
                    project_info = {}

                    # 研究課題名（リンクのテキスト）
                    project_title = link.get_text().strip()
                    if project_title and project_title != "もっとみる":
                        project_info['title'] = project_title

                        # 研究課題の詳細ページURL
                        project_url = link['href']
                        if not project_url.startswith('http'):
                            project_url = urljoin(self.base_url, project_url)
                        project_info['project_url'] = project_url

                        # 研究課題IDを抽出
                        match = re.search(r'/research_projects/(\d+)$', project_url)
                        if match:
                            project_info['project_id'] = match.group(1)

                        # 競争的研究資金かどうかを判定（タイトルから推測）
                        competitive_keywords = [
                            '科研費', '科学研究費', 'jst', 'amst', '文部科学省', '厚生労働省', '経済産業省',
                            '競争的', '基盤研究', '挑戦的研究', '新学術領域', '特別研究員',
                            '若手研究', '萌芽研究', '基盤研究(a)', '基盤研究(b)', '基盤研究(c)',
                            '挑戦的萌芽研究', '新学術領域研究', '特別推進研究', '科学研究費補助金'
                        ]

                        if any(keyword.lower() in project_title.lower() for keyword in competitive_keywords):
                            project_info['is_competitive'] = True
                        else:
                            # 詳細ページを確認
                            try:
                                project_response = self.session.get(project_url)
                                if project_response.status_code == 200:
                                    project_soup = BeautifulSoup(project_response.content, 'html.parser')

                                    # 研究種目やカテゴリを探す
                                    project_text = project_soup.get_text().lower()
                                    if any(keyword in project_text for keyword in competitive_keywords):
                                        project_info['is_competitive'] = True
                                    else:
                                        project_info['is_competitive'] = False
                                else:
                                    project_info['is_competitive'] = False
                            except:
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

    def scrape_all_researchers_and_projects(self, search_url: str, max_researchers: int = None) -> Dict[str, Any]:
        """
        全研究者とその競争的研究課題を取得

        Args:
            search_url (str): 検索URL
            max_researchers (int): 処理する最大研究者数（テスト用）

        Returns:
            Dict[str, Any]: 全データ
        """
        logger.info("研究者と競争的研究課題の取得を開始")

        # 全研究者を取得
        all_researchers = self.get_researchers_from_all_pages(search_url)

        # 最大研究者数が指定されている場合は制限
        if max_researchers and max_researchers < len(all_researchers):
            all_researchers = all_researchers[:max_researchers]
            logger.info(f"テストモード: 最初の{max_researchers}人の研究者のみ処理します")

        # 各研究者の競争的研究課題を取得
        researchers_with_projects = []
        total_competitive_projects = 0

        for i, researcher in enumerate(all_researchers, 1):
            try:
                logger.info(f"研究者 {i}/{len(all_researchers)} を処理中: {researcher.get('name', 'Unknown')}")

                researcher_url = researcher.get('researcher_url')
                if not researcher_url:
                    logger.warning(f"研究者 {researcher.get('name', 'Unknown')} のURLが見つかりません")
                    continue

                # 競争的研究課題を取得
                projects = self.get_research_projects(researcher_url)

                # 競争的研究課題のみをフィルタリング
                competitive_projects = [p for p in projects if p.get('is_competitive', False)]
                total_competitive_projects += len(competitive_projects)

                researcher_data = researcher.copy()
                researcher_data['all_projects'] = projects
                researcher_data['competitive_projects'] = competitive_projects
                researcher_data['competitive_project_count'] = len(competitive_projects)

                researchers_with_projects.append(researcher_data)

                logger.info(f"研究者 {researcher.get('name', 'Unknown')}: "
                          f"全{len(projects)}件、競争的{len(competitive_projects)}件 "
                          f"(累計: {total_competitive_projects}件)")

                # レート制限を避けるための待機
                time.sleep(random.uniform(2, 5))

            except Exception as e:
                logger.error(f"研究者 {researcher.get('name', 'Unknown')} の処理エラー: {e}")
                continue

        # 結果をまとめる
        result = {
            'total_researchers': len(all_researchers),
            'processed_researchers': len(researchers_with_projects),
            'total_competitive_projects': total_competitive_projects,
            'researchers': researchers_with_projects,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'search_url': search_url
        }

        logger.info(f"取得完了: 研究者{result['processed_researchers']}人、"
                   f"競争的研究課題{result['total_competitive_projects']}件")

        return result

    def save_results(self, data: Dict[str, Any], output_file: str = "researchmap_results.json"):
        """
        結果をJSONファイルに保存

        Args:
            data (Dict[str, Any]): 保存するデータ
            output_file (str): 出力ファイル名
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"結果を {output_file} に保存しました")
        except Exception as e:
            logger.error(f"ファイル保存エラー: {e}")

    def export_to_excel(self, data: Dict[str, Any], output_file: str = "researchmap_results.xlsx"):
        """
        結果をExcelファイルにエクスポート

        Args:
            data (Dict[str, Any]): エクスポートするデータ
            output_file (str): 出力ファイル名
        """
        try:
            # 研究者情報をフラット化
            researchers_data = []
            for researcher in data['researchers']:
                base_info = {
                    'name': researcher.get('name', ''),
                    'english_name': researcher.get('english_name', ''),
                    'affiliation': researcher.get('affiliation', ''),
                    'position': researcher.get('position', ''),
                    'researcher_id': researcher.get('researcher_id', ''),
                    'researcher_url': researcher.get('researcher_url', ''),
                    'competitive_project_count': researcher.get('competitive_project_count', 0)
                }

                # 競争的研究課題がない場合は基本情報のみ追加
                if not researcher.get('competitive_projects'):
                    researchers_data.append(base_info)
                else:
                    # 各競争的研究課題について行を作成
                    for project in researcher['competitive_projects']:
                        row = base_info.copy()
                        row.update({
                            'project_title': project.get('title', ''),
                            'project_period': project.get('period', ''),
                            'project_category': project.get('category', ''),
                            'project_institution': project.get('institution', ''),
                            'project_description': project.get('description', '')
                        })
                        researchers_data.append(row)

            # DataFrameに変換
            df = pd.DataFrame(researchers_data)

            # Excelファイルに保存
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='競争的研究課題', index=False)

                # サマリーシートを作成
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

def main():
    """
    メイン実行関数
    """
    import argparse

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='Research Map研究者と競争的研究課題スクレイパー')
    parser.add_argument('--test', type=int, help='テストモード: 指定した数の研究者のみ処理')
    parser.add_argument('--output-prefix', type=str, default='researchmap_researchers',
                       help='出力ファイルのプレフィックス')

    args = parser.parse_args()

    # 検索URL
    search_url = "https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE"

    # スクレイパーを初期化
    scraper = ResearchMapResearchersScraper()

    try:
        # 全研究者と競争的研究課題を取得
        if args.test:
            logger.info(f"テストモードで実行: 最初の{args.test}人の研究者のみ処理")
            results = scraper.scrape_all_researchers_and_projects(search_url, max_researchers=args.test)
            output_prefix = f"{args.output_prefix}_test_{args.test}"
        else:
            logger.info("本格実行モード: 全研究者を処理")
            results = scraper.scrape_all_researchers_and_projects(search_url)
            output_prefix = args.output_prefix

        # 結果を保存
        scraper.save_results(results, f"{output_prefix}_results.json")
        scraper.export_to_excel(results, f"{output_prefix}_results.xlsx")

        logger.info("処理が完了しました")

    except Exception as e:
        logger.error(f"メイン処理エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
