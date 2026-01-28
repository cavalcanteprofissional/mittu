#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Management Dashboard
===========================

Consolidated Streamlit dashboard for visualizing project management data including
projects, costs, hours, and status tracking. All data processing and visualization
functions are contained in this single file for easy deployment.

Author: Project Dashboard Team
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import Dict, Tuple, Optional


# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

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


# ============================================================================
# DASHBOARD FUNCTIONS
# ============================================================================

@st.cache_data
def load_data():
    """Load and cache the processed data."""
    try:
        return load_and_clean_data("data/joined_projects_data.csv")
    except FileNotFoundError:
        st.error("Arquivo data/joined_projects_data.csv não encontrado!")
        return None


def display_kpi_cards(kpis):
    """Display KPI cards at the top of the dashboard."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total de Projetos",
            value=kpis['total_projects']
        )
    
    with col2:
        # Find most common status for display
        if kpis['status_counts']:
            most_common_status = max(kpis['status_counts'], key=kpis['status_counts'].get)
            status_count = kpis['status_counts'][most_common_status]
            st.metric(
                label=f"Projetos {most_common_status}",
                value=status_count
            )
        else:
            st.metric(label="Projetos por Status", value="0")
    
    with col3:
        st.metric(
            label="Percentual Médio de Conclusão",
            value=format_percentage(kpis['avg_completion'] * 100)
        )
    
    with col4:
        st.metric(
            label="Variação de Custo",
            value=format_percentage(kpis['cost_variance']),
            delta=f"{format_percentage(abs(kpis['cost_variance']))} vs previsto",
            delta_color="normal" if kpis['cost_variance'] >= 0 else "inverse"
        )


def create_status_pie_chart(status_counts, status_colors):
    """Create a pie chart for project status distribution."""
    if not status_counts:
        return None
        
    # Prepare data for pie chart
    labels = list(status_counts.keys())
    values = list(status_counts.values())
    colors = [status_colors.get(status, '#A9A9A9') for status in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Distribuição de Projetos por Status",
        font=dict(size=12),
        showlegend=True,
        height=400
    )
    
    return fig


def create_area_chart(area_data):
    """Create a comprehensive area analysis chart."""
    # Melt data for better visualization
    metrics = ['qtd_projetos', 'custo_previsto_total', 'custo_real_total']
    melted_data = pd.melt(
        area_data, 
        id_vars=['area'], 
        value_vars=metrics,
        var_name='metric', 
        value_name='value'
    )
    
    # Define metric names and colors
    metric_config = {
        'qtd_projetos': {'name': 'Qtd Projetos', 'color': '#1f77b4'},
        'custo_previsto_total': {'name': 'Custo Previsto', 'color': '#ff7f0e'},
        'custo_real_total': {'name': 'Custo Real', 'color': '#2ca02c'}
    }
    
    melted_data['metric_name'] = melted_data['metric'].map(lambda x: metric_config[x]['name'])
    melted_data['color'] = melted_data['metric'].map(lambda x: metric_config[x]['color'])
    
    # Create grouped bar chart
    fig = px.bar(
        melted_data,
        x='area',
        y='value',
        color='metric_name',
        title='Visão por Área',
        labels={'value': 'Valor', 'area': 'Área'},
        color_discrete_map={
            'Qtd Projetos': '#1f77b4',
            'Custo Previsto': '#ff7f0e', 
            'Custo Real': '#2ca02c'
        },
        barmode='group'
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="Área",
        yaxis_title="Valor",
        legend_title="Métricas"
    )
    
    return fig


def create_cost_comparison_chart(cost_data):
    """Create a cost comparison chart."""
    fig = go.Figure()
    
    # Add planned costs
    fig.add_trace(go.Bar(
        name='Custo Previsto',
        x=cost_data['area'],
        y=cost_data['custo_previsto_clean'],
        marker_color='#ff7f0e',
        text=[format_currency(val) for val in cost_data['custo_previsto_clean']],
        textposition='auto'
    ))
    
    # Add actual costs
    fig.add_trace(go.Bar(
        name='Custo Real',
        x=cost_data['area'],
        y=cost_data['custo_real_total'],
        marker_color='#2ca02c',
        text=[format_currency(val) for val in cost_data['custo_real_total']],
        textposition='auto'
    ))
    
    fig.update_layout(
        title='Custo Previsto x Real por Área',
        barmode='group',
        height=400,
        xaxis_title='Área',
        yaxis_title='Valor (R$)',
        legend_title='Tipo de Custo'
    )
    
    return fig


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def main():
    """Main dashboard function."""
    st.set_page_config(
        page_title="Dashboard de Projetos",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Dashboard de Gestão de Projetos")
    st.markdown("---")
    
    # Load data
    df = load_data()
    
    if df is None:
        st.error("Não foi possível carregar os dados. Verifique se o arquivo 'data/joined_projects_data.csv' existe.")
        return
    
    # Calculate KPIs
    kpis = calculate_kpis(df)
    
    # Display KPI cards
    display_kpi_cards(kpis)
    
    st.markdown("---")
    
    # Get analysis data
    area_data = get_area_analysis(df)
    status_counts, status_colors = get_status_distribution(df)
    cost_comparison = prepare_cost_comparison_data(df)
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Status pie chart
        status_fig = create_status_pie_chart(status_counts, status_colors)
        if status_fig:
            st.plotly_chart(status_fig, width='stretch')
    
    with col2:
        # Cost comparison chart  
        cost_fig = create_cost_comparison_chart(cost_comparison)
        st.plotly_chart(cost_fig, width='stretch')
    
    # Main area analysis chart
    st.markdown("### Visão Detalhada por Área")
    area_fig = create_area_chart(area_data)
    st.plotly_chart(area_fig, width='stretch')
    
    # Detailed data table (optional - can be expanded)
    with st.expander("📋 Ver Dados Detalhados por Área"):
        # Format the data for display
        display_data = area_data.copy()
        display_data['custo_previsto_total'] = display_data['custo_previsto_total'].apply(format_currency)
        display_data['custo_real_total'] = display_data['custo_real_total'].apply(format_currency)
        display_data['conclusao_media'] = display_data['conclusao_media'].apply(lambda x: format_percentage(x * 100))
        
        display_data.columns = ['Área', 'Qtd Projetos', 'Custo Previsto Total', 'Conclusão Média', 'Custo Real Total']
        st.dataframe(display_data, width='stretch', hide_index=True)
    
    # Footer
    st.markdown("---")
    st.markdown("*Dashboard consolidado para fácil deployment*")


if __name__ == "__main__":
    main()