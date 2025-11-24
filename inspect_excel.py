import pandas as pd
import os

file_path = 'Plan_Arbeitstunden 2026.xlsx'

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
else:
    try:
        # Read all sheets to understand the structure
        xls = pd.ExcelFile(file_path)
        print(f"Sheet names: {xls.sheet_names}")
        
        for sheet in xls.sheet_names:
            print(f"\n--- Sheet: {sheet} ---")
            df = pd.read_excel(xls, sheet_name=sheet, nrows=5)
            print(df.columns.tolist())
            print(df.head())
            
    except Exception as e:
        print(f"Error reading excel: {e}")
