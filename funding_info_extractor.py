import requests
from bs4 import BeautifulSoup
import json
import logging
import re
import time
import pandas as pd
from urllib.parse import quote

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FundingInfoExtractor:
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

    def search_company_on_prtimes(self, company_name):
        """Search for company on PR TIMES"""
        # URL encode the company name for search
        encoded_name = quote(company_name)
        search_url = f"https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word={encoded_name}&lang=en"

        logger.info(f"Searching for {company_name} on PR TIMES: {search_url}")

        html_content = self.get_page_content(search_url)
        if not html_content:
            return []

        return self.extract_funding_articles(html_content, company_name)

    def extract_funding_articles(self, html_content, company_name):
        """Extract funding-related articles from PR TIMES search results"""
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []

        # Look for articles that contain funding-related keywords
        funding_keywords = ['調達', '資金調達', '投資', 'シリーズ', 'ラウンド', '億円', '万円', '兆円']

        # Find all article links
        article_links = soup.find_all('a', href=True)

        for link in article_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Check if this is a funding-related article
            if any(keyword in text for keyword in funding_keywords):
                # Extract funding amount from title
                funding_amount = self.extract_funding_amount(text)

                if funding_amount:
                    article_info = {
                        'company_name': company_name,
                        'article_title': text,
                        'article_url': href,
                        'funding_amount': funding_amount,
                        'article_content': ''
                    }

                    # Get article content if URL is valid
                    if href.startswith('http'):
                        article_content = self.get_article_content(href)
                        if article_content:
                            article_info['article_content'] = article_content

                    articles.append(article_info)

        return articles

    def extract_funding_amount(self, text):
        """Extract funding amount from text"""
        # Patterns for funding amounts
        patterns = [
            r'総額(\d+(?:\.\d+)?)(億円|万円|兆円)',
            r'(\d+(?:\.\d+)?)(億円|万円|兆円)の資金調達',
            r'(\d+(?:\.\d+)?)(億円|万円|兆円)を調達',
            r'調達額(\d+(?:\.\d+)?)(億円|万円|兆円)',
            r'(\d+(?:\.\d+)?)(億円|万円|兆円)の投資'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount = match.group(1)
                unit = match.group(2)
                return f"{amount}{unit}"

        return None

    def get_article_content(self, url):
        """Get article content from PR TIMES article page"""
        html_content = self.get_page_content(url)
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract article content
        # Look for common article content containers
        content_selectors = [
            'article',
            '.article-content',
            '.content',
            '.main-content',
            'main'
        ]

        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(strip=True)

        # If no specific content found, get all text
        return soup.get_text(strip=True)

    def process_portfolio_companies(self, portfolio_data):
        """Process portfolio companies to extract funding information"""
        all_funding_info = []

        for vc_data in portfolio_data:
            vc_name = vc_data.get('vc_name', '')
            portfolio_companies = vc_data.get('portfolio_companies', [])

            logger.info(f"Processing {len(portfolio_companies)} companies for {vc_name}")

            for company in portfolio_companies:
                company_name = company.get('company_name', '')
                if company_name:
                    logger.info(f"Searching funding info for: {company_name}")

                    # Search for funding information
                    funding_articles = self.search_company_on_prtimes(company_name)

                    for article in funding_articles:
                        article['vc_name'] = vc_name
                        all_funding_info.append(article)

                    # Add delay to be respectful to servers
                    time.sleep(2)

        return all_funding_info

    def save_results(self, funding_info, output_file='funding_info_database.json'):
        """Save funding information to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(funding_info, f, ensure_ascii=False, indent=2)
            logger.info(f"Funding information saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving funding information: {e}")

    def create_excel_report(self, funding_info, output_file='funding_info_database.xlsx'):
        """Create Excel report with funding information"""
        try:
            # Prepare data for Excel
            excel_data = []
            for article in funding_info:
                row = {
                    'VC_Name': article.get('vc_name', ''),
                    'Company_Name': article.get('company_name', ''),
                    'Article_Title': article.get('article_title', ''),
                    'Article_URL': article.get('article_url', ''),
                    'Funding_Amount': article.get('funding_amount', ''),
                    'Article_Content': article.get('article_content', '')[:1000]  # Limit content length
                }
                excel_data.append(row)

            # Create DataFrame and save to Excel
            df = pd.DataFrame(excel_data)
            df.to_excel(output_file, index=False)
            logger.info(f"Excel report saved to {output_file}")

        except Exception as e:
            logger.error(f"Error creating Excel report: {e}")

def main():
    extractor = FundingInfoExtractor()

    # Load existing portfolio data
    try:
        with open('globis_portfolio_database.json', 'r', encoding='utf-8') as f:
            portfolio_data = json.load(f)
    except FileNotFoundError:
        logger.error("Portfolio database not found. Please run the portfolio extractor first.")
        return

    # Process portfolio companies to extract funding information
    funding_info = extractor.process_portfolio_companies(portfolio_data)

    # Save results
    extractor.save_results(funding_info)
    extractor.create_excel_report(funding_info)

    # Print summary
    logger.info(f"Funding information extraction completed!")
    logger.info(f"Total funding articles found: {len(funding_info)}")

    # Print sample results
    logger.info("Sample funding articles found:")
    for i, article in enumerate(funding_info[:3]):
        logger.info(f"  {i+1}. {article['company_name']} - {article['funding_amount']} - {article['article_title']}")

if __name__ == "__main__":
    main()
