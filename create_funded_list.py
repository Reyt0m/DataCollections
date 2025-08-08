import pandas as pd
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_empty_or_no_investor(value):
    """
    Check if a value indicates no investor or is empty

    Args:
        value: The value to check

    Returns:
        bool: True if the value indicates no investor, False otherwise
    """
    if pd.isna(value) or value == '':
        return True

    # Convert to string and normalize
    value_str = str(value).strip().lower()

    # Patterns that indicate no investor
    no_investor_patterns = [
        'なし', 'ない', 'そんざいしない', 'わからない', '不明', '未定',
        'na', 'none', 'n/a', 'unknown', 'undecided', 'tbd',
        '0', '0%', '0.0', '0.00',
        '無し', '無い', '存在しない', '分からない',
        '該当なし', '該当無し', '該当ない',
        '未回答', '未入力', '空白',
        '特になし', '特にない', '特に無し',
        '投資なし', '投資ない', '投資無し',
        '出資なし', '出資ない', '出資無し',
        '資本なし', '資本ない', '資本無し'
    ]

    # Check if the value matches any no-investor pattern
    for pattern in no_investor_patterns:
        if pattern in value_str:
            return True

    # Check if the value is just whitespace or very short (likely empty)
    if len(value_str) <= 2 and not value_str.isdigit():
        return True

    return False

def has_investor(row, investor_columns):
    """
    Check if a company has any investors

    Args:
        row: DataFrame row
        investor_columns: List of investor column names

    Returns:
        bool: True if the company has at least one investor, False otherwise
    """
    for col in investor_columns:
        value = row[col]
        if not is_empty_or_no_investor(value):
            # Check if the value contains meaningful investor information
            value_str = str(value).strip()

            # Skip if it's just a percentage or number without context
            if re.match(r'^[\d.,\s%]+$', value_str):
                continue

            # If it's not empty and doesn't indicate "no investor", consider it as having an investor
            if len(value_str) > 0 and not is_empty_or_no_investor(value_str):
                return True

    return False

def create_funded_list(input_file, output_file):
    """
    Create a funded list by filtering out companies without investors

    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file
    """
    try:
        # Read the CSV file
        logger.info(f"Reading input file: {input_file}")
        df = pd.read_csv(input_file, encoding='utf-8')

        logger.info(f"Total companies in input file: {len(df)}")

        # Define investor columns
        investor_columns = [
            '国内エンジェル',
            '国内VC（事業会社系）',
            '国内VC（大学系）',
            '国内VC（その他）',
            '国内事業会社',
            '国内銀行',
            '国内大学',
            '国内その他',
            '海外エンジェル',
            '海外VC（事業会社系）',
            '海外VC（大学系）',
            '海外VC（その他）',
            '海外事業会社',
            '海外銀行',
            '海外大学',
            '海外その他',
            '資本構成_12調整用その他(国内海外問わず円グラフはこちら入力）',
            '資本構成_リードインベスタ名'
        ]

        # Check which columns exist in the dataframe
        existing_investor_columns = [col for col in investor_columns if col in df.columns]
        logger.info(f"Found {len(existing_investor_columns)} investor columns: {existing_investor_columns}")

        # Filter companies that have investors
        funded_companies = []
        removed_companies = []

        for index, row in df.iterrows():
            company_name = row.get('企業名', f'Company_{index}')

            if has_investor(row, existing_investor_columns):
                funded_companies.append(row)
                logger.debug(f"Company '{company_name}' has investors - KEEPING")
            else:
                removed_companies.append(company_name)
                logger.debug(f"Company '{company_name}' has no investors - REMOVING")

        # Create new dataframe with funded companies
        funded_df = pd.DataFrame(funded_companies)

        # Save the funded list
        funded_df.to_csv(output_file, index=False, encoding='utf-8-sig')

        logger.info(f"Funded list created successfully!")
        logger.info(f"Total companies in funded list: {len(funded_df)}")
        logger.info(f"Companies removed (no investors): {len(removed_companies)}")
        logger.info(f"Output saved to: {output_file}")

        # Log some examples of removed companies
        if removed_companies:
            logger.info(f"Examples of removed companies (no investors): {removed_companies[:5]}")

        # Log some examples of kept companies
        if funded_companies:
            kept_examples = [row.get('企業名', 'Unknown') for row in funded_companies[:5]]
            logger.info(f"Examples of kept companies (with investors): {kept_examples}")

        return funded_df, removed_companies

    except Exception as e:
        logger.error(f"Error creating funded list: {e}")
        return None, None

def main():
    """Main function"""
    input_file = 'Dissertation - METI provided Academia Startup List.csv'
    output_file = 'METI_Funded_Startup_List.csv'

    logger.info("Starting to create funded list from METI provided academia startup list...")

    # Create funded list
    funded_df, removed_companies = create_funded_list(input_file, output_file)

    if funded_df is not None:
        logger.info("=== FUNDED LIST CREATION SUMMARY ===")
        logger.info(f"Input file: {input_file}")
        logger.info(f"Output file: {output_file}")
        logger.info(f"Total companies processed: {len(funded_df) + len(removed_companies)}")
        logger.info(f"Companies with investors (kept): {len(funded_df)}")
        logger.info(f"Companies without investors (removed): {len(removed_companies)}")
        logger.info(f"Success rate: {len(funded_df)/(len(funded_df) + len(removed_companies))*100:.1f}%")

        # Save removed companies list for reference
        if removed_companies:
            removed_df = pd.DataFrame({'企業名': removed_companies})
            removed_df.to_csv('METI_Removed_Companies_No_Investors.csv', index=False, encoding='utf-8-sig')
            logger.info(f"Removed companies list saved to: METI_Removed_Companies_No_Investors.csv")
    else:
        logger.error("Failed to create funded list")

if __name__ == "__main__":
    main()
