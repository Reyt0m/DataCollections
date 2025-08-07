#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full extraction script for all researchers with improved data extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from researchmap_integrated_scraper import ResearchMapIntegratedScraper
import logging
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_full_extraction(search_url=None, max_researchers=None, output_prefix="full_extraction"):
    """Run the improved extraction on all researchers"""

    scraper = ResearchMapIntegratedScraper()

    # Default search URL for 株式会社 researchers
    if not search_url:
        search_url = "https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE&lang=en"

    print("=== Full Researcher Extraction with Improved Data Extraction ===")
    print(f"Search URL: {search_url}")
    if max_researchers:
        print(f"Max researchers to process: {max_researchers}")
    else:
        print("Processing all researchers found")

    try:
        # Run the comprehensive scraper
        result = scraper.scrape_all_researchers_and_projects(
            search_url=search_url,
            max_researchers=max_researchers
        )

        print(f"\n=== Extraction Results Summary ===")
        print(f"Total researchers found: {result['total_researchers']}")
        print(f"Processed researchers: {result['processed_researchers']}")
        print(f"Total competitive projects: {result['total_competitive_projects']}")

        # Calculate statistics
        total_projects = sum(len(researcher.get('all_projects', [])) for researcher in result['researchers'])
        total_keywords = sum(len(researcher.get('research_keywords', [])) for researcher in result['researchers'])
        total_areas = sum(len(researcher.get('research_areas', [])) for researcher in result['researchers'])
        total_affiliations = sum(len(researcher.get('all_affiliations', [])) for researcher in result['researchers'])

        print(f"\n=== Data Extraction Statistics ===")
        print(f"Total research projects: {total_projects}")
        print(f"Total research keywords: {total_keywords}")
        print(f"Total research areas: {total_areas}")
        print(f"Total affiliations: {total_affiliations}")

        # Show sample data for first few researchers
        print(f"\n=== Sample Data (First 3 Researchers) ===")
        for i, researcher in enumerate(result['researchers'][:3], 1):
            print(f"\nResearcher {i}: {researcher.get('name', 'Unknown')}")
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
        json_file = f"{output_prefix}_results.json"
        scraper.save_results(result, json_file)
        print(f"\nResults saved to: {json_file}")

        # Export to Excel
        excel_file = f"{output_prefix}_results.xlsx"
        scraper.export_to_excel(result, excel_file)
        print(f"Excel file saved to: {excel_file}")

        print("\n=== Full Extraction Completed Successfully ===")

        return result

    except Exception as e:
        logger.error(f"Full extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    parser = argparse.ArgumentParser(description='Run full researcher extraction with improved data extraction')
    parser.add_argument('--search-url', type=str, help='Search URL for researchers')
    parser.add_argument('--max-researchers', type=int, help='Maximum number of researchers to process')
    parser.add_argument('--output-prefix', type=str, default='full_extraction', help='Output file prefix')

    args = parser.parse_args()

    result = run_full_extraction(
        search_url=args.search_url,
        max_researchers=args.max_researchers,
        output_prefix=args.output_prefix
    )

    if result:
        print(f"\nExtraction completed successfully!")
        print(f"Processed {result['processed_researchers']} researchers")
        print(f"Found {result['total_competitive_projects']} competitive projects")
    else:
        print(f"\nExtraction failed!")

if __name__ == "__main__":
    main()
