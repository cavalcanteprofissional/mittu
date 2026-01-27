import pandas as pd
import os

excel_file = 'E:/TESTES/mittu/data/raw.xlsx'
output_dir = 'E:/TESTES/mittu/data/csv'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

xl = pd.ExcelFile(excel_file)
print(f"Found {len(xl.sheet_names)} sheets: {xl.sheet_names}")

for sheet_name in xl.sheet_names:
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    csv_filename = f"{sheet_name}.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Created: {csv_path}")

print("All sheets converted to CSV successfully!")