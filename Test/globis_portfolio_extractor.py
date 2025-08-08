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

    def extract_company_info_from_div(self, div_element):
        """Extract company information from a div element"""
        company_info = {
            'company_name': '',
            'initial_investment': '',
            'category': '',
            'website': '',
            'description': ''
        }

        # Get all text content from the div
        text_content = div_element.get_text(strip=True)

        # Look for company name (usually the first part before any special characters)
        lines = text_content.split('\n')
        if lines:
            # First line is usually the company name
            company_info['company_name'] = lines[0].strip()

        # Look for website URL
        links = div_element.find_all('a', href=True)
        for link in links:
            href = link.get('href', '').strip()
            if href and (href.startswith('http') or href.startswith('www')):
                company_info['website'] = href
                break

        # Extract other information from text content
        # Look for patterns like "Seed", "Early", "Growth", "Consumer", "Business", "Frontier"
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

        # Extract description (usually after the company name)
        if len(lines) > 1:
            # Join remaining lines as description
            description_lines = [line.strip() for line in lines[1:] if line.strip()]
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

        # Look for li elements that contain div elements with company information
        li_elements = soup.find_all('li')

        for li in li_elements:
            # Find div elements within li
            div_elements = li.find_all('div')

            for div in div_elements:
                # Check if this div contains company information
                text_content = div.get_text(strip=True)

                # Skip if it's navigation or common UI elements
                skip_words = ['menu', 'navigation', 'header', 'footer', 'copyright', 'privacy']
                if any(word in text_content.lower() for word in skip_words):
                    continue

                # Check if it looks like company information (contains company-like text)
                if len(text_content) > 10 and not text_content.isdigit():
                    company_info = self.extract_company_info_from_div(div)

                    # Only add if we have a company name
                    if company_info['company_name'] and len(company_info['company_name']) > 2:
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
