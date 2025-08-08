import requests
from bs4 import BeautifulSoup
import json
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GlobisPortfolioExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.results = []

    def get_page_content(self, url, timeout=10):
        """Get page content with error handling"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def extract_company_info_from_text(self, text_content):
        """Extract company information from text content"""
        company_info = {
            'company_name': '',
            'initial_investment': '',
            'category': '',
            'website': '',
            'description': ''
        }

        # Split by lines and clean up
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]

        if not lines:
            return company_info

        # First line is usually the company name
        company_info['company_name'] = lines[0]

        # Look for investment stages and categories in the text
        investment_stages = ['Seed', 'Early', 'Growth']
        categories = ['Consumer', 'Business', 'Frontier']

        for stage in investment_stages:
            if stage in text_content:
                company_info['initial_investment'] = stage
                break

        for category in categories:
            if category in text_content:
                company_info['category'] = category
                break

        # Extract description (remaining text after company name)
        if len(lines) > 1:
            description_lines = lines[1:]
            company_info['description'] = ' '.join(description_lines)

        return company_info

    def extract_portfolio_companies(self, html_content):
        """Extract portfolio companies from GLOBIS Capital Partners page"""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        companies = []

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Based on the website structure, look for company information
        # The companies seem to be listed in a structured format

        # Look for elements that might contain company information
        # Try different selectors based on the website structure

        # Method 1: Look for elements with company-like patterns
        company_patterns = [
            # Look for elements containing company names followed by descriptions
            r'([A-Z][a-zA-Z0-9\s&.,\-()]+)->([^->]+)',
            # Look for elements with investment stages
            r'(Seed|Early|Growth)',
            # Look for elements with categories
            r'(Consumer|Business|Frontier)'
        ]

        # Method 2: Look for specific HTML structure
        # Based on the website content, companies seem to be in a list format

        # Look for all text content that might contain company information
        all_text = soup.get_text()

        # Split by potential company entries
        # Look for patterns like "Company Name->Description"
        company_entries = re.findall(r'([A-Z][a-zA-Z0-9\s&.,\-()]+)->([^->]+)', all_text)

        for company_name, description in company_entries:
            if len(company_name.strip()) > 3:  # Filter out very short names
                company_info = {
                    'company_name': company_name.strip(),
                    'initial_investment': '',
                    'category': '',
                    'website': '',
                    'description': description.strip()
                }

                # Extract investment stage and category from description
                if 'Seed' in description:
                    company_info['initial_investment'] = 'Seed'
                elif 'Early' in description:
                    company_info['initial_investment'] = 'Early'
                elif 'Growth' in description:
                    company_info['initial_investment'] = 'Growth'

                if 'Consumer' in description:
                    company_info['category'] = 'Consumer'
                elif 'Business' in description:
                    company_info['category'] = 'Business'
                elif 'Frontier' in description:
                    company_info['category'] = 'Frontier'

                companies.append(company_info)

        # Method 3: Look for specific HTML elements that might contain company data
        # Look for elements with class names or IDs that might indicate company listings
        company_elements = soup.find_all(['div', 'li', 'p'], class_=re.compile(r'company|portfolio|investment', re.I))

        for element in company_elements:
            text_content = element.get_text(strip=True)
            if len(text_content) > 20:  # Only process substantial text
                company_info = self.extract_company_info_from_text(text_content)
                if company_info['company_name'] and len(company_info['company_name']) > 3:
                    companies.append(company_info)

        # Remove duplicates based on company name
        unique_companies = []
        seen_names = set()

        for company in companies:
            if company['company_name'] not in seen_names:
                seen_names.add(company['company_name'])
                unique_companies.append(company)

        return unique_companies

    def scrape_globis_portfolio(self, url):
        """Scrape GLOBIS Capital Partners portfolio"""
        logger.info(f"Scraping GLOBIS Capital Partners portfolio from: {url}")

        # Get the page content
        html_content = self.get_page_content(url)
        if not html_content:
            logger.error("Could not fetch GLOBIS Capital Partners page")
            return

        # Extract portfolio companies
        portfolio_companies = self.extract_portfolio_companies(html_content)

        # Store results
        result = {
            'vc_name': 'GLOBIS Capital Partners',
            'vc_url': url,
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
            import pandas as pd

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

    # Scrape GLOBIS Capital Partners portfolio
    globis_url = 'https://www.globiscapital.co.jp/ja/companies#all'
    extractor.scrape_globis_portfolio(globis_url)

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
