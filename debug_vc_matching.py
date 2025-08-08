import json
import pandas as pd
import re

def normalize_vc_name(vc_name):
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

# Load CSV data
df = pd.read_csv('Dissertation - VC list probided by startup db.csv', encoding='utf-8')
active_vcs = df[df.iloc[:, 0] == 'o'].copy()

# Load JSON data
with open('integrated_vc_database.json', 'r', encoding='utf-8') as f:
    integrated_data = json.load(f)

# Get unique VC names from integrated data
integrated_vc_names = set()
for company in integrated_data:
    integrated_vc_names.add(company['vc_name'])

print("=== VC Name Matching Debug ===")
print(f"Total VCs in CSV: {len(active_vcs)}")
print(f"Total VCs in integrated data: {len(integrated_vc_names)}")
print()

print("=== CSV VC Names (first 10) ===")
for i, row in active_vcs.head(10).iterrows():
    vc_name = row.iloc[2] if pd.notna(row.iloc[2]) else ''
    normalized = normalize_vc_name(vc_name)
    print(f"Original: '{vc_name}' -> Normalized: '{normalized}'")
print()

print("=== Integrated Data VC Names ===")
for vc_name in integrated_vc_names:
    normalized = normalize_vc_name(vc_name)
    print(f"Original: '{vc_name}' -> Normalized: '{normalized}'")
print()

print("=== Matching Attempts ===")
for i, row in active_vcs.head(5).iterrows():
    csv_vc_name = row.iloc[2] if pd.notna(row.iloc[2]) else ''
    csv_normalized = normalize_vc_name(csv_vc_name)

    print(f"\nTrying to match CSV VC: '{csv_vc_name}' (normalized: '{csv_normalized}')")

    for integrated_vc_name in integrated_vc_names:
        integrated_normalized = normalize_vc_name(integrated_vc_name)

        if csv_normalized == integrated_normalized:
            print(f"  ✓ EXACT MATCH: '{integrated_vc_name}'")
        elif csv_normalized in integrated_normalized or integrated_normalized in csv_normalized:
            print(f"  ~ PARTIAL MATCH: '{integrated_vc_name}' (normalized: '{integrated_normalized}')")
        else:
            # Calculate similarity score
            common_chars = len(set(csv_normalized) & set(integrated_normalized))
            total_chars = len(set(csv_normalized) | set(integrated_normalized))
            if total_chars > 0:
                similarity = common_chars / total_chars
                if similarity > 0.3:
                    print(f"  ? SIMILARITY ({similarity:.2f}): '{integrated_vc_name}' (normalized: '{integrated_normalized}')")
