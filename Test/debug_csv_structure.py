import pandas as pd

def debug_csv_structure():
    # Read CSV with proper encoding and skip the first 2 rows (headers)
    df = pd.read_csv('Dissertation - VC list probided by startup db.csv', encoding='utf-8', skiprows=2)

    print("CSV Structure Analysis")
    print("=" * 50)
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print("\nColumn names:")
    for i, col in enumerate(df.columns):
        print(f"Column {i}: {col}")

    print("\nFirst few rows:")
    for i in range(min(5, len(df))):
        print(f"\nRow {i}:")
        for j in range(min(15, len(df.columns))):
            value = df.iloc[i, j] if pd.notna(df.iloc[i, j]) else "N/A"
            print(f"  Column {j}: {value}")

    # Check specific columns for the first few VCs
    print("\nVC Data Analysis:")
    for i in range(min(5, len(df))):
        if pd.notna(df.iloc[i, 2]) and pd.notna(df.iloc[i, 3]):
            print(f"\nVC {i+1}:")
            print(f"  ID: {df.iloc[i, 1]}")
            print(f"  URL: {df.iloc[i, 2]}")
            print(f"  Name: {df.iloc[i, 3]}")
            print(f"  Year Founded: {df.iloc[i, 7] if pd.notna(df.iloc[i, 7]) else 'N/A'}")
            print(f"  Affiliation Type: {df.iloc[i, 8] if pd.notna(df.iloc[i, 8]) else 'N/A'}")
            print(f"  Location: {df.iloc[i, 9] if pd.notna(df.iloc[i, 9]) else 'N/A'}")
            print(f"  Example Investments: {df.iloc[i, 13] if pd.notna(df.iloc[i, 13]) else 'N/A'}")
            print(f"  Example Exits: {df.iloc[i, 14] if pd.notna(df.iloc[i, 14]) else 'N/A'}")

if __name__ == "__main__":
    debug_csv_structure()
