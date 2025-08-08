#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for projects extraction
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

def test_projects_extraction():
    """Test the projects extraction with sample HTML"""

    scraper = ResearchMapIntegratedScraper()

    # Test with the sample research projects HTML file
    sample_file = "samples/兼松 秀行 (Hideyuki Kanematsu) - 共同研究・競争的資金等の研究課題 - researchmap.html"

    if not os.path.exists(sample_file):
        logger.error(f"Sample file not found: {sample_file}")
        return

    try:
        with open(sample_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        print("=== Testing Projects Extraction ===")

        # Test the extraction logic directly
        project_items = soup.find_all('li', class_='list-group-item')
        print(f"Found {len(project_items)} project items")

        projects = []
        for i, item in enumerate(project_items, 1):
            project = {}

            # Extract title
            title_link = item.find('a', class_='rm-cv-list-title')
            if title_link:
                project['title'] = title_link.get_text().strip()
                project['project_url'] = title_link.get('href')

            # Extract funding system
            divs = item.find_all('div')
            for div in divs:
                # タイトルリンクを含まないdivを探す
                if not div.find('a') and not div.get('class') or 'rm-cv-list-author' not in div.get('class', []):
                    funding_text = div.get_text().strip()
                    if funding_text and funding_text != project.get('title', ''):
                        project['funding_system'] = funding_text
                        break

            # Extract researchers
            author_div = item.find('div', class_='rm-cv-list-author')
            if author_div:
                project['researchers'] = author_div.get_text().strip()

            # Check if competitive
            project['is_competitive'] = scraper.is_competitive_funding_by_html_structure(
                project.get('funding_system', ''),
                project.get('institution', ''),
                project.get('project_type', '')
            )

            if project.get('title'):
                projects.append(project)
                print(f"\nProject {i}:")
                print(f"  Title: {project.get('title', 'N/A')}")
                print(f"  Funding: {project.get('funding_system', 'N/A')}")
                print(f"  Researchers: {project.get('researchers', 'N/A')}")
                print(f"  Competitive: {project.get('is_competitive', False)}")

        # Test competitive projects filtering
        competitive_projects = [p for p in projects if p.get('is_competitive', False)]
        print(f"\nTotal projects: {len(projects)}")
        print(f"Competitive projects: {len(competitive_projects)}")

        print("\n=== Projects Extraction Test Completed ===")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_projects_extraction()
