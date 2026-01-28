#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Processor for Project Management Dashboard
==============================================

This module handles loading, cleaning, and processing of the joined_projects_data.csv
for the Streamlit dashboard. It includes functions to clean Brazilian data formats,
calculate KPIs, and prepare data for visualization.

Author: Project Dashboard Team
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional


def load_and_clean_data(csv_path: str) -> pd.DataFrame:
    """
    Load and clean the joined projects data.
    
    Args:
        csv_path: Path to the joined_projects_data.csv file
        
    Returns:
        Cleaned DataFrame with processed columns
    """
    df = pd.read_csv(csv_path)
    
    # Remove rows with empty project_id
    df = df[df['project_id'].notna() & (df['project_id'] != '')]
    
    # Clean completion percentage column (convert "0,7%" -> 0.07, "70%" -> 0.70)
    df['conclusao_clean'] = df['conclusao'].copy()
    
    # Handle percentage strings
    mask = df['conclusao_clean'].astype(str).str.contains('%')
    df.loc[mask, 'conclusao_clean'] = (
        df.loc[mask, 'conclusao_clean']
        .astype(str)
        .str.replace('%', '')
        .str.replace(',', '.')
        .astype(float) / 100
    )
    
    # Convert to float, handle missing values
    df['conclusao_clean'] = pd.to_numeric(df['conclusao_clean'], errors='coerce')
    
    # Clean cost values (ensure they are numeric)
    df['valor_clean'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['custo_previsto_clean'] = pd.to_numeric(df['custo_previsto'], errors='coerce').fillna(0)
    
    # Clean dates
    df['inicio_clean'] = pd.to_datetime(df['inicio'], errors='coerce')
    df['prazo_clean'] = pd.to_datetime(df['prazo'], errors='coerce')
    
    return df


def calculate_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate key performance indicators for the dashboard.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        Dictionary with KPI values
    """
    # Total unique projects
    total_projects = df['project_id'].nunique()
    
    # Projects by status
    status_counts = df.groupby('status')['project_id'].nunique().to_dict()
    
    # Average completion rate
    avg_completion = df['conclusao_clean'].mean()
    
    # Cost comparison
    # Get unique project planned costs (first occurrence)
    planned_costs = df.drop_duplicates(subset=['project_id'])['custo_previsto_clean'].sum()
    actual_costs = df['valor_clean'].sum()
    
    return {
        'total_projects': total_projects,
        'status_counts': status_counts,
        'avg_completion': avg_completion if not np.isnan(avg_completion) else 0.0,
        'planned_costs': planned_costs,
        'actual_costs': actual_costs,
        'cost_variance': ((actual_costs - planned_costs) / planned_costs * 100) if planned_costs > 0 else 0.0
    }


def get_area_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze projects by department/area.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        DataFrame with area-wise metrics
    """
    # Get unique projects per area (to avoid double counting)
    area_data = df.drop_duplicates(subset=['project_id']).groupby('area').agg({
        'project_id': 'count',
        'custo_previsto_clean': 'sum',
        'conclusao_clean': 'mean'
    }).round(2)
    
    # Calculate actual costs per area (sum of all costs for projects in that area)
    actual_costs_by_area = df.groupby('area')['valor_clean'].sum()
    
    area_data['custo_real'] = actual_costs_by_area
    area_data = area_data.round(2)
    
    # Rename columns for better display
    area_data.columns = ['qtd_projetos', 'custo_previsto_total', 'conclusao_media', 'custo_real_total']
    
    return area_data.reset_index()


def get_status_distribution(df: pd.DataFrame) -> Tuple[Dict[str, int], Dict[str, str]]:
    """
    Get distribution of projects by status with colors.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        Tuple of (status_counts, status_colors)
    """
    status_counts = df.groupby('status')['project_id'].nunique().to_dict()
    
    # Define colors for each status
    status_colors = {
        'em dia': '#2E8B57',      # Sea green
        'atrasado': '#FF8C00',    # Dark orange  
        'critico': '#DC143C',     # Crimson
        'pausado': '#708090',     # Slate gray
        'concluido': '#4682B4',   # Steel blue
        'andamento': '#3CB371'    # Medium sea green
    }
    
    # Ensure all statuses have colors (default to gray if not defined)
    for status in status_counts:
        if status not in status_colors:
            status_colors[status] = '#A9A9A9'  # Gray
    
    return status_counts, status_colors


def prepare_cost_comparison_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for cost comparison visualization.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        DataFrame with cost comparison by project
    """
    # Get planned costs (unique projects)
    planned = df.drop_duplicates(subset=['project_id'])[['project_id', 'area', 'custo_previsto_clean']]
    
    # Get actual costs (sum of all costs per project)
    actual = df.groupby('project_id')['valor_clean'].sum().reset_index()
    actual.columns = ['project_id', 'custo_real_total']
    
    # Merge planned and actual costs
    cost_comparison = planned.merge(actual, on='project_id', how='left')
    cost_comparison['custo_real_total'] = cost_comparison['custo_real_total'].fillna(0)
    
    # Calculate variance
    cost_comparison['variance_percent'] = (
        (cost_comparison['custo_real_total'] - cost_comparison['custo_previsto_clean']) / 
        cost_comparison['custo_previsto_clean'] * 100
    ).round(2)
    
    return cost_comparison


def format_currency(value: float) -> str:
    """Format currency values in Brazilian Real format."""
    if pd.isna(value) or value == 0:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def format_percentage(value: float) -> str:
    """Format percentage values."""
    if pd.isna(value):
        return "0,0%"
    return f"{value:.1f}%".replace('.', ',')


if __name__ == "__main__":
    # Test the data processor
    df = load_and_clean_data("data/joined_projects_data.csv")
    print(f"Loaded {len(df)} rows")
    print(f"Unique projects: {df['project_id'].nunique()}")
    
    kpis = calculate_kpis(df)
    print("\nKPIs:")
    for key, value in kpis.items():
        print(f"  {key}: {value}")
    
    area_data = get_area_analysis(df)
    print("\nArea Analysis:")
    print(area_data.head())