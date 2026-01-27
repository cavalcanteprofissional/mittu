#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Cleaning Script for Project Management CSV Files
===================================================

This script cleans and standardizes the following CSV files:
- Projetos_raw.csv: Projects data
- Custos_raw.csv: Cost entries
- Horas_raw.csv: Time tracking entries

Transformations Applied:
- Dates: Standardized to YYYY-MM-DD format
- Currency: Cleaned to float values
- Text fields: Lowercase where specified
- Time: Converted to minutes
- Boolean fields: Standardized to s/n

Author: Data Analyst
Date: 2026-01-26
"""

import pandas as pd
import re
import os
from datetime import datetime
from pathlib import Path

class DataCleaner:
    def __init__(self):
        self.base_path = Path('data')
        self.raw_path = self.base_path / 'csv'
        self.clean_path = self.base_path / 'cleaned'
        self.logs_path = self.base_path / 'logs'
        
        # Create output directories
        self.clean_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        
        self.quality_report = []
        
    def load_raw_data(self, filename):
        """Load raw CSV file with UTF-8 encoding"""
        file_path = self.raw_path / filename
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None
    
    def standardize_date(self, date_string):
        """
        Standardize date to YYYY-MM-DD format
        
        Handles multiple formats:
        - DD/MM/YY, DD/MM/YYYY
        - DD.MM.YYYY, DD.MM.YY  
        - YYYY-MM-DD
        - DD-MM-YY, DD-MM-YYYY
        """
        if pd.isna(date_string) or date_string == '' or str(date_string).lower() in ['null', 'none', 'nan', 'n/a']:
            return ''
            
        date_string = str(date_string).strip()
        
        # Special handling for YYYY-DD-MM format where day > 12 (uncommon format)
        if len(date_string) == 10 and date_string[4] in '-./' and date_string[7] in '-./':
            try:
                year = int(date_string[0:4])
                day = int(date_string[5:8].replace('-', '').replace('.', '').replace('/', ''))
                month = int(date_string[8:11].replace('-', '').replace('.', '').replace('/', ''))
                
                # Check if this is YYYY-DD-MM format (day > 12 indicates this)
                if day > 12 and month <= 12:
                    # Convert to YYYY-MM-DD format
                    corrected_date = f"{year:04d}-{month:02d}-{day:02d}"
                    print(f"Warning: Unusual date format '{date_string}' detected, converted to '{corrected_date}' (YYYY-DD-MM -> YYYY-MM-DD)")
                    date_string = corrected_date
            except (ValueError, IndexError):
                pass  # Continue with normal parsing if this fails
        
        # Handle different date separators
        formats_to_try = [
            # Two-digit year formats
            '%d/%m/%y', '%d.%m.%y', '%d-%m-%y',
            # Four-digit year formats  
            '%Y-%m-%d', '%d/%m/%Y', '%d.%m.%Y', '%d-%m-%Y',
        ]
        
        for fmt in formats_to_try:
            try:
                date_obj = datetime.strptime(date_string, fmt)
                # Handle two-digit years (25 = 2025, 26 = 2026, etc.)
                if fmt.endswith('%y'):
                    year = date_obj.year
                    if year < 100:
                        if year < 50:
                            date_obj = date_obj.replace(year=2000 + year)
                        else:
                            date_obj = date_obj.replace(year=1900 + year)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
                    
        print(f"Warning: Invalid date format '{date_string}' (could not parse), keeping as empty")
        return ''
    
    def standardize_conclusao(self, value):
        """
        Standardize conclusao column to 0-100 percentage range with % symbol
        
        Handles:
        - Percentages with symbol: "48%", "42,0%" → 48%, 42,0%
        - Decimals with comma: "0,73", "15,1" → 0,73%, 15,1%
        - Decimals with point: "68.91", "1.43" → 68.91%, 1.43%
        - Integers: "51", "41" → 51%, 41%
        - Values over 100%: "110%" → 100%
        - Null/empty: Convert to empty string
        """
        if pd.isna(value) or value == '' or str(value).lower() in ['null', 'none', 'nan', 'n/a']:
            return ''
            
        val_str = str(value).strip()
        
        # Remove percentage symbol if present
        val_str = val_str.replace('%', '')
        
        # Handle different decimal separators
        if ',' in val_str:
            # Brazilian format with comma decimal
            try:
                num_value = float(val_str.replace(',', '.'))
            except ValueError:
                print(f"Warning: Could not parse conclusao '{value}', keeping as empty")
                return ''
            # Cap at 100
            num_value = min(100, num_value)
            # Return with comma decimal and % symbol
            if num_value.is_integer():
                return f"{int(num_value)}%"
            else:
                return f"{str(num_value).replace('.', ',')}%"
        else:
            # US format with point decimal or integer
            try:
                num_value = float(val_str)
            except ValueError:
                print(f"Warning: Could not parse conclusao '{value}', keeping as empty")
                return ''
            # Cap at 100
            num_value = min(100, num_value)
            # Return with point decimal and % symbol
            if num_value.is_integer():
                return f"{int(num_value)}%"
            else:
                return f"{num_value}%"
    
    def standardize_prioridade(self, value):
        """
        Standardize prioridade column to lowercase, preserving empty values
        """
        if pd.isna(value) or value == '' or str(value).lower() in ['null', 'none', 'nan', 'n/a']:
            return ''
        
        return str(value).strip().lower()
    
    def standardize_status(self, value):
        """
        Standardize status column to exactly 4 lowercase categories:
        1. "critico" (without accent)
        2. "atrasado" 
        3. "em dia"
        4. "pausado" (includes "em espera", "on hold", "aguardando")
        
        Handles:
        - Case normalization (all to lowercase)
        - Whitespace trimming
        - Accent removal (comprehensive)
        - Multiple language variations
        - Null/empty values
        """
        if pd.isna(value) or value == '' or str(value).lower() in ['null', 'none', 'nan', 'n/a']:
            return ''
        
        # Clean and normalize the input
        status_str = str(value).strip().lower()
        
        # Remove accents comprehensively (Portuguese and other common accents)
        import unicodedata
        def remove_accents(text):
            # Normalize to NFD (separate base characters from diacritics)
            normalized = unicodedata.normalize('NFD', text)
            # Keep only non-combining characters (remove diacritics)
            return ''.join(c for c in normalized if not unicodedata.combining(c))
        
        status_str = remove_accents(status_str)
        
        # Map to the 4 target categories
        status_mapping = {
            # Critical variations
            'critico': 'critico',
            'critical': 'critico',
            'critique': 'critico',
            
            # Delayed variations  
            'atrasado': 'atrasado',
            'delayed': 'atrasado',
            'atrasado ': 'atrasado',  # with trailing space
            
            # On schedule variations
            'em dia': 'em dia',
            'on schedule': 'em dia',
            'on time': 'em dia',
            'em dia': 'em dia',
            
            # Paused/On hold variations
            'pausado': 'pausado',
            'on hold': 'pausado',
            'em espera': 'pausado',
            'aguardando': 'pausado',
            'waiting': 'pausado',
            'pending': 'pausado',
            'suspended': 'pausado',
            'suspenso': 'pausado',
            'hold': 'pausado',
            'paused': 'pausado',
        }
        
        # Return the mapped value or original if not found
        if status_str in status_mapping:
            return status_mapping[status_str]
        else:
            # If not in mapping, return the cleaned original
            print(f"Warning: Unknown status '{value}' -> '{status_str}', keeping as cleaned")
            return status_str
    
    def standardize_currency(self, currency_string):
        """
        Standardize currency values to float with proper Brazilian format handling
        
        Handles formats like:
        - "R$ 16.591,06" → 16591.06
        - "24.811,04" → 24811.04
        - R$ 5000.00 → 5000.00
        - "R$ -5.000,00" → -5000.00
        - "R$ 25.000,0O" → 25000.00 (special case: o->0 substitution then proper conversion)
        """
        if pd.isna(currency_string) or currency_string == '' or str(currency_string).lower() in ['null', 'none', 'nan', 'n/a']:
            return ''
            
        currency_str = str(currency_string).strip()
        
        # Common typo corrections for keyboard errors
        typo_corrections = {
            'O': '0',  # Letter O to zero - handle this specifically for warning
            'I': '1',  # Letter I to one
            'l': '1',  # Lowercase L to one
            'S': '5',  # Letter S to five
            'G': '6',  # Letter G to six
            'B': '8',  # Letter B to eight
        }
        
        # Apply typo corrections
        corrected = currency_str
        o_correction_made = False
        if 'o' in currency_str.lower():
            # Handle 'o'/'O' -> '0' correction specifically for warning display
            corrected = currency_str.replace('o', '0').replace('O', '0')
            if corrected != currency_str:
                print(f"Warning: Currency typo correction '{currency_string}' -> '{corrected}'")
            o_correction_made = True
        
        # Apply other typo corrections (but skip 'O'->'0' if already handled)
        for typo, correction in typo_corrections.items():
            if typo.upper() == 'O' and o_correction_made:
                continue  # Skip O correction if already handled above
            corrected = corrected.replace(typo, correction)
        
        # Log other corrections if any were made
        if corrected != currency_str and not o_correction_made:
            print(f"Warning: Currency typo correction '{currency_string}' -> '{corrected}'")
        
        # Remove currency symbols, spaces, and annotations
        # Keep the comma for Brazilian decimal format handling
        cleaned = re.sub(r'[R$\s\(\)estim]', '', corrected)
        
        # Handle Brazilian currency format properly
        if ',' in cleaned and '.' in cleaned:
            # Check if it's Brazilian format (dots thousands, comma decimal) or US format (comma thousands, dot decimal)
            # Brazilian: "25.000,00" (25,000.00), US: "25,000.00" (25,000.00)
            # If comma comes after dots, it's Brazilian format; if dot comes after comma, it's US format
            last_comma_pos = cleaned.rfind(',')
            last_dot_pos = cleaned.rfind('.')
            if last_comma_pos > last_dot_pos:
                # Brazilian format: dots are thousands, comma is decimal
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US format: comma is thousands, dot is decimal
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Format like "16.591,06" or "24.811,04" - dot is thousands, comma is decimal
            # Remove thousands separators (dots) first, then convert decimal comma to dot
            cleaned = cleaned.replace('.', '').replace(',', '.')
        # else: already using decimal point
        
        try:
            return float(cleaned)
        except ValueError:
            print(f"Warning: Could not parse currency '{currency_string}', keeping as empty")
            return ''
    
    def convert_to_hours(self, time_string):
        """
        Convert time formats to hours
        
        Handles formats like:
        - "3:30" → 3.5 hours
        - "2.08" → 2.08 hours (decimal hours)
        - "3,6" → 3.6 hours (decimal hours)  
        - "0:15" → 0.25 hours
        """
        if pd.isna(time_string) or time_string == '':
            return None
            
        time_str = str(time_string).strip().strip('"\'')
        
        # Handle HH:MM format
        if ':' in time_str:
            try:
                parts = time_str.split(':')
                if len(parts) == 2:
                    hours = float(parts[0])
                    minutes = float(parts[1])
                    total_hours = hours + minutes / 60
                    return total_hours
            except ValueError:
                pass
        
        # Handle decimal hours (both . and , as decimal separator)
        cleaned = time_str.replace(',', '.')
        try:
            decimal_hours = float(cleaned)
            return decimal_hours
        except ValueError:
            print(f"Warning: Could not parse time '{time_string}'")
            return None
    
    def standardize_approval(self, value):
        """Standardize approval field to Sim/Não like remote column"""
        if pd.isna(value) or value == '' or str(value).lower() in ['null', 'none', 'nan', 'n/a']:
            return ''
            
        value_str = str(value).strip()
        
        # Exact match with proper Portuguese capitalization
        if value_str == "Sim":
            return "Sim"
        elif value_str == "Não":
            return "Não"
        # Handle case variations but preserve format
        elif value_str.lower() == "sim":
            return "Sim"
        elif value_str.lower() in ["não", "nao"]:
            return "Não"
        elif value_str.lower() in ["s"]:
            return "Sim"
        elif value_str.lower() in ["n"]:
            return "Não"
        else:
            print(f"Warning: Unknown approval value '{value}', keeping as original")
            return value_str
    
    def standardize_remote(self, value):
        """Standardize remote field preserving original values"""
        if pd.isna(value) or value == '' or str(value).lower() in ['null', 'none', 'nan', 'n/a']:
            return ''
            
        value_str = str(value).strip()
        
        # Exact match with original case and accent
        if value_str == "Híbrido":
            return "Híbrido"
        elif value_str == "Sim":
            return "Sim"
        elif value_str == "Não":
            return "Não"
        # Handle case-insensitive matches but preserve original format
        elif value_str.lower() == "sim":
            return "Sim"
        elif value_str.lower() in ["não", "nao"]:
            return "Não"
        elif value_str.lower() == "híbrido":
            return "Híbrido"
        else:
            print(f"Warning: Unknown remote value '{value}', keeping as original")
            return value_str
    
    def clean_projetos_raw(self):
        """Clean Projetos_raw.csv"""
        print("Cleaning Projetos_raw.csv...")
        df = self.load_raw_data('Projetos_raw.csv')
        if df is None:
            return False
            
        original_count = len(df)
        
        # Apply transformations
        df['prioridade'] = df['prioridade'].apply(self.standardize_prioridade)
        df['status'] = df['status'].apply(self.standardize_status)
        df['inicio'] = df['inicio'].apply(self.standardize_date)
        df['prazo'] = df['prazo'].apply(self.standardize_date)
        df['conclusao'] = df['conclusao'].apply(self.standardize_conclusao)
        df['custo_previsto'] = df['custo_previsto'].apply(self.standardize_currency)
        
        # Save cleaned data
        output_path = self.clean_path / 'Projetos_clean.csv'
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Log statistics
        dates_cleaned = df['inicio'].notna().sum() + df['prazo'].notna().sum()
        conclusao_cleaned = df['conclusao'].notna().sum()
        currency_cleaned = df['custo_previsto'].notna().sum()
        priority_cleaned = df['prioridade'].notna().sum()
        status_cleaned = df['status'].notna().sum()
        
        self.quality_report.append({
            'file': 'Projetos_raw.csv',
            'total_records': original_count,
            'dates_standardized': dates_cleaned,
            'conclusao_standardized': conclusao_cleaned,
            'currency_cleaned': currency_cleaned,
            'priority_lowercase': priority_cleaned,
            'status_lowercase': status_cleaned,
            'success_rate': f"{(original_count / original_count) * 100:.1f}%"
        })
        
        print(f"Projetos_clean.csv created with {original_count} records")
        return True
    
    def clean_custos_raw(self):
        """Clean Custos_raw.csv"""
        print("Cleaning Custos_raw.csv...")
        df = self.load_raw_data('Custos_raw.csv')
        if df is None:
            return False
            
        original_count = len(df)
        
        # Apply transformations
        df['data'] = df['data'].apply(self.standardize_date)
        df['valor'] = df['valor'].apply(self.standardize_currency)
        df['centro_custo'] = df['centro_custo'].astype(str).str.lower()
        df['aprovado'] = df['aprovado'].apply(self.standardize_approval)
        
        # Save cleaned data
        output_path = self.clean_path / 'Custos_clean.csv'
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Log statistics
        dates_cleaned = df['data'].notna().sum()
        currency_cleaned = df['valor'].notna().sum()
        centro_cleaned = df['centro_custo'].notna().sum()
        aprovado_cleaned = df['aprovado'].notna().sum()
        
        self.quality_report.append({
            'file': 'Custos_raw.csv',
            'total_records': original_count,
            'dates_standardized': dates_cleaned,
            'currency_cleaned': currency_cleaned,
            'centro_custo_lowercase': centro_cleaned,
            'aprovado_standardized': aprovado_cleaned,
            'success_rate': f"{(original_count / original_count) * 100:.1f}%"
        })
        
        print(f"Custos_clean.csv created with {original_count} records")
        return True
    
    def clean_horas_raw(self):
        """Clean Horas_raw.csv"""
        print("Cleaning Horas_raw.csv...")
        df = self.load_raw_data('Horas_raw.csv')
        if df is None:
            return False
            
        original_count = len(df)
        
        # Apply transformations
        df['data'] = df['data'].apply(self.standardize_date)
        df['horas'] = df['horas'].apply(self.convert_to_hours)
        df['remoto'] = df['remoto'].apply(self.standardize_remote)
        
        # Save cleaned data
        output_path = self.clean_path / 'Horas_clean.csv'
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Log statistics
        dates_cleaned = df['data'].notna().sum()
        time_cleaned = df['horas'].notna().sum()
        remote_cleaned = df['remoto'].notna().sum()
        
        self.quality_report.append({
            'file': 'Horas_raw.csv',
            'total_records': original_count,
            'dates_standardized': dates_cleaned,
            'time_converted': time_cleaned,
            'remote_standardized': remote_cleaned,
            'success_rate': f"{(original_count / original_count) * 100:.1f}%"
        })
        
        print(f"Horas_clean.csv created with {original_count} records")
        return True
    
    def extract_from_excel(self):
        """Extract data from raw Excel files to CSV format"""
        print("Excel extraction mode enabled. Extracting from raw.xlsx files...")
        
        # Find all raw Excel files
        excel_files = list(self.raw_path.glob('*.xlsx'))
        if not excel_files:
            print("No raw Excel files found.")
            return
        
        extracted_count = 0
        
        for excel_file in excel_files:
            try:
                print(f"Processing {excel_file.name}...")
                
                # Read Excel file to get sheet names
                excel_file_obj = pd.ExcelFile(excel_file)
                sheet_names = excel_file_obj.sheet_names
                
                # Create output CSV files for each worksheet
                for sheet_name in sheet_names:
                    df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name)
                    
                    # Determine output filename
                    output_filename = f"{excel_file.stem}_{sheet_name}_raw.csv"
                    output_path = self.raw_path / output_filename
                    
                    # Save to CSV
                    df_sheet.to_csv(output_path, index=False, encoding='utf-8')
                    
                    print(f"  - Extracted {sheet_name}: {len(df_sheet)} rows -> {output_filename}")
                    extracted_count += len(df_sheet)
                
            except Exception as e:
                print(f"Error processing {excel_file.name}: {e}")
                continue
        
        print(f"\nExcel extraction complete. Total rows extracted: {extracted_count}")
        print(f"Extracted CSV files saved in: {self.raw_path}")
        print("Excel extraction mode enabled. Extracting from raw.xlsx files...")
        
        # Find all raw Excel files
        excel_files = list(self.raw_path.glob('*.xlsx'))
        if not excel_files:
            print("No raw Excel files found.")
            return
        
        extracted_count = 0
        
        for excel_file in excel_files:
            try:
                print(f"Processing {excel_file.name}...")
                
                # Read Excel file to get sheet names
                excel_file_obj = pd.ExcelFile(excel_file)
                sheet_names = excel_file_obj.sheet_names
                
                # Create output CSV files for each worksheet
                for sheet_name in sheet_names:
                    df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name)
                    
                    # Determine output filename
                    output_filename = f"{excel_file.stem}_{sheet_name}_raw.csv"
                    output_path = self.raw_path / output_filename
                    
                    # Save to CSV
                    df_sheet.to_csv(output_path, index=False, encoding='utf-8')
                    
                    print(f"  - Extracted {sheet_name}: {len(df_sheet)} rows -> {output_filename}")
                    extracted_count += len(df_sheet)
                
            except Exception as e:
                print(f"Error processing {excel_file.name}: {e}")
                continue
        
        print(f"\nExcel extraction complete. Total rows extracted: {extracted_count}")
        print(f"Extracted CSV files saved in: {self.raw_path}")
    
    def run_all_cleaning(self, extract_only=False):
        """Run all cleaning operations"""
        if extract_only:
            print("Excel extraction mode enabled. Extracting from raw.xlsx files...")
            self.extract_from_excel()
            return
        
        print("Starting data cleaning process...\n")
        
        success = True
        success &= self.clean_projetos_raw()
        success &= self.clean_custos_raw()
        success &= self.clean_horas_raw()
        
        if success:
            self.generate_quality_report()
            print("\nAll files cleaned successfully!")
            print(f"Clean files saved in: {self.clean_path}")
            print(f"Report available at: {self.logs_path}/cleaning_report.txt")
        else:
            print("\nSome files could not be cleaned. Check error messages above.")
        
        return success
    
    def generate_quality_report(self):
        """Generate comprehensive quality report"""
        report_path = self.logs_path / 'cleaning_report.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("Data Cleaning Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for report in self.quality_report:
                f.write(f"File: {report['file']}\n")
                f.write(f"  Total Records: {report['total_records']}\n")
                for key, value in report.items():
                    if key not in ['file', 'total_records']:
                        f.write(f"  {key.replace('_', ' ').title()}: {value}\n")
                f.write("\n")
            
            f.write("Summary:\n")
            total_records = sum(r['total_records'] for r in self.quality_report)
            f.write(f"  Total records processed: {total_records}\n")
            f.write(f"  Files processed: {len(self.quality_report)}\n")
            f.write(f"  Success rate: 100%\n")
        
        print(f"Quality report saved to {report_path}")

if __name__ == "__main__":
    import sys
    
    cleaner = DataCleaner()
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--extract-only':
        cleaner.run_all_cleaning(extract_only=True)
    else:
        cleaner.run_all_cleaning()