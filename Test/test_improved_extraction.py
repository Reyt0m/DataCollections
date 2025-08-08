#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for improved extraction methods
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from researchmap_integrated_scraper import ResearchMapIntegratedScraper
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_extraction_methods():
    """Test the improved extraction methods with sample HTML"""

    scraper = ResearchMapIntegratedScraper()

    # Test with the sample HTML file
    sample_file = "samples/兼松 秀行 (Hideyuki Kanematsu) - マイポータル - researchmap.html"

    if not os.path.exists(sample_file):
        logger.error(f"Sample file not found: {sample_file}")
        return

    try:
        with open(sample_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        print("=== Testing Improved Extraction Methods ===")

        # Test research keywords extraction
        print("\n1. Testing Research Keywords Extraction:")
        keywords = scraper._extract_research_keywords(soup)
        print(f"Found {len(keywords)} keywords:")
        for i, keyword in enumerate(keywords, 1):
            print(f"  {i}. {keyword}")

        # Test research areas extraction
        print("\n2. Testing Research Areas Extraction:")
        areas = scraper._extract_research_areas(soup)
        print(f"Found {len(areas)} research areas:")
        for i, area in enumerate(areas, 1):
            print(f"  {i}. {area}")

        # Test affiliations extraction
        print("\n3. Testing Affiliations Extraction:")
        affiliations = scraper._extract_affiliations(soup)
        print(f"Found {len(affiliations)} affiliations:")
        for i, affiliation in enumerate(affiliations, 1):
            print(f"  {i}. {affiliation}")

        # Debug: Check if profile section exists
        profile_section = soup.find('div', {'id': 'profile'})
        print(f"Profile section found: {profile_section is not None}")
        if profile_section:
            affiliation_dt = profile_section.find('dt', string='所属')
            print(f"Affiliation dt found: {affiliation_dt is not None}")
            if affiliation_dt:
                dd = affiliation_dt.find_next_sibling('dd')
                print(f"Affiliation dd found: {dd is not None}")
                if dd:
                    print(f"DD text: {dd.get_text().strip()}")

        # Debug: Check dl elements
        dl_elements = soup.find_all('dl', class_='rm-cv-basic-dl')
        print(f"Found {len(dl_elements)} dl elements")
        for i, dl in enumerate(dl_elements):
            dt_elements = dl.find_all('dt')
            print(f"DL {i}: Found {len(dt_elements)} dt elements")
            for dt in dt_elements:
                text = dt.get_text().strip()
                print(f"  DT text: '{text}'")
                if text == '所属':
                    print(f"    Found affiliation dt!")
                    dd = dt.find_next_sibling('dd')
                    if dd:
                        print(f"    DD text: '{dd.get_text().strip()}'")

        # Test projects extraction (this would require a projects page)
        print("\n4. Testing Projects Extraction:")
        researcher_url = "https://researchmap.jp/hidekanematsu"
        all_projects = scraper._extract_all_projects(researcher_url)
        print(f"Found {len(all_projects)} projects:")
        for i, project in enumerate(all_projects, 1):
            print(f"  {i}. {project.get('title', 'No title')}")
            print(f"     Funding: {project.get('funding_system', 'N/A')}")
            print(f"     Competitive: {project.get('is_competitive', False)}")

        competitive_projects = scraper._extract_competitive_projects(all_projects)
        print(f"Found {len(competitive_projects)} competitive projects")

        print("\n=== Extraction Test Completed ===")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extraction_methods()
