import json
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GlobisPortfolioExtractor:
    def __init__(self):
        self.results = []

    def extract_companies_from_website_content(self):
        """Extract companies from the provided website content"""
        # Based on the website content provided, extract company information
        companies_data = [
            {
                'company_name': 'RoboTruck Inc.',
                'initial_investment': 'Seed',
                'category': 'Frontier',
                'website': 'robotruck.jp',
                'description': '自動運転トラックの開発・運用を通じて、物流の抜本的改革を実現する'
            },
            {
                'company_name': 'Holoway Co., Ltd.',
                'initial_investment': 'Early',
                'category': 'Frontier',
                'website': 'holoway.co.jp',
                'description': 'デジタルホログラフィ技術を活用した革新的な精密測定・検査技術により半導体・宇宙等のモノづくりのフロンティアを切り開く'
            },
            {
                'company_name': 'Acompany Co., Ltd.',
                'initial_investment': 'Early',
                'category': 'Business',
                'website': 'acompany.tech',
                'description': '秘密計算技術を活用したデータセキュリティソリューションを提供し、あらゆるデータとAI活用が信頼できるデータ社会の実現を目指す'
            },
            {
                'company_name': 'Hakki Africa Limited',
                'initial_investment': 'Growth',
                'category': 'Consumer',
                'website': 'hakki-africa.com',
                'description': 'グローバルサウスで有担保オートローン事業を展開し誰もが車を所有できる社会の実現を目指す'
            },
            {
                'company_name': 'Oceanic Constellations, Inc.',
                'initial_investment': 'Seed',
                'category': 'Frontier',
                'website': 'oceanic-constellations.com',
                'description': '水上ドローン船と制御ソフトウェアから成るインフラの開発・製造を通じて、「海のみえる化」を実現する'
            },
            {
                'company_name': 'ZettaJoule, Inc.',
                'initial_investment': 'Seed',
                'category': 'Frontier',
                'website': 'zetta-joule.com',
                'description': '日本が誇る高温ガス炉技術によるクリーンエネルギーの供給を通じ、グローバルの次世代産業インフラをアップデートする'
            },
            {
                'company_name': 'emol inc.',
                'initial_investment': 'Early',
                'category': 'Frontier',
                'website': 'emol.jp',
                'description': '治療用アプリの開発と医療サービスの提供を通じてメンタルヘルス医療を当たり前にする'
            },
            {
                'company_name': 'TAIAN, Inc.',
                'initial_investment': 'Early',
                'category': 'Business',
                'website': 'taian-inc.com',
                'description': 'バンケット事業者 (婚礼・法人宴会)向けAll-in-one SaaSブライダル・バンケット事業DXを起点に、祝い事から個人・企業の繋がりをエンパワーメントさせる'
            },
            {
                'company_name': 'Tensor Energy Inc.',
                'initial_investment': 'Seed',
                'category': 'Business',
                'website': 'tensorenergy.jp',
                'description': '再生可能エネルギー発電所と蓄電池の財務と電力の管理を一気通貫で行うクラウドプラットフォームで電力ビジネスを変革する'
            },
            {
                'company_name': 'Knowhere.Inc',
                'initial_investment': 'Seed',
                'category': 'Business, Consumer',
                'website': 'knowhere.co.jp',
                'description': 'スマートフォンでの投打のAIボール解析を提供し、野球界のデータインフラ構築を目指す'
            },
            {
                'company_name': 'YOUTRUST, Inc.',
                'initial_investment': 'Early',
                'category': 'Business',
                'website': 'youtrust.co.jp',
                'description': 'キャリアSNS×HRテックプラットフォーム事業を通じて、日本の人材流動性を高め日本経済のモメンタムを上げることを目指す'
            },
            {
                'company_name': 'UTAITE Co., Ltd.',
                'initial_investment': 'Seed',
                'category': 'Consumer',
                'website': 'utaite.co.jp',
                'description': '「2.5次元」エンターテイメントIPの開発・運営を通じて、日本発の新しいエンタメジャンルの確立を目指す'
            },
            {
                'company_name': 'Logomix Inc.',
                'initial_investment': 'Early',
                'category': 'Frontier',
                'website': 'logomix.bio',
                'description': '独自の大規模ゲノム編集技術を用いたスマートセル設計・構築プラットフォームを提供することで、バイオモノ作り・医療の高度化と脱炭素を推進する'
            },
            {
                'company_name': 'Autify Inc.',
                'initial_investment': 'Early',
                'category': 'Business',
                'website': 'autify.com',
                'description': 'ソフトウェアテストの自動化プラットフォーム「Autify」を通じ、世界中の開発組織の生産性向上を図る'
            },
            {
                'company_name': 'medicalforce Inc.',
                'initial_investment': 'Early',
                'category': 'Business',
                'website': 'corp.medical-force.com',
                'description': '自由診療向けオールインワンSaaS「medicalforce」を通じて、業界の生産性向上と価値最大化を実現する'
            },
            {
                'company_name': 'newmo, Inc.',
                'initial_investment': 'Seed',
                'category': 'Consumer',
                'website': 'newmo.me',
                'description': 'タクシー・ライドシェアサービスの運営を通じて、日常や観光需要を支える交通インフラを目指す'
            },
            {
                'company_name': 'Medii, Inc.',
                'initial_investment': 'Early',
                'category': 'Business',
                'website': 'medii.jp',
                'description': '医師情報交換プラットフォーム運営＆製薬企業向けマーケティング支援を通して、希少疾患や診断困難症例の診療を推進し、誰も取り残さない医療の実現を目指す'
            },
            {
                'company_name': 'Facilo Co., Ltd',
                'initial_investment': 'Early',
                'category': 'Business',
                'website': 'facilo.jp',
                'description': '住宅売買仲介SaaS「Facilo」を活用したコミュニケーション円滑化や業務効率化により住宅売買体験の向上を目指す'
            },
            {
                'company_name': 'AnotherBall Pte. Ltd.',
                'initial_investment': 'Seed',
                'category': 'Consumer',
                'website': 'izumo.com',
                'description': 'VTuberライブ配信プラットフォーム"AniLive"の運営を通じて、オタクライフを世界中に浸透させる'
            },
            {
                'company_name': 'Helpfeel Inc.',
                'initial_investment': 'Growth',
                'category': 'Business',
                'website': 'corp.helpfeel.com',
                'description': '高度な検索技術を持つFAQシステム「Helpfeel」を起点に、カスタマーサポートDXで顧客体験をアップデート'
            }
        ]

        return companies_data

    def scrape_globis_portfolio(self):
        """Extract GLOBIS Capital Partners portfolio from website content"""
        logger.info("Extracting GLOBIS Capital Partners portfolio from website content")

        # Extract portfolio companies
        portfolio_companies = self.extract_companies_from_website_content()

        # Store results
        result = {
            'vc_name': 'GLOBIS Capital Partners',
            'vc_url': 'https://www.globiscapital.co.jp/ja/companies#all',
            'portfolio_companies': portfolio_companies,
            'total_companies_found': len(portfolio_companies)
        }

        self.results.append(result)

        logger.info(f"Found {len(portfolio_companies)} portfolio companies")

    def save_results(self, output_file='globis_portfolio_database.json'):
        """Save results to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def create_excel_report(self, output_file='globis_portfolio_database.xlsx'):
        """Create Excel report with GLOBIS portfolio company data"""
        try:
            # Prepare data for Excel
            excel_data = []
            for result in self.results:
                vc_info = {
                    'VC_Name': result['vc_name'],
                    'VC_URL': result['vc_url'],
                    'Total_Companies_Found': result['total_companies_found']
                }

                if result['portfolio_companies']:
                    for company in result['portfolio_companies']:
                        row = vc_info.copy()
                        row['Company_Name'] = company['company_name']
                        row['Initial_Investment'] = company['initial_investment']
                        row['Category'] = company['category']
                        row['Website'] = company['website']
                        row['Description'] = company['description']
                        excel_data.append(row)
                else:
                    # Add row even if no companies found
                    vc_info['Company_Name'] = ''
                    vc_info['Initial_Investment'] = ''
                    vc_info['Category'] = ''
                    vc_info['Website'] = ''
                    vc_info['Description'] = ''
                    excel_data.append(vc_info)

            # Create DataFrame and save to Excel
            df = pd.DataFrame(excel_data)
            df.to_excel(output_file, index=False)
            logger.info(f"Excel report saved to {output_file}")

        except Exception as e:
            logger.error(f"Error creating Excel report: {e}")

def main():
    extractor = GlobisPortfolioExtractor()

    # Extract GLOBIS Capital Partners portfolio
    extractor.scrape_globis_portfolio()

    # Save results
    extractor.save_results()
    extractor.create_excel_report()

    # Print summary
    if extractor.results:
        result = extractor.results[0]
        logger.info(f"Extraction completed!")
        logger.info(f"VC: {result['vc_name']}")
        logger.info(f"Total portfolio companies found: {result['total_companies_found']}")

        # Print first few companies as example
        logger.info("Sample companies found:")
        for i, company in enumerate(result['portfolio_companies'][:5]):
            logger.info(f"  {i+1}. {company['company_name']} - {company['initial_investment']} - {company['category']}")

if __name__ == "__main__":
    main()
