import json
import csv
import pandas as pd
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VCPortfolioWithFunding:
    def __init__(self):
        self.vc_list = []
        self.integrated_data = []
        self.final_output = []

    def normalize_vc_name(self, vc_name):
        """Normalize VC name for better matching"""
        if not vc_name:
            return ""

        # Remove common suffixes and prefixes
        normalized = vc_name.strip()
        normalized = re.sub(r'\s*\([^)]*\)', '', normalized)  # Remove parentheses content
        normalized = re.sub(r'\s*Inc\.?', '', normalized)
        normalized = re.sub(r'\s*LLC', '', normalized)
        normalized = re.sub(r'\s*Ltd\.?', '', normalized)
        normalized = re.sub(r'\s*Co\.?', '', normalized)
        normalized = re.sub(r'\s*Corp\.?', '', normalized)
        normalized = re.sub(r'\s*株式会社', '', normalized)
        normalized = re.sub(r'\s*有限会社', '', normalized)
        normalized = re.sub(r'\s*合同会社', '', normalized)
        normalized = re.sub(r'\s*PTE\.?', '', normalized)
        normalized = re.sub(r'\s*LTD\.?', '', normalized)

        # Remove extra spaces and convert to lowercase
        normalized = re.sub(r'\s+', ' ', normalized).strip().lower()

        return normalized

    def find_matching_vc(self, vc_name, vc_list):
        """Find matching VC in the list using fuzzy matching"""
        normalized_target = self.normalize_vc_name(vc_name)

        best_match = None
        best_score = 0

        for vc in vc_list:
            normalized_list_name = self.normalize_vc_name(vc['vc_name'])

            # Exact match
            if normalized_target == normalized_list_name:
                return vc

            # Partial match
            if normalized_target in normalized_list_name or normalized_list_name in normalized_target:
                score = len(set(normalized_target) & set(normalized_list_name)) / len(set(normalized_target) | set(normalized_list_name))
                if score > best_score:
                    best_score = score
                    best_match = vc

        # Return best match if score is above threshold
        if best_score > 0.2:  # Lowered threshold for better matching
            return best_match

        return None

    def load_vc_list(self, csv_file='Dissertation - VC list probided by startup db.csv'):
        """Load VC list from CSV file"""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            # Filter only active VCs (marked with 'o' in first column)
            active_vcs = df[df.iloc[:, 0] == 'o'].copy()

            # Clean and process VC data
            for _, row in active_vcs.iterrows():
                # Fix: Use correct column for VC name (column 3, index 2)
                vc_name = row.iloc[2] if pd.notna(row.iloc[2]) else ''
                vc_url = row.iloc[1] if pd.notna(row.iloc[1]) else ''

                vc_data = {
                    'vc_name': vc_name,
                    'vc_url': vc_url,
                    'investment_stages': {
                        'seed': '◎' if row.iloc[3] == '◎' else '〇' if row.iloc[3] == '〇' else '',
                        'early': '◎' if row.iloc[4] == '◎' else '〇' if row.iloc[4] == '〇' else '',
                        'middle_growth': '◎' if row.iloc[5] == '◎' else '〇' if row.iloc[5] == '〇' else '',
                        'later': '◎' if row.iloc[6] == '◎' else '〇' if row.iloc[6] == '〇' else ''
                    },
                    'year_founded': row.iloc[7] if pd.notna(row.iloc[7]) else '',
                    'affiliation_type': row.iloc[8] if pd.notna(row.iloc[8]) else '',
                    'location': row.iloc[9] if pd.notna(row.iloc[9]) else '',
                    'ticket_size': row.iloc[10] if pd.notna(row.iloc[10]) else '',
                    'target_geographies': row.iloc[11] if pd.notna(row.iloc[11]) else '',
                    'monthly_deals': row.iloc[12] if pd.notna(row.iloc[12]) else '',
                    'investment_areas': {
                        'health_bio': row.iloc[15] if pd.notna(row.iloc[15]) else '',
                        'lifestyle': row.iloc[16] if pd.notna(row.iloc[16]) else '',
                        'media_ad': row.iloc[17] if pd.notna(row.iloc[17]) else '',
                        'legacy': row.iloc[18] if pd.notna(row.iloc[18]) else '',
                        'frontier': row.iloc[19] if pd.notna(row.iloc[19]) else '',
                        'finance': row.iloc[20] if pd.notna(row.iloc[20]) else '',
                        'enterprise': row.iloc[21] if pd.notna(row.iloc[21]) else '',
                        'other': row.iloc[22] if pd.notna(row.iloc[22]) else ''
                    }
                }
                self.vc_list.append(vc_data)

            logger.info(f"Loaded {len(self.vc_list)} active VCs from CSV")
            return True
        except Exception as e:
            logger.error(f"Error loading VC list: {e}")
            return False

    def load_integrated_data(self, json_file='integrated_vc_database.json'):
        """Load integrated VC database"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.integrated_data = json.load(f)
            logger.info(f"Loaded {len(self.integrated_data)} integrated company records")
            return True
        except FileNotFoundError:
            logger.warning(f"Integrated database file {json_file} not found. Continuing without existing data.")
            return False
        except Exception as e:
            logger.error(f"Error loading integrated data: {e}")
            return False

    def search_prtimes_funding(self, company_name):
        """Search for funding information on Prtimes for a specific company"""
        try:
            # Create search URL for Prtimes
            search_url = f"https://prtimes.jp/main/search.php?q={company_name}+調達"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract funding articles (this is a simplified version)
            articles = []
            article_elements = soup.find_all('div', class_='list-article')

            for element in article_elements[:3]:  # Limit to first 3 articles
                title_element = element.find('h3')
                link_element = element.find('a')

                if title_element and link_element:
                    title = title_element.get_text(strip=True)
                    url = link_element.get('href')

                    # Check if it's a funding-related article
                    if any(keyword in title.lower() for keyword in ['調達', '資金', '投資', 'funding', 'investment']):
                        articles.append({
                            'article_title': title,
                            'article_url': f"https://prtimes.jp{url}" if url.startswith('/') else url,
                            'funding_amount': self.extract_funding_amount(title),
                            'article_content': ''
                        })

            return articles

        except Exception as e:
            logger.warning(f"Error searching Prtimes for {company_name}: {e}")
            return []

    def extract_funding_amount(self, title):
        """Extract funding amount from article title"""
        # Common funding amount patterns
        patterns = [
            r'(\d+億円)',
            r'(\d+万円)',
            r'(\d+万ドル)',
            r'(\d+億ドル)',
            r'(\d+\.\d+億円)',
            r'(\d+\.\d+万円)'
        ]

        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1)

        return ''

    def create_comprehensive_portfolio(self):
        """Create comprehensive portfolio with VC list and funding information"""
        comprehensive_data = []

        # Group companies by VC for better matching
        vc_companies = {}
        for company in self.integrated_data:
            vc_name = company['vc_name']
            if vc_name not in vc_companies:
                vc_companies[vc_name] = []
            vc_companies[vc_name].append(company)

        # Process each VC from the list
        for vc in self.vc_list:
            vc_name = vc['vc_name']

            # Find matching companies for this VC
            matching_companies = []

            # Try exact match first
            if vc_name in vc_companies:
                matching_companies = vc_companies[vc_name]
                logger.info(f"Exact match found for '{vc_name}'")
            else:
                # Try fuzzy matching
                for integrated_vc_name, companies in vc_companies.items():
                    if self.find_matching_vc(integrated_vc_name, [vc]):
                        matching_companies = companies
                        logger.info(f"Fuzzy match: '{integrated_vc_name}' -> '{vc_name}'")
                        break

            if not matching_companies:
                # If no companies found, create a basic entry
                comprehensive_data.append({
                    'vc_name': vc_name,
                    'vc_url': vc['vc_url'],
                    'investment_stages': vc['investment_stages'],
                    'year_founded': vc['year_founded'],
                    'affiliation_type': vc['affiliation_type'],
                    'location': vc['location'],
                    'ticket_size': vc['ticket_size'],
                    'target_geographies': vc['target_geographies'],
                    'monthly_deals': vc['monthly_deals'],
                    'investment_areas': vc['investment_areas'],
                    'portfolio_companies': [],
                    'total_portfolio_companies': 0,
                    'companies_with_funding': 0,
                    'total_funding_articles': 0
                })
            else:
                # Process companies for this VC
                portfolio_companies = []
                total_funding_articles = 0
                companies_with_funding = 0

                for company in matching_companies:
                    # Search for additional funding information on Prtimes
                    prtimes_articles = self.search_prtimes_funding(company['company_name'])

                    # Combine existing and new funding articles
                    all_funding_articles = company['funding_articles'] + prtimes_articles

                    company_data = {
                        'company_name': company['company_name'],
                        'initial_investment': company['initial_investment'],
                        'category': company['category'],
                        'website': company['website'],
                        'description': company['description'],
                        'funding_articles': all_funding_articles,
                        'total_funding_articles': len(all_funding_articles)
                    }

                    portfolio_companies.append(company_data)

                    if len(all_funding_articles) > 0:
                        companies_with_funding += 1
                        total_funding_articles += len(all_funding_articles)

                    # Add delay to avoid overwhelming the server
                    time.sleep(1)

                comprehensive_data.append({
                    'vc_name': vc_name,
                    'vc_url': vc['vc_url'],
                    'investment_stages': vc['investment_stages'],
                    'year_founded': vc['year_founded'],
                    'affiliation_type': vc['affiliation_type'],
                    'location': vc['location'],
                    'ticket_size': vc['ticket_size'],
                    'target_geographies': vc['target_geographies'],
                    'monthly_deals': vc['monthly_deals'],
                    'investment_areas': vc['investment_areas'],
                    'portfolio_companies': portfolio_companies,
                    'total_portfolio_companies': len(portfolio_companies),
                    'companies_with_funding': companies_with_funding,
                    'total_funding_articles': total_funding_articles
                })

        self.final_output = comprehensive_data
        return comprehensive_data

    def save_to_json(self, filename='vc_portfolio_final_fixed.json'):
        """Save comprehensive portfolio data to JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.final_output, f, ensure_ascii=False, indent=2)
            logger.info(f"Comprehensive portfolio data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}")

    def save_to_csv(self, filename='vc_portfolio_final_fixed.csv'):
        """Save comprehensive portfolio data to CSV"""
        try:
            csv_data = []

            for vc in self.final_output:
                # Base VC information
                base_row = {
                    'VC_Name': vc['vc_name'],
                    'VC_URL': vc['vc_url'],
                    'Investment_Stages_Seed': vc['investment_stages']['seed'],
                    'Investment_Stages_Early': vc['investment_stages']['early'],
                    'Investment_Stages_Middle_Growth': vc['investment_stages']['middle_growth'],
                    'Investment_Stages_Later': vc['investment_stages']['later'],
                    'Year_Founded': vc['year_founded'],
                    'Affiliation_Type': vc['affiliation_type'],
                    'Location': vc['location'],
                    'Ticket_Size': vc['ticket_size'],
                    'Target_Geographies': vc['target_geographies'],
                    'Monthly_Deals': vc['monthly_deals'],
                    'Investment_Areas_Health_Bio': vc['investment_areas']['health_bio'],
                    'Investment_Areas_Lifestyle': vc['investment_areas']['lifestyle'],
                    'Investment_Areas_Media_Ad': vc['investment_areas']['media_ad'],
                    'Investment_Areas_Legacy': vc['investment_areas']['legacy'],
                    'Investment_Areas_Frontier': vc['investment_areas']['frontier'],
                    'Investment_Areas_Finance': vc['investment_areas']['finance'],
                    'Investment_Areas_Enterprise': vc['investment_areas']['enterprise'],
                    'Investment_Areas_Other': vc['investment_areas']['other'],
                    'Total_Portfolio_Companies': vc['total_portfolio_companies'],
                    'Companies_With_Funding': vc['companies_with_funding'],
                    'Total_Funding_Articles': vc['total_funding_articles']
                }

                # Add company information
                portfolio_companies = vc.get('portfolio_companies', [])
                if portfolio_companies:
                    for i, company in enumerate(portfolio_companies):
                        row = base_row.copy()
                        row['Company_Number'] = i + 1
                        row['Company_Name'] = company['company_name']
                        row['Initial_Investment'] = company['initial_investment']
                        row['Category'] = company['category']
                        row['Website'] = company['website']
                        row['Description'] = company['description']
                        row['Company_Funding_Articles'] = company['total_funding_articles']

                        # Add funding article details
                        funding_articles = company.get('funding_articles', [])
                        if funding_articles:
                            for j, article in enumerate(funding_articles):
                                article_row = row.copy()
                                article_row['Funding_Article_Number'] = j + 1
                                article_row['Article_Title'] = article.get('article_title', '')
                                article_row['Article_URL'] = article.get('article_url', '')
                                article_row['Funding_Amount'] = article.get('funding_amount', '')
                                article_row['Article_Content'] = article.get('article_content', '')[:500]
                                csv_data.append(article_row)
                        else:
                            # Add row even if no funding articles
                            row['Funding_Article_Number'] = ''
                            row['Article_Title'] = ''
                            row['Article_URL'] = ''
                            row['Funding_Amount'] = ''
                            row['Article_Content'] = ''
                            csv_data.append(row)
                else:
                    # Add row for VC with no portfolio companies
                    base_row['Company_Number'] = ''
                    base_row['Company_Name'] = ''
                    base_row['Initial_Investment'] = ''
                    base_row['Category'] = ''
                    base_row['Website'] = ''
                    base_row['Description'] = ''
                    base_row['Company_Funding_Articles'] = ''
                    base_row['Funding_Article_Number'] = ''
                    base_row['Article_Title'] = ''
                    base_row['Article_URL'] = ''
                    base_row['Funding_Amount'] = ''
                    base_row['Article_Content'] = ''
                    csv_data.append(base_row)

            # Save to CSV
            df = pd.DataFrame(csv_data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"Comprehensive portfolio data saved to {filename}")

        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")

    def create_summary_report(self):
        """Create a summary report of the comprehensive portfolio"""
        summary = {
            'total_vcs': len(self.final_output),
            'vcs_with_portfolio': len([vc for vc in self.final_output if vc['total_portfolio_companies'] > 0]),
            'total_companies': sum(vc['total_portfolio_companies'] for vc in self.final_output),
            'companies_with_funding': sum(vc['companies_with_funding'] for vc in self.final_output),
            'total_funding_articles': sum(vc['total_funding_articles'] for vc in self.final_output),
            'investment_stages_distribution': {},
            'affiliation_types': {},
            'locations': {}
        }

        # Count distributions
        for vc in self.final_output:
            # Investment stages
            for stage, value in vc['investment_stages'].items():
                if value:
                    summary['investment_stages_distribution'][stage] = summary['investment_stages_distribution'].get(stage, 0) + 1

            # Affiliation types
            aff_type = vc['affiliation_type']
            if aff_type:
                summary['affiliation_types'][aff_type] = summary['affiliation_types'].get(aff_type, 0) + 1

            # Locations
            location = vc['location']
            if location:
                summary['locations'][location] = summary['locations'].get(location, 0) + 1

        return summary

def main():
    portfolio_creator = VCPortfolioWithFunding()

    # Load VC list
    logger.info("Loading VC list from CSV...")
    if not portfolio_creator.load_vc_list():
        logger.error("Failed to load VC list. Exiting.")
        return

    # Load integrated data
    logger.info("Loading integrated VC database...")
    portfolio_creator.load_integrated_data()

    # Create comprehensive portfolio
    logger.info("Creating comprehensive portfolio with funding information...")
    comprehensive_data = portfolio_creator.create_comprehensive_portfolio()

    # Save outputs
    portfolio_creator.save_to_json()
    portfolio_creator.save_to_csv()

    # Create and display summary
    summary = portfolio_creator.create_summary_report()

    logger.info("=== COMPREHENSIVE VC PORTFOLIO SUMMARY ===")
    logger.info(f"Total VCs: {summary['total_vcs']}")
    logger.info(f"VCs with portfolio: {summary['vcs_with_portfolio']}")
    logger.info(f"Total companies: {summary['total_companies']}")
    logger.info(f"Companies with funding info: {summary['companies_with_funding']}")
    logger.info(f"Total funding articles: {summary['total_funding_articles']}")

    logger.info("\nInvestment Stages Distribution:")
    for stage, count in summary['investment_stages_distribution'].items():
        logger.info(f"  {stage}: {count}")

    logger.info("\nAffiliation Types:")
    for aff_type, count in summary['affiliation_types'].items():
        logger.info(f"  {aff_type}: {count}")

    logger.info("\nTop Locations:")
    sorted_locations = sorted(summary['locations'].items(), key=lambda x: x[1], reverse=True)
    for location, count in sorted_locations[:10]:
        logger.info(f"  {location}: {count}")

    logger.info("\nComprehensive portfolio creation completed successfully!")

if __name__ == "__main__":
    main()
