import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin, urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VCPortfolioExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.results = []

    def load_vc_data(self, csv_file, limit=None):
        """Load VC data from CSV file"""
        try:
            # Read CSV with proper encoding and skip the first 2 rows (headers)
            df = pd.read_csv(csv_file, encoding='utf-8', skiprows=2)
            logger.info(f"Loaded {len(df)} rows from CSV file")

            # Extract VC information
            vc_data = []
            count = 0
            for index, row in df.iterrows():
                if limit and count >= limit:
                    break

                # Check if we have valid data
                if pd.notna(row.iloc[2]) and pd.notna(row.iloc[3]):  # URL and VC name columns
                    vc_url = str(row.iloc[2]).strip()
                    vc_name = str(row.iloc[3]).strip()

                    # Skip if URL is invalid
                    if vc_url == '#N/A' or vc_url == 'nan' or not vc_url.startswith('http'):
                        continue

                    # Extract additional information with correct column indices
                    vc_data.append({
                        'vc_id': row.iloc[1] if pd.notna(row.iloc[1]) else '',
                        'vc_name': vc_name,
                        'vc_url': vc_url,
                        'location': row.iloc[9] if pd.notna(row.iloc[9]) else '',  # Location column
                        'year_founded': row.iloc[7] if pd.notna(row.iloc[7]) else '',  # Year Founded column
                        'affiliation_type': row.iloc[8] if pd.notna(row.iloc[8]) else '',  # Affiliation Type column
                        'example_investments': row.iloc[13] if pd.notna(row.iloc[13]) else '',  # Example of Investments
                        'example_exits': row.iloc[14] if pd.notna(row.iloc[14]) else ''  # Example of Exits
                    })
                    count += 1

            logger.info(f"Extracted {len(vc_data)} VCs with valid URLs")
            return vc_data

        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return []

    def get_page_content(self, url, timeout=10):
        """Get page content with error handling"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def extract_portfolio_companies(self, html_content, vc_name, vc_url):
        """Extract portfolio companies from HTML content"""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        companies = []

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Look for portfolio companies in various ways
        portfolio_patterns = [
            # Common portfolio page patterns
            'portfolio', 'investments', 'companies', 'startups',
            'portfolio-companies', 'investment-portfolio', 'our-companies',
            'portfolio companies', 'investment companies', 'our investments'
        ]

        # First, try to find portfolio-specific sections
        portfolio_sections = []
        for pattern in portfolio_patterns:
            # Use string parameter instead of deprecated text parameter
            elements = soup.find_all(string=re.compile(pattern, re.IGNORECASE))
            for element in elements:
                if element.parent:
                    portfolio_sections.append(element.parent)

        # Extract company names from portfolio sections
        for section in portfolio_sections:
            # Look for company names in links, headings, and text
            for element in section.find_all(['a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span']):
                text = element.get_text().strip()
                if self.is_likely_company_name(text):
                    companies.append({
                        'company_name': text,
                        'source_element': element.name,
                        'confidence': 'medium',
                        'source_section': 'portfolio'
                    })

        # If no portfolio sections found, extract from entire page
        if not companies:
            # Look for company names in the entire page
            for element in soup.find_all(['a', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = element.get_text().strip()
                if self.is_likely_company_name(text):
                    companies.append({
                        'company_name': text,
                        'source_element': element.name,
                        'confidence': 'low',
                        'source_section': 'general'
                    })

        # Remove duplicates and filter
        unique_companies = []
        seen = set()
        for company in companies:
            if company['company_name'] not in seen and len(company['company_name']) > 2:
                seen.add(company['company_name'])
                unique_companies.append(company)

        # Sort by confidence and length
        unique_companies.sort(key=lambda x: (x['confidence'] == 'low', len(x['company_name'])))

        return unique_companies[:30]  # Limit to top 30 potential companies

    def is_likely_company_name(self, text):
        """Check if text looks like a company name"""
        if not text or len(text) < 3 or len(text) > 50:
            return False

        # Skip common navigation and UI text
        skip_words = [
            'home', 'about', 'contact', 'portfolio', 'investments', 'news', 'blog',
            'privacy', 'terms', 'cookie', 'login', 'signup', 'search', 'menu',
            'copyright', 'all rights reserved', 'follow us', 'subscribe',
            'team', 'company', 'platform', 'information', 'mail magazine',
            'value', 'jaen', 'team', 'company', 'platform', 'information'
        ]

        text_lower = text.lower()
        for word in skip_words:
            if word in text_lower:
                return False

        # Check if it looks like a company name (contains letters and possibly numbers)
        if re.match(r'^[A-Za-z0-9\s&.,\-()]+$', text):
            # Should contain at least one letter
            if re.search(r'[A-Za-z]', text):
                # Additional checks for better filtering
                if len(text.split()) <= 5:  # Company names are usually short
                    return True

        return False

    def scrape_vc_portfolio(self, vc_data):
        """Scrape portfolio information for each VC"""
        for i, vc in enumerate(vc_data):
            logger.info(f"Processing VC {i+1}/{len(vc_data)}: {vc['vc_name']} ({vc['vc_url']})")

            # Get the main page
            html_content = self.get_page_content(vc['vc_url'])
            if not html_content:
                logger.warning(f"Could not fetch content for {vc['vc_name']}")
                continue

            # Extract portfolio companies
            portfolio_companies = self.extract_portfolio_companies(html_content, vc['vc_name'], vc['vc_url'])

            # Store results
            result = {
                'vc_id': vc['vc_id'],
                'vc_name': vc['vc_name'],
                'vc_url': vc['vc_url'],
                'location': vc['location'],
                'year_founded': vc['year_founded'],
                'affiliation_type': vc['affiliation_type'],
                'example_investments': vc['example_investments'],
                'example_exits': vc['example_exits'],
                'portfolio_companies': portfolio_companies,
                'total_companies_found': len(portfolio_companies)
            }

            self.results.append(result)

            # Add delay to be respectful to servers
            time.sleep(2)

    def save_results(self, output_file='vc_portfolio_database.json'):
        """Save results to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def create_excel_report(self, output_file='vc_portfolio_database.xlsx'):
        """Create Excel report with VC and portfolio company data"""
        try:
            # Prepare data for Excel
            excel_data = []
            for result in self.results:
                vc_info = {
                    'VC_ID': result['vc_id'],
                    'VC_Name': result['vc_name'],
                    'VC_URL': result['vc_url'],
                    'Location': result['location'],
                    'Year_Founded': result['year_founded'],
                    'Affiliation_Type': result['affiliation_type'],
                    'Example_Investments': result['example_investments'],
                    'Example_Exits': result['example_exits'],
                    'Total_Companies_Found': result['total_companies_found']
                }

                if result['portfolio_companies']:
                    for company in result['portfolio_companies']:
                        row = vc_info.copy()
                        row['Portfolio_Company'] = company['company_name']
                        row['Source_Element'] = company['source_element']
                        row['Confidence'] = company['confidence']
                        row['Source_Section'] = company['source_section']
                        excel_data.append(row)
                else:
                    # Add row even if no companies found
                    vc_info['Portfolio_Company'] = ''
                    vc_info['Source_Element'] = ''
                    vc_info['Confidence'] = ''
                    vc_info['Source_Section'] = ''
                    excel_data.append(vc_info)

            # Create DataFrame and save to Excel
            df = pd.DataFrame(excel_data)
            df.to_excel(output_file, index=False)
            logger.info(f"Excel report saved to {output_file}")

        except Exception as e:
            logger.error(f"Error creating Excel report: {e}")

def main():
    extractor = VCPortfolioExtractor()

    # Load VC data from CSV (limit to 10 for testing)
    vc_data = extractor.load_vc_data('Dissertation - VC list probided by startup db.csv', limit=10)

    if not vc_data:
        logger.error("No VC data found. Please check the CSV file.")
        return

    # Scrape portfolio information
    extractor.scrape_vc_portfolio(vc_data)

    # Save results
    extractor.save_results()
    extractor.create_excel_report()

    # Print summary
    total_vcs = len(extractor.results)
    total_companies = sum(result['total_companies_found'] for result in extractor.results)

    logger.info(f"Extraction completed!")
    logger.info(f"Total VCs processed: {total_vcs}")
    logger.info(f"Total portfolio companies found: {total_companies}")

if __name__ == "__main__":
    main()
