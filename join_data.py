import pandas as pd
import numpy as np
from difflib import SequenceMatcher
import re

class DataJoiner:
    def __init__(self):
        self.project_mapping = {}
        
    def standardize_project_name(self, name):
        """Standardize project names for matching"""
        if pd.isna(name) or not isinstance(name, str):
            return ""
        
        standardized = name.lower().strip()
        standardized = re.sub(r'[^\w\s]', '', standardized)
        standardized = re.sub(r'\s+', ' ', standardized)
        return standardized
    
    def create_project_mapping(self, projetos_df):
        """Create comprehensive project mapping table"""
        mapping = {}
        
        for _, row in projetos_df.iterrows():
            project_id = row['project_id'] if not pd.isna(row['project_id']) else ""
            projeto = row['projeto'] if not pd.isna(row['projeto']) else ""
            
            if projeto:
                std_name = self.standardize_project_name(projeto)
                mapping[std_name] = projeto
                
            if project_id:
                mapping[project_id] = projeto
                
        return mapping
    
    def match_project_key(self, project_id, projeto):
        """Find the best matching project key"""
        if project_id and not pd.isna(project_id) and str(project_id).strip():
            return str(project_id)
            
        if projeto and not pd.isna(projeto):
            std_name = self.standardize_project_name(str(projeto))
            return std_name
        
        return ""
    
    def prepare_dataframes(self):
        """Load and prepare all dataframes"""
        projetos_df = pd.read_csv(r"E:\TESTES\mittu\data\cleaned\Projetos_clean.csv")
        horas_df = pd.read_csv(r"E:\TESTES\mittu\data\cleaned\Horas_clean.csv") 
        custos_df = pd.read_csv(r"E:\TESTES\mittu\data\cleaned\Custos_clean.csv")
        
        self.project_mapping = self.create_project_mapping(projetos_df)
        
        # Add match keys to each dataframe
        projetos_df['match_key'] = projetos_df.apply(
            lambda row: self.match_project_key(row['project_id'], row['projeto']), axis=1
        )
        
        horas_df['match_key'] = horas_df.apply(
            lambda row: self.match_project_key(row['project_id'], row['projeto']), axis=1
        )
        
        custos_df['match_key'] = custos_df.apply(
            lambda row: self.match_project_key(row['project_id'], row['projeto']), axis=1
        )
        
        return projetos_df, horas_df, custos_df
    
    def full_outer_join_data(self):
        """Perform full outer join of all datasets"""
        projetos_df, horas_df, custos_df = self.prepare_dataframes()
        
        # Add unique identifiers for each source
        projetos_df['projeto_source_id'] = 'PROJ_' + projetos_df.index.astype(str)
        horas_df['horas_source_id'] = 'HOR_' + horas_df.index.astype(str) 
        custos_df['custo_source_id'] = 'CUST_' + custos_df.index.astype(str)
        
        # Get all unique match keys from all datasets
        all_keys = set(projetos_df['match_key'].dropna().unique()) | \
                  set(horas_df['match_key'].dropna().unique()) | \
                  set(custos_df['match_key'].dropna().unique())
        
        # Create base dataframe with all possible match keys
        base_df = pd.DataFrame({'match_key': list(all_keys)})
        
        # Left join each dataset to preserve all records
        merged = base_df.merge(projetos_df, on='match_key', how='left', suffixes=('', '_projeto'))
        merged = merged.merge(horas_df, on='match_key', how='left', suffixes=('', '_horas'))
        merged = merged.merge(custos_df, on='match_key', how='left', suffixes=('', '_custo'))
        
        return merged, projetos_df, horas_df, custos_df
    
    def add_match_flags(self, merged_df):
        """Add flags to indicate data quality and match status"""
        merged_df['has_projeto_data'] = ~merged_df['projeto_source_id'].isna()
        merged_df['has_horas_data'] = ~merged_df['horas_source_id'].isna()
        merged_df['has_custo_data'] = ~merged_df['custo_source_id'].isna()
        
        merged_df['match_quality'] = 'unmatched'
        merged_df.loc[merged_df['has_projeto_data'] & merged_df['has_horas_data'], 'match_quality'] = 'partial'
        merged_df.loc[merged_df['has_projeto_data'] & merged_df['has_custo_data'], 'match_quality'] = 'partial'
        merged_df.loc[merged_df['has_horas_data'] & merged_df['has_custo_data'], 'match_quality'] = 'partial'
        merged_df.loc[merged_df['has_projeto_data'] & merged_df['has_horas_data'] & merged_df['has_custo_data'], 'match_quality'] = 'full'
        
        return merged_df
    
    def generate_final_output(self):
        """Generate and save the final joined dataset"""
        print("Starting data joining process...")
        
        merged_df, projetos_df, horas_df, custos_df = self.full_outer_join_data()
        final_df = self.add_match_flags(merged_df)
        
        output_path = r"E:\TESTES\mittu\data\joined_projects_data.csv"
        final_df.to_csv(output_path, index=False)
        
        self.generate_summary_report(final_df, projetos_df, horas_df, custos_df)
        
        print(f"Data joining completed successfully!")
        print(f"Final dataset: {len(final_df)} rows, {len(final_df.columns)} columns")
        print(f"Saved to: {output_path}")
        
        return final_df
    
    def generate_summary_report(self, final_df, projetos_df, horas_df, custos_df):
        """Generate summary statistics report"""
        print("\n" + "="*50)
        print("DATA JOINING SUMMARY REPORT")
        print("="*50)
        
        print(f"\nSource Data:")
        print(f"   Projetos: {len(projetos_df)} records")
        print(f"   Horas: {len(horas_df)} records") 
        print(f"   Custos: {len(custos_df)} records")
        
        print(f"\nJoin Results:")
        print(f"   Total joined records: {len(final_df)}")
        print(f"   Match quality breakdown:")
        quality_counts = final_df['match_quality'].value_counts()
        for quality, count in quality_counts.items():
            print(f"     {quality}: {count} records ({count/len(final_df)*100:.1f}%)")
        
        print(f"\nData Coverage:")
        print(f"   Records with projeto data: {final_df['has_projeto_data'].sum()}")
        print(f"   Records with horas data: {final_df['has_horas_data'].sum()}")
        print(f"   Records with custo data: {final_df['has_custo_data'].sum()}")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    joiner = DataJoiner()
    final_data = joiner.generate_final_output()