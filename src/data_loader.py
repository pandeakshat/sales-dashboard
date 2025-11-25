import pandas as pd
import re

# Standard Concepts we look for
REQUIRED_CONCEPTS = {
    'Order Date': [r'(?i)order.*date', r'(?i)date'],
    'Sales': [r'(?i)sales', r'(?i)revenue', r'(?i)amount'],
    'Profit': [r'(?i)profit', r'(?i)earnings', r'(?i)net', r'(?i)margin'],
    'Quantity': [r'(?i)qty', r'(?i)quantity', r'(?i)units'], # Removed 'count' to avoid 'Country'
    'Category': [r'(?i)category', r'(?i)type'],
    'Sub-Category': [r'(?i)sub.*category', r'(?i)minor'],
    'Region': [r'(?i)region', r'(?i)area', r'(?i)zone'],
    'State': [r'(?i)state', r'(?i)province'],
    'City': [r'(?i)city', r'(?i)town'],
    'Discount': [r'(?i)discount', r'(?i)perc', r'(?i)off'],
    'Order ID': [r'(?i)order.*id', r'(?i)trans.*id']
}
def filter_data(df: pd.DataFrame, regions: list = None, categories: list = None, date_range: tuple = None) -> pd.DataFrame:
    """Applies filters to the dataframe."""
    filtered_df = df.copy()
    
    if regions:
        filtered_df = filtered_df[filtered_df['Region'].isin(regions)]
    
    if categories:
        filtered_df = filtered_df[filtered_df['Category'].isin(categories)]
        
    if date_range and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered_df = filtered_df[
            (filtered_df['Order Date'] >= start_date) & 
            (filtered_df['Order Date'] <= end_date)
        ]
        
    return filtered_df
def normalize_schema(df: pd.DataFrame) -> dict:
    """
    Scans the dataframe and maps columns to standard names.
    Priority: Exact Match > Regex Match.
    Prevents duplicates by ensuring 1-to-1 mapping.
    """
    df_columns = list(df.columns)
    col_mapping = {}  # {Original_Name : New_Standard_Name}
    
    found_concepts = set()
    used_original_cols = set()

    # 1. Priority Loop: Exact matches (Case Insensitive)
    # We loop through concepts first to prioritize "Concept Discovery"
    for concept in REQUIRED_CONCEPTS.keys():
        for col in df_columns:
            if col.lower() == concept.lower():
                col_mapping[col] = concept
                found_concepts.add(concept)
                used_original_cols.add(col)
                break # Found this concept, move to next

    # 2. Secondary Loop: Regex matches (Only for missing concepts)
    for concept, patterns in REQUIRED_CONCEPTS.items():
        if concept in found_concepts: 
            continue # Already found exactly
        
        for col in df_columns:
            if col in used_original_cols: 
                continue # Column already used
            
            # Check regex
            for pattern in patterns:
                if re.search(pattern, col):
                    col_mapping[col] = concept
                    found_concepts.add(concept)
                    used_original_cols.add(col)
                    break # Found match for this concept
            
            if concept in found_concepts: break

    # 3. Rename columns
    # We keep ALL columns, just rename the identified ones.
    clean_df = df.rename(columns=col_mapping)
    
    return {
        'df': clean_df,
        'found_cols': list(found_concepts),
        'missing_cols': [k for k in REQUIRED_CONCEPTS.keys() if k not in found_concepts]
    }

def assess_data_quality(df: pd.DataFrame) -> list:
    """Checks for Nulls and logical issues."""
    issues = []
    
    # Null Checks
    for col in df.columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            pct = (null_count / len(df)) * 100
            if pct > 5: # Only warn if significant
                issues.append(f"⚠️ **{col}**: {null_count} missing values ({pct:.1f}%)")

    # Logical Checks
    if 'Sales' in df.columns and (df['Sales'] < 0).any():
        issues.append("⚠️ **Sales**: Negative values detected (Refunds?).")

    return issues

def load_and_validate(file) -> dict:
    try:
        if isinstance(file, str):
            df = pd.read_csv(file, encoding='latin-1')
        else:
            df = pd.read_csv(file)
            
        # 1. Normalize Names
        report = normalize_schema(df)
        df_clean = report['df']
        
        # 2. Type Enforcing
        if 'Order Date' in df_clean.columns:
            df_clean['Order Date'] = pd.to_datetime(df_clean['Order Date'], errors='coerce')
        
        numeric_cols = ['Sales', 'Profit', 'Discount', 'Quantity']
        for col in numeric_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        # 3. Quality Assessment
        issues = assess_data_quality(df_clean)

        return {
            "success": True,
            "df": df_clean,
            "found_cols": report['found_cols'],
            "missing_cols": report['missing_cols'],
            "quality_issues": issues
        }

    except Exception as e:
        return {"success": False, "error": str(e)}