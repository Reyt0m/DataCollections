#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test script for the updated scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from researchmap_integrated_scraper import ResearchMapIntegratedScraper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_comprehensive_extraction():
    """Test the comprehensive extraction with a small sample"""

    scraper = ResearchMapIntegratedScraper()

    # Test with a small number of researchers
    search_url = "https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE"

    print("=== Testing Comprehensive Extraction ===")
    print(f"Search URL: {search_url}")

    try:
        # Run the scraper with max 2 researchers for testing
        result = scraper.scrape_all_researchers_and_projects(
            search_url=search_url,
            max_researchers=2
        )

        print(f"\nResults Summary:")
        print(f"Total researchers: {result['total_researchers']}")
        print(f"Processed researchers: {result['processed_researchers']}")
        print(f"Total competitive projects: {result['total_competitive_projects']}")

        print(f"\nDetailed Results:")
        for i, researcher in enumerate(result['researchers'], 1):
            print(f"\nResearcher {i}: {researcher.get('name', 'Unknown')}")
            print(f"  URL: {researcher.get('researcher_url', 'N/A')}")
            print(f"  Research Keywords: {len(researcher.get('research_keywords', []))} items")
            print(f"  Research Areas: {len(researcher.get('research_areas', []))} items")
            print(f"  All Affiliations: {len(researcher.get('all_affiliations', []))} items")
            print(f"  All Projects: {len(researcher.get('all_projects', []))} items")
            print(f"  Competitive Projects: {len(researcher.get('competitive_projects', []))} items")

            # Show some sample data
            if researcher.get('research_keywords'):
                print(f"    Sample keywords: {researcher['research_keywords'][:3]}")
            if researcher.get('research_areas'):
                print(f"    Sample areas: {researcher['research_areas'][:2]}")
            if researcher.get('all_affiliations'):
                print(f"    Sample affiliations: {researcher['all_affiliations'][:2]}")

        # Save results
        output_file = "test_comprehensive_results.json"
        scraper.save_results(result, output_file)
        print(f"\nResults saved to: {output_file}")

        # Export to Excel
        excel_file = "test_comprehensive_results.xlsx"
        scraper.export_to_excel(result, excel_file)
        print(f"Excel file saved to: {excel_file}")

        print("\n=== Test Completed Successfully ===")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comprehensive_extraction()
