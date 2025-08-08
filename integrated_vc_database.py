import json
import csv
import pandas as pd
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VCPortfolioWithFunding:
    def __init__(self, headless=True, timeout=10):
        self.vc_list = []
        self.integrated_data = []
        self.final_output = []
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Portfolio keywords for finding portfolio pages
        self.portfolio_keywords = [
            'portfolio', 'ポートフォリオ', '投資先', '企業', 'パートナー',
            'investments', 'companies', 'partners', 'clients',
            'investment', 'invest', '出資先', '投資企業', '投資実績',
            'portfolio companies', 'portfolio companies', '投資対象企業'
        ]

        # Initialize Selenium driver
        self._initialize_driver()

    def _initialize_driver(self):
        """Initialize Selenium driver"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')

            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_page_load_timeout(self.timeout)
                self.driver.implicitly_wait(10)
                logger.info("Selenium driver initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize with WebDriver Manager: {e}")
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    self.driver.set_page_load_timeout(self.timeout)
                    self.driver.implicitly_wait(10)
                    logger.info("Selenium driver initialized with system ChromeDriver")
                except Exception as e2:
                    logger.error(f"Failed to initialize Selenium driver: {e2}")
                    self.driver = None

        except Exception as e:
            logger.error(f"Selenium driver initialization failed: {e}")
            self.driver = None

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
        if best_score > 0.2:
            return best_match

        return None

    def load_vc_list(self, csv_file='Dissertation - VC list probided by startup db.csv'):
        """Load VC list from CSV file"""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            active_vcs = df[df.iloc[:, 0] == 'o'].copy()

            for _, row in active_vcs.iterrows():
                vc_name = row.iloc[3] if pd.notna(row.iloc[3]) else ''
                vc_url = row.iloc[2] if pd.notna(row.iloc[2]) else ''

                vc_data = {
                    'vc_name': vc_name,
                    'vc_url': vc_url,
                    'investment_stages': {
                        'seed': '◎' if row.iloc[4] == '◎' else '〇' if row.iloc[4] == '〇' else '',
                        'early': '◎' if row.iloc[5] == '◎' else '〇' if row.iloc[5] == '〇' else '',
                        'middle_growth': '◎' if row.iloc[6] == '◎' else '〇' if row.iloc[6] == '〇' else '',
                        'later': '◎' if row.iloc[7] == '◎' else '〇' if row.iloc[7] == '〇' else ''
                    },
                    'year_founded': row.iloc[8] if pd.notna(row.iloc[8]) else '',
                    'affiliation_type': row.iloc[9] if pd.notna(row.iloc[9]) else '',
                    'location': row.iloc[10] if pd.notna(row.iloc[10]) else '',
                    'ticket_size': row.iloc[11] if pd.notna(row.iloc[11]) else '',
                    'target_geographies': row.iloc[12] if pd.notna(row.iloc[12]) else '',
                    'monthly_deals': row.iloc[13] if pd.notna(row.iloc[13]) else '',
                    'investment_areas': {
                        'health_bio': row.iloc[16] if pd.notna(row.iloc[16]) else '',
                        'lifestyle': row.iloc[17] if pd.notna(row.iloc[17]) else '',
                        'media_ad': row.iloc[18] if pd.notna(row.iloc[18]) else '',
                        'legacy': row.iloc[19] if pd.notna(row.iloc[19]) else '',
                        'frontier': row.iloc[20] if pd.notna(row.iloc[20]) else '',
                        'finance': row.iloc[21] if pd.notna(row.iloc[21]) else '',
                        'enterprise': row.iloc[22] if pd.notna(row.iloc[22]) else '',
                        'other': row.iloc[23] if pd.notna(row.iloc[23]) else ''
                    }
                }
                self.vc_list.append(vc_data)

            logger.info(f"Loaded {len(self.vc_list)} active VCs from CSV")
            return True
        except Exception as e:
            logger.error(f"Error loading VC list: {e}")
            return False

    def load_integrated_data(self, json_file='integrated_vc_database.json'):
        """Load existing integrated data"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.integrated_data = json.load(f)
            logger.info(f"Loaded {len(self.integrated_data)} integrated company records")
            return True
        except FileNotFoundError:
            logger.warning(f"Integrated data file {json_file} not found. Starting with empty data.")
            self.integrated_data = []
            return True
        except Exception as e:
            logger.error(f"Error loading integrated data: {e}")
            return False

    def find_portfolio_tab(self, soup, base_url):
        """Find portfolio tab in the page"""
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text().lower()

            for keyword in self.portfolio_keywords:
                if keyword in href or keyword in text:
                    portfolio_url = urljoin(base_url, link['href'])
                    logger.info(f"Found portfolio tab: {portfolio_url}")
                    return portfolio_url

        # Check if current page is portfolio page
        current_url = base_url.lower()
        for keyword in self.portfolio_keywords:
            if keyword in current_url:
                logger.info(f"Current page is portfolio page: {base_url}")
                return base_url

        return None

    def extract_companies_from_page(self, soup, base_url=""):
        """Extract company names from page"""
        companies = set()

        # Portfolio-specific selectors
        portfolio_selectors = [
            '.fg-item-title',  # 15th Rock
            '.card_companyName__BWs6G',  # ANRI
            '.portfolioItem__title',  # サムライインキュベート
            '.portfolio__item',  # ジェネシア
            '[class*="company-name"]',
            '[class*="companyName"]',
            '[class*="fg-item-title"]',
            '[class*="card_companyName"]',
            '[class*="portfolio-item"]',
            '[class*="portfolioItem"]',
            'h2.fg-item-title',
            'h3.card_companyName__BWs6G',
            '.portfolio-item h2',
            '.portfolio-item h3',
            '.company-card h2',
            '.company-card h3',
            '.card h2',
            '.card h3',
            '.gallery-item h2',
            '.gallery-item h3',
            '.portfolio__item h3',
            '.portfolio__item h2'
        ]

        for selector in portfolio_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 1 and len(text) < 100:
                    clean_text = re.sub(r'[🇯🇵🇺🇸🇳🇱🇨🇦🇬🇧🇺🇸🇳🇱]', '', text).strip()
                    if clean_text:
                        companies.add(clean_text)

        # Extract from links
        link_selectors = [
            'a[href*="http"]',
            '.card a',
            '.portfolio-item a',
            '.company-card a',
            '.gallery-item a',
            '.portfolio__item a'
        ]

        for selector in link_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 1 and len(text) < 100:
                    clean_text = re.sub(r'[🇯🇵🇺🇸🇳🇱🇨🇦🇬🇧🇺🇸🇳🇱]', '', text).strip()
                    if clean_text:
                        companies.add(clean_text)

        # Extract from images alt text
        img_elements = soup.find_all('img')
        for img in img_elements:
            alt_text = img.get('alt', '')
            if alt_text and len(alt_text) > 1 and len(alt_text) < 100:
                if any(keyword in alt_text.lower() for keyword in ['logo', 'company', 'corp', 'inc', 'ltd', '株式会社', '有限会社']):
                    clean_text = re.sub(r'[🇯🇵🇺🇸🇳🇱🇨🇦🇬🇧🇺🇸🇳🇱]', '', alt_text).strip()
                    if clean_text:
                        companies.add(clean_text)

        return companies

    def scrape_with_requests(self, url):
        """Scrape with requests"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            logger.error(f"Failed to get HTML with requests: {url} - {e}")
            return None

    def scrape_with_selenium(self, url):
        """Scrape with Selenium"""
        if not self.driver:
            logger.error("Selenium driver not available")
            return None

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            return BeautifulSoup(self.driver.page_source, 'lxml')
        except Exception as e:
            logger.error(f"Failed to get HTML with Selenium: {url} - {e}")
            return None

    def scrape_vc_portfolio(self, vc_data):
        """Scrape portfolio for a specific VC"""
        vc_name = vc_data['vc_name']
        vc_url = vc_data['vc_url']

        if not vc_url:
            logger.warning(f"No URL for VC: {vc_name}")
            return []

        logger.info(f"Scraping portfolio for VC: {vc_name} - {vc_url}")

        # Try requests first
        soup = self.scrape_with_requests(vc_url)
        if not soup:
            # Try Selenium if requests fails
            soup = self.scrape_with_selenium(vc_url)
            if not soup:
                logger.error(f"Failed to scrape VC: {vc_name}")
                return []

        # Find portfolio tab
        portfolio_url = self.find_portfolio_tab(soup, vc_url)
        if portfolio_url:
            # Scrape portfolio page
            portfolio_soup = self.scrape_with_requests(portfolio_url)
            if not portfolio_soup:
                portfolio_soup = self.scrape_with_selenium(portfolio_url)

            if portfolio_soup:
                companies = self.extract_companies_from_page(portfolio_soup, portfolio_url)
                logger.info(f"Found {len(companies)} companies for {vc_name}")
                return list(companies)
            else:
                logger.error(f"Failed to scrape portfolio page for {vc_name}")
                return []
        else:
            # Try to extract companies from current page
            companies = self.extract_companies_from_page(soup, vc_url)
            logger.info(f"Found {len(companies)} companies from current page for {vc_name}")
            return list(companies)

    def search_prtimes_funding(self, company_name):
        """Search for funding information on Prtimes"""
        try:
            # Search URL for Prtimes
            search_url = f"https://prtimes.jp/topics/keywords/{company_name}"
            response = self.session.get(search_url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                articles = []

                # Extract articles
                article_elements = soup.find_all('article') or soup.find_all('div', class_='article')

                for article in article_elements[:5]:  # Limit to 5 articles
                    title_elem = article.find('h3') or article.find('h2') or article.find('a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if any(keyword in title.lower() for keyword in ['調達', 'funding', 'investment', '出資', '投資']):
                            link_elem = article.find('a')
                            link = link_elem.get('href') if link_elem else ''
                            if link and not link.startswith('http'):
                                link = urljoin('https://prtimes.jp', link)

                            funding_amount = self.extract_funding_amount(title)

                            articles.append({
                                'article_title': title,
                                'article_url': link,
                                'funding_amount': funding_amount
                            })

                return articles
            else:
                logger.debug(f"Prtimes search returned status {response.status_code} for {company_name}")
                return []

        except Exception as e:
            logger.debug(f"Error searching Prtimes for {company_name}: {e}")
            return []

    def extract_funding_amount(self, title):
        """Extract funding amount from article title"""
        # Common funding amount patterns
        patterns = [
            r'(\d+(?:\.\d+)?)\s*億円',
            r'(\d+(?:\.\d+)?)\s*千万円',
            r'(\d+(?:\.\d+)?)\s*百万円',
            r'(\d+(?:\.\d+)?)\s*万円',
            r'(\d+(?:\.\d+)?)\s*億',
            r'(\d+(?:\.\d+)?)\s*千万',
            r'(\d+(?:\.\d+)?)\s*百万',
            r'(\d+(?:\.\d+)?)\s*万',
            r'(\d+(?:\.\d+)?)\s*億円',
            r'(\d+(?:\.\d+)?)\s*千万円',
            r'(\d+(?:\.\d+)?)\s*百万円',
            r'(\d+(?:\.\d+)?)\s*万円'
        ]

        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(0)

        return ""

    def create_comprehensive_portfolio(self):
        """Create comprehensive portfolio with funding information"""
        logger.info("Creating comprehensive portfolio...")

        # Process each VC
        for vc in self.vc_list:
            vc_name = vc['vc_name']
            vc_url = vc['vc_url']

            logger.info(f"Processing VC: {vc_name}")

            # Check if we already have data for this VC
            existing_companies = [item for item in self.integrated_data if item['vc_name'] == vc_name]

            if existing_companies:
                logger.info(f"Found {len(existing_companies)} existing companies for {vc_name}")
                self.final_output.extend(existing_companies)
            else:
                # Scrape portfolio for this VC
                companies = self.scrape_vc_portfolio(vc)

                if companies:
                    logger.info(f"Scraped {len(companies)} companies for {vc_name}")

                    for company_name in companies:
                        # Search for funding information
                        funding_articles = self.search_prtimes_funding(company_name)

                        company_data = {
                            'vc_name': vc_name,
                            'vc_url': vc_url,
                            'company_name': company_name,
                            'initial_investment': '',  # Will be filled if available
                            'category': '',  # Will be filled if available
                            'website': '',  # Will be filled if available
                            'description': '',  # Will be filled if available
                            'funding_articles': funding_articles,
                            'total_funding_articles': len(funding_articles)
                        }

                        self.final_output.append(company_data)

                        # Add delay to avoid overwhelming servers
                        time.sleep(1)
                else:
                    logger.warning(f"No companies found for {vc_name}")

        logger.info(f"Comprehensive portfolio creation completed. Total companies: {len(self.final_output)}")

    def save_to_json(self, filename='vc_portfolio_comprehensive.json'):
        """Save results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.final_output, f, ensure_ascii=False, indent=2)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")

    def save_to_csv(self, filename='vc_portfolio_comprehensive.csv'):
        """Save results to CSV file"""
        try:
            # Flatten the data for CSV
            csv_data = []
            for item in self.final_output:
                base_row = {
                    'vc_name': item['vc_name'],
                    'vc_url': item['vc_url'],
                    'company_name': item['company_name'],
                    'initial_investment': item['initial_investment'],
                    'category': item['category'],
                    'website': item['website'],
                    'description': item['description'],
                    'total_funding_articles': item['total_funding_articles']
                }

                # Add funding articles
                funding_articles = item.get('funding_articles', [])
                if funding_articles:
                    for i, article in enumerate(funding_articles):
                        row = base_row.copy()
                        row['funding_article_number'] = i + 1
                        row['article_title'] = article.get('article_title', '')
                        row['article_url'] = article.get('article_url', '')
                        row['funding_amount'] = article.get('funding_amount', '')
                        csv_data.append(row)
                else:
                    base_row['funding_article_number'] = ''
                    base_row['article_title'] = ''
                    base_row['article_url'] = ''
                    base_row['funding_amount'] = ''
                    csv_data.append(base_row)

            df = pd.DataFrame(csv_data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")

    def create_summary_report(self):
        """Create summary report"""
        total_companies = len(self.final_output)
        vcs_with_companies = len(set(item['vc_name'] for item in self.final_output))
        companies_with_funding = len([item for item in self.final_output if item['total_funding_articles'] > 0])
        total_funding_articles = sum(item['total_funding_articles'] for item in self.final_output)

        summary = {
            'total_companies': total_companies,
            'vcs_with_companies': vcs_with_companies,
            'companies_with_funding_info': companies_with_funding,
            'total_funding_articles': total_funding_articles,
            'vcs_processed': len(self.vc_list)
        }

        logger.info("=== COMPREHENSIVE VC PORTFOLIO SUMMARY ===")
        logger.info(f"Total VCs processed: {summary['vcs_processed']}")
        logger.info(f"VCs with portfolio companies: {summary['vcs_with_companies']}")
        logger.info(f"Total companies found: {summary['total_companies']}")
        logger.info(f"Companies with funding info: {summary['companies_with_funding_info']}")
        logger.info(f"Total funding articles: {summary['total_funding_articles']}")

        return summary

    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        self.session.close()
        logger.info("Resources cleaned up")

def main():
    """Main function"""
    vc_portfolio = VCPortfolioWithFunding(headless=True, timeout=20)

    try:
        # Load VC list
        if not vc_portfolio.load_vc_list():
            logger.error("Failed to load VC list")
            return

        # Load existing integrated data
        vc_portfolio.load_integrated_data()

        # Create comprehensive portfolio
        vc_portfolio.create_comprehensive_portfolio()

        # Save results
        vc_portfolio.save_to_json()
        vc_portfolio.save_to_csv()

        # Create summary
        summary = vc_portfolio.create_summary_report()

        logger.info("Comprehensive VC portfolio creation completed successfully!")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Error in main process: {e}")
    finally:
        vc_portfolio.close()

if __name__ == "__main__":
    main()
