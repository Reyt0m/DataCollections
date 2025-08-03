import requests
import json
import time
import pandas as pd
from typing import List, Dict, Any
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResearchMapScraper:
    """
    Research MapのAPIを使用して研究者情報を取得するクラス
    """

    def __init__(self, api_key: str = None):
        """
        Research Map Scraperの初期化

        Args:
            api_key (str): Research MapのAPIキー（必要に応じて）
        """
        self.api_key = api_key
        self.base_url = "https://researchmap.jp/api/v2"
        self.session = requests.Session()

        # APIキーがある場合はヘッダーに追加
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })

    def search_researchers_by_organization(self, organization_name: str) -> List[Dict[str, Any]]:
        """
        組織名で研究者を検索

        Args:
            organization_name (str): 検索する組織名

        Returns:
            List[Dict[str, Any]]: 研究者のリスト
        """
        try:
            # 組織名で研究者を検索
            search_url = f"{self.base_url}/researchers"
            params = {
                'q': organization_name,
                'limit': 100  # 最大100件取得
            }

            logger.info(f"組織 '{organization_name}' の研究者を検索中...")
            response = self.session.get(search_url, params=params)
            response.raise_for_status()

            researchers = response.json().get('researchers', [])
            logger.info(f"{len(researchers)}人の研究者が見つかりました")

            return researchers

        except requests.exceptions.RequestException as e:
            logger.error(f"研究者検索エラー: {e}")
            return []

    def get_researcher_details(self, researcher_id: str) -> Dict[str, Any]:
        """
        研究者の詳細情報を取得

        Args:
            researcher_id (str): 研究者ID

        Returns:
            Dict[str, Any]: 研究者の詳細情報
        """
        try:
            # 研究者の詳細情報を取得
            detail_url = f"{self.base_url}/researchers/{researcher_id}"

            logger.info(f"研究者ID {researcher_id} の詳細情報を取得中...")
            response = self.session.get(detail_url)
            response.raise_for_status()

            researcher_data = response.json()

            # 研究課題とキーワードを抽出
            research_topics = []
            keywords = []

            # 研究課題の取得
            if 'research_topics' in researcher_data:
                research_topics = [topic.get('title', '') for topic in researcher_data['research_topics']]

            # キーワードの取得
            if 'keywords' in researcher_data:
                keywords = [keyword.get('name', '') for keyword in researcher_data['keywords']]

            # 研究分野の取得
            research_fields = []
            if 'research_fields' in researcher_data:
                research_fields = [field.get('name', '') for field in researcher_data['research_fields']]

            return {
                'id': researcher_id,
                'name': researcher_data.get('name', ''),
                'organization': researcher_data.get('organization', ''),
                'position': researcher_data.get('position', ''),
                'research_topics': research_topics,
                'keywords': keywords,
                'research_fields': research_fields,
                'profile_url': f"https://researchmap.jp/{researcher_id}"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"研究者詳細取得エラー (ID: {researcher_id}): {e}")
            return {}

    def get_researcher_publications(self, researcher_id: str) -> List[Dict[str, Any]]:
        """
        研究者の論文情報を取得

        Args:
            researcher_id (str): 研究者ID

        Returns:
            List[Dict[str, Any]]: 論文のリスト
        """
        try:
            publications_url = f"{self.base_url}/researchers/{researcher_id}/publications"
            params = {'limit': 50}  # 最新50件

            response = self.session.get(publications_url, params=params)
            response.raise_for_status()

            publications = response.json().get('publications', [])
            return publications

        except requests.exceptions.RequestException as e:
            logger.error(f"論文取得エラー (ID: {researcher_id}): {e}")
            return []

    def analyze_portfolio_companies(self, portfolio_file: str = "portfolio_result.json") -> Dict[str, Any]:
        """
        ポートフォリオ企業の研究者情報を分析

        Args:
            portfolio_file (str): ポートフォリオ結果のJSONファイル

        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            # ポートフォリオファイルを読み込み
            with open(portfolio_file, 'r', encoding='utf-8') as f:
                portfolio_data = json.load(f)

            all_researchers = []
            company_researchers = {}

            # 各企業の研究者を検索
            for company in portfolio_data.get('companies', []):
                company_name = company.get('name', '')
                logger.info(f"企業 '{company_name}' の研究者を検索中...")

                researchers = self.search_researchers_by_organization(company_name)
                company_researchers[company_name] = []

                for researcher in researchers:
                    researcher_id = researcher.get('id')
                    if researcher_id:
                        # 詳細情報を取得
                        details = self.get_researcher_details(researcher_id)
                        if details:
                            company_researchers[company_name].append(details)
                            all_researchers.append(details)

                        # API制限を避けるため少し待機
                        time.sleep(1)

            return {
                'total_researchers': len(all_researchers),
                'company_researchers': company_researchers,
                'all_researchers': all_researchers
            }

        except FileNotFoundError:
            logger.error(f"ポートフォリオファイル '{portfolio_file}' が見つかりません")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSONファイルの解析エラー: {e}")
            return {}

    def export_to_excel(self, analysis_result: Dict[str, Any], output_file: str = "researchers_analysis.xlsx"):
        """
        分析結果をExcelファイルにエクスポート

        Args:
            analysis_result (Dict[str, Any]): 分析結果
            output_file (str): 出力ファイル名
        """
        try:
            # 全研究者のデータをDataFrameに変換
            researchers_data = []
            for researcher in analysis_result.get('all_researchers', []):
                researchers_data.append({
                    '研究者名': researcher.get('name', ''),
                    '所属組織': researcher.get('organization', ''),
                    '役職': researcher.get('position', ''),
                    '研究課題': '; '.join(researcher.get('research_topics', [])),
                    'キーワード': '; '.join(researcher.get('keywords', [])),
                    '研究分野': '; '.join(researcher.get('research_fields', [])),
                    'プロフィールURL': researcher.get('profile_url', '')
                })

            # 企業別研究者数の集計
            company_summary = []
            for company, researchers in analysis_result.get('company_researchers', {}).items():
                company_summary.append({
                    '企業名': company,
                    '研究者数': len(researchers)
                })

            # キーワードの頻度分析
            keyword_freq = {}
            for researcher in analysis_result.get('all_researchers', []):
                for keyword in researcher.get('keywords', []):
                    keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1

            keyword_summary = [{'キーワード': k, '出現回数': v} for k, v in keyword_freq.items()]
            keyword_summary.sort(key=lambda x: x['出現回数'], reverse=True)

            # Excelファイルに書き込み
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 研究者詳細
                if researchers_data:
                    df_researchers = pd.DataFrame(researchers_data)
                    df_researchers.to_excel(writer, sheet_name='研究者詳細', index=False)

                # 企業別集計
                if company_summary:
                    df_companies = pd.DataFrame(company_summary)
                    df_companies.to_excel(writer, sheet_name='企業別集計', index=False)

                # キーワード分析
                if keyword_summary:
                    df_keywords = pd.DataFrame(keyword_summary)
                    df_keywords.to_excel(writer, sheet_name='キーワード分析', index=False)

            logger.info(f"分析結果を '{output_file}' にエクスポートしました")

        except Exception as e:
            logger.error(f"Excelエクスポートエラー: {e}")

    def generate_research_report(self, analysis_result: Dict[str, Any], output_file: str = "research_report.txt"):
        """
        研究レポートを生成

        Args:
            analysis_result (Dict[str, Any]): 分析結果
            output_file (str): 出力ファイル名
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== 投資先企業研究者分析レポート ===\n\n")

                # 概要
                total_researchers = analysis_result.get('total_researchers', 0)
                f.write(f"総研究者数: {total_researchers}人\n\n")

                # 企業別分析
                f.write("【企業別研究者数】\n")
                for company, researchers in analysis_result.get('company_researchers', {}).items():
                    f.write(f"- {company}: {len(researchers)}人\n")
                f.write("\n")

                # 主要キーワード
                keyword_freq = {}
                for researcher in analysis_result.get('all_researchers', []):
                    for keyword in researcher.get('keywords', []):
                        keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1

                f.write("【主要研究キーワード】\n")
                sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
                for keyword, count in sorted_keywords[:20]:  # 上位20件
                    f.write(f"- {keyword}: {count}回\n")
                f.write("\n")

                # 研究者詳細
                f.write("【研究者詳細】\n")
                for researcher in analysis_result.get('all_researchers', []):
                    f.write(f"\n研究者: {researcher.get('name', '')}\n")
                    f.write(f"所属: {researcher.get('organization', '')}\n")
                    f.write(f"役職: {researcher.get('position', '')}\n")

                    if researcher.get('research_topics'):
                        f.write("研究課題:\n")
                        for topic in researcher['research_topics']:
                            f.write(f"  - {topic}\n")

                    if researcher.get('keywords'):
                        f.write("キーワード:\n")
                        for keyword in researcher['keywords']:
                            f.write(f"  - {keyword}\n")

                    f.write(f"プロフィール: {researcher.get('profile_url', '')}\n")
                    f.write("-" * 50 + "\n")

            logger.info(f"研究レポートを '{output_file}' に生成しました")

        except Exception as e:
            logger.error(f"レポート生成エラー: {e}")


def main():
    """
    メイン実行関数
    """
    # Research Map Scraperの初期化
    scraper = ResearchMapScraper()

    # ポートフォリオ企業の研究者分析
    logger.info("ポートフォリオ企業の研究者分析を開始します...")
    analysis_result = scraper.analyze_portfolio_companies()

    if analysis_result:
        # 結果をExcelファイルにエクスポート
        scraper.export_to_excel(analysis_result)

        # 研究レポートを生成
        scraper.generate_research_report(analysis_result)

        logger.info("分析が完了しました")
    else:
        logger.error("分析に失敗しました")


if __name__ == "__main__":
    main()
