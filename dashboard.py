#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Management Dashboard
===========================

Streamlit dashboard for visualizing project management data including
projects, costs, hours, and status tracking.

Author: Project Dashboard Team
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_processor import (
    load_and_clean_data, 
    calculate_kpis, 
    get_area_analysis,
    get_status_distribution,
    prepare_cost_comparison_data,
    format_currency,
    format_percentage
)


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
            st.plotly_chart(status_fig, use_container_width=True)
    
    with col2:
        # Cost comparison chart  
        cost_fig = create_cost_comparison_chart(cost_comparison)
        st.plotly_chart(cost_fig, use_container_width=True)
    
    # Main area analysis chart
    st.markdown("### Visão Detalhada por Área")
    area_fig = create_area_chart(area_data)
    st.plotly_chart(area_fig, use_container_width=True)
    
    # Detailed data table (optional - can be expanded)
    with st.expander("📋 Ver Dados Detalhados por Área"):
        # Format the data for display
        display_data = area_data.copy()
        display_data['custo_previsto_total'] = display_data['custo_previsto_total'].apply(format_currency)
        display_data['custo_real_total'] = display_data['custo_real_total'].apply(format_currency)
        display_data['conclusao_media'] = display_data['conclusao_media'].apply(lambda x: format_percentage(x * 100))
        
        display_data.columns = ['Área', 'Qtd Projetos', 'Custo Previsto Total', 'Conclusão Média', 'Custo Real Total']
        st.dataframe(display_data, use_container_width=True, hide_index=True)
    
    # Footer
    st.markdown("---")
    st.markdown("*Dashboard atualizado com dados mais recentes*")


if __name__ == "__main__":
    main()