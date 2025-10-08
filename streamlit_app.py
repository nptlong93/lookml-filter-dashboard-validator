#!/usr/bin/env python3
"""
LookML Filter Link Visualizer - Streamlit + PyVis

Interactive web application for visualizing and validating LookML dashboard filter links.
Uses Streamlit for the UI and PyVis for interactive network visualizations.

Features:
- Interactive network visualization with PyVis
- Filter link validation and analysis
- Real-time filtering and exploration
- Export capabilities
- Responsive design

Author: AI Assistant
Date: 2024
"""

import streamlit as st
import yaml
import json
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pyvis.network import Network
import tempfile
import os
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="LookML Filter Link Visualizer",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

class LookMLAnalyzer:
    """LookML Dashboard Filter Link Analyzer"""
    
    def __init__(self):
        self.dashboards = []
        self.current_dashboard = None
        self.filter_analysis = []
    
    def load_dashboard_file(self, file_path: str) -> Optional[Dict]:
        """Load and parse a single dashboard file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            data = yaml.safe_load(content)
            
            # Extract dashboard name
            dashboard_name = "Unknown Dashboard"
            if isinstance(data, list) and len(data) > 0:
                dashboard_data = data[0]
                if isinstance(dashboard_data, dict):
                    dashboard_name = dashboard_data.get('dashboard', dashboard_data.get('title', 'Unknown Dashboard'))
            
            # Parse filters
            filters = []
            if isinstance(data, list) and len(data) > 0:
                dashboard_data = data[0]
                if isinstance(dashboard_data, dict) and 'filters' in dashboard_data:
                    filters_data = dashboard_data['filters']
                    if isinstance(filters_data, list):
                        for filter_data in filters_data:
                            filters.append({
                                'name': filter_data.get('name', ''),
                                'title': filter_data.get('title', ''),
                                'type': filter_data.get('type', ''),
                                'field': filter_data.get('field', ''),
                                'listens_to_filters': filter_data.get('listens_to_filters', []),
                                'model': filter_data.get('model', ''),
                                'explore': filter_data.get('explore', ''),
                                'default_value': str(filter_data.get('default_value', '')),
                                'allow_multiple_values': filter_data.get('allow_multiple_values', False),
                                'required': filter_data.get('required', False)
                            })
            
            # Parse visualizations
            visualizations = []
            if isinstance(data, list) and len(data) > 0:
                dashboard_data = data[0]
                if isinstance(dashboard_data, dict) and 'elements' in dashboard_data:
                    elements_data = dashboard_data['elements']
                    if isinstance(elements_data, list):
                        for element_data in elements_data:
                            if element_data.get('type') not in ['text', 'single_value', 'single_number']:
                                visualizations.append({
                                    'title': element_data.get('title', ''),
                                    'name': element_data.get('name', ''),
                                    'type': element_data.get('type', ''),
                                    'explore': element_data.get('explore', ''),
                                    'listen': element_data.get('listen', {}),
                                    'fields': element_data.get('fields', []),
                                    'row': element_data.get('row', 0),
                                    'col': element_data.get('col', 0),
                                    'width': element_data.get('width', 0),
                                    'height': element_data.get('height', 0)
                                })
            
            dashboard = {
                'name': dashboard_name,
                'file_path': file_path,
                'filters': filters,
                'visualizations': visualizations
            }
            
            self.dashboards.append(dashboard)
            self.current_dashboard = dashboard
            
            return dashboard
            
        except Exception as e:
            st.error(f"Error loading dashboard file: {str(e)}")
            return None
    
    def analyze_filter_links(self, dashboard: Dict) -> List[Dict]:
        """Analyze filter links for a dashboard"""
        filter_analysis = []
        
        for filter_def in dashboard['filters']:
            linked_viz = []
            for viz in dashboard['visualizations']:
                if filter_def['title'] in viz['listen']:
                    linked_viz.append(viz['title'])
            
            coverage = (len(linked_viz) / len(dashboard['visualizations']) * 100) if dashboard['visualizations'] else 0
            
            # Determine status
            if coverage == 100:
                status = 'complete'
                status_color = '#4caf50'
            elif coverage > 0:
                status = 'partial'
                status_color = '#ff9800'
            else:
                status = 'missing'
                status_color = '#ff6b6b'
            
            filter_analysis.append({
                'filter_title': filter_def['title'],
                'filter_type': filter_def['type'],
                'field': filter_def['field'],
                'linked_visualizations': linked_viz,
                'coverage_percentage': coverage,
                'link_count': len(linked_viz),
                'total_visualizations': len(dashboard['visualizations']),
                'status': status,
                'status_color': status_color,
                'listens_to_filters': filter_def['listens_to_filters']
            })
        
        self.filter_analysis = filter_analysis
        return filter_analysis
    
    def create_pyvis_network(self, dashboard: Dict, filter_analysis: List[Dict]) -> Network:
        """Create PyVis network visualization"""
        net = Network(
            height="600px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#333333",
            directed=True
        )
        
        # Configure physics
        net.set_options("""
        {
            "physics": {
                "enabled": true,
                "stabilization": {"iterations": 100},
                "barnesHut": {
                    "gravitationalConstant": -2000,
                    "centralGravity": 0.1,
                    "springLength": 200,
                    "springConstant": 0.05,
                    "damping": 0.09
                }
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 200
            }
        }
        """)
        
        # Add filter nodes
        for filter_info in filter_analysis:
            status = filter_info['status']
            color = filter_info['status_color']
            
            # Node size based on link count
            size = max(20, filter_info['link_count'] * 5)
            
            net.add_node(
                filter_info['filter_title'],
                label=filter_info['filter_title'],
                color=color,
                size=size,
                title=f"""
                Filter: {filter_info['filter_title']}
                Type: {filter_info['filter_type']}
                Coverage: {filter_info['coverage_percentage']:.1f}%
                Links: {filter_info['link_count']}
                Status: {status.title()}
                """,
                group="filter"
            )
        
        # Add visualization nodes
        for viz in dashboard['visualizations']:
            filter_count = len(viz['listen'])
            size = max(15, filter_count * 3)
            
            net.add_node(
                viz['title'],
                label=viz['title'],
                color='#2196f3',
                size=size,
                title=f"""
                Visualization: {viz['title']}
                Type: {viz['type']}
                Explore: {viz['explore']}
                Filters: {filter_count}
                """,
                group="visualization"
            )
        
        # Add edges for filter-to-visualization links
        for viz in dashboard['visualizations']:
            for filter_title in viz['listen'].keys():
                net.add_edge(
                    filter_title,
                    viz['title'],
                    color='#667eea',
                    width=2,
                    title=f"Filter Link: {filter_title} → {viz['title']}"
                )
        
        # Add edges for filter dependencies
        for filter_info in filter_analysis:
            for dep in filter_info['listens_to_filters']:
                net.add_edge(
                    dep,
                    filter_info['filter_title'],
                    color='#96ceb4',
                    width=1,
                    title=f"Filter Dependency: {dep} → {filter_info['filter_title']}"
                )
        
        return net
    
    def create_coverage_chart(self, filter_analysis: List[Dict]) -> go.Figure:
        """Create coverage analysis chart"""
        df = pd.DataFrame(filter_analysis)
        
        # Sort by coverage
        df_sorted = df.sort_values('coverage_percentage')
        
        # Create horizontal bar chart
        fig = go.Figure()
        
        # Color based on status
        colors = [info['status_color'] for info in filter_analysis]
        
        fig.add_trace(go.Bar(
            y=df_sorted['filter_title'],
            x=df_sorted['coverage_percentage'],
            orientation='h',
            marker_color=colors,
            text=[f"{coverage:.1f}%" for coverage in df_sorted['coverage_percentage']],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Coverage: %{x:.1f}%<br>Links: %{customdata}<extra></extra>',
            customdata=df_sorted['link_count']
        ))
        
        fig.update_layout(
            title='Filter Coverage Analysis',
            xaxis_title='Coverage Percentage',
            yaxis_title='Filter Name',
            height=max(600, len(df) * 25),
            margin=dict(l=200),
            showlegend=False
        )
        
        return fig
    
    def create_summary_metrics(self, dashboard: Dict, filter_analysis: List[Dict]) -> Dict:
        """Create summary metrics"""
        total_filters = len(filter_analysis)
        total_visualizations = len(dashboard['visualizations'])
        
        complete_links = len([f for f in filter_analysis if f['status'] == 'complete'])
        partial_links = len([f for f in filter_analysis if f['status'] == 'partial'])
        missing_links = len([f for f in filter_analysis if f['status'] == 'missing'])
        
        avg_coverage = sum(f['coverage_percentage'] for f in filter_analysis) / len(filter_analysis) if filter_analysis else 0
        
        return {
            'total_filters': total_filters,
            'total_visualizations': total_visualizations,
            'complete_links': complete_links,
            'partial_links': partial_links,
            'missing_links': missing_links,
            'avg_coverage': avg_coverage
        }

def main():
    """Main Streamlit application"""
    
    # Initialize analyzer
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = LookMLAnalyzer()
    
    # Header
    st.title("🔗 LookML Filter Link Visualizer")
    st.markdown("Interactive visualization and validation of LookML dashboard filter links")
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Dashboard Selection")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload LookML Dashboard File",
            type=['lookml', 'yaml', 'yml'],
            help="Upload a .lookml dashboard file to analyze"
        )
        
        # Or select from existing files
        dashboard_files = list(Path("00_LookML_Dashboards").glob("*.lookml"))
        if dashboard_files:
            st.markdown("**Or select from existing files:**")
            selected_file = st.selectbox(
                "Choose dashboard file:",
                options=dashboard_files,
                format_func=lambda x: x.name
            )
            
            if st.button("Load Selected File"):
                dashboard = st.session_state.analyzer.load_dashboard_file(str(selected_file))
                if dashboard:
                    st.success(f"Loaded: {dashboard['name']}")
                    st.session_state.current_dashboard = dashboard
                    st.session_state.filter_analysis = st.session_state.analyzer.analyze_filter_links(dashboard)
        
        # Load sample data
        if st.button("Load Sample Data"):
            sample_file = "00_LookML_Dashboards/pricing_filing_analysis.dashboard.lookml"
            if Path(sample_file).exists():
                dashboard = st.session_state.analyzer.load_dashboard_file(sample_file)
                if dashboard:
                    st.success(f"Loaded sample: {dashboard['name']}")
                    st.session_state.current_dashboard = dashboard
                    st.session_state.filter_analysis = st.session_state.analyzer.analyze_filter_links(dashboard)
            else:
                st.error("Sample file not found")
    
    # Main content
    if st.session_state.current_dashboard and st.session_state.filter_analysis:
        dashboard = st.session_state.current_dashboard
        filter_analysis = st.session_state.filter_analysis
        
        # Summary metrics
        metrics = st.session_state.analyzer.create_summary_metrics(dashboard, filter_analysis)
        
        # Display metrics
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("Total Filters", metrics['total_filters'])
        with col2:
            st.metric("Visualizations", metrics['total_visualizations'])
        with col3:
            st.metric("Avg Coverage", f"{metrics['avg_coverage']:.1f}%")
        with col4:
            st.metric("Complete Links", metrics['complete_links'])
        with col5:
            st.metric("Partial Links", metrics['partial_links'])
        with col6:
            st.metric("Missing Links", metrics['missing_links'])
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🌐 Network Visualization", "📊 Coverage Analysis", "📋 Filter Details", "📄 Export"])
        
        with tab1:
            st.header("Interactive Network Visualization")
            st.markdown("Click and drag nodes to explore filter connections")
            
            # Create PyVis network
            net = st.session_state.analyzer.create_pyvis_network(dashboard, filter_analysis)
            
            # Save to temporary file and display
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                net.save_graph(f.name)
                html_file = f.name
            
            # Read and display
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            st.components.v1.html(html_content, height=600)
            
            # Clean up
            os.unlink(html_file)
            
            # Legend
            st.markdown("""
            **Legend:**
            - 🟢 **Green**: Complete links (100% coverage)
            - 🟠 **Orange**: Partial links (partial coverage)
            - 🔴 **Red**: Missing links (0% coverage)
            - 🔵 **Blue**: Visualizations
            """)
        
        with tab2:
            st.header("Coverage Analysis")
            
            # Coverage chart
            coverage_fig = st.session_state.analyzer.create_coverage_chart(filter_analysis)
            st.plotly_chart(coverage_fig, use_container_width=True)
            
            # Status distribution
            status_counts = pd.DataFrame(filter_analysis)['status'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Status Distribution")
                fig_pie = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    color_discrete_map={
                        'complete': '#4caf50',
                        'partial': '#ff9800',
                        'missing': '#ff6b6b'
                    }
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("Coverage Statistics")
                df = pd.DataFrame(filter_analysis)
                
                st.metric("Average Coverage", f"{df['coverage_percentage'].mean():.1f}%")
                st.metric("Median Coverage", f"{df['coverage_percentage'].median():.1f}%")
                st.metric("Min Coverage", f"{df['coverage_percentage'].min():.1f}%")
                st.metric("Max Coverage", f"{df['coverage_percentage'].max():.1f}%")
        
        with tab3:
            st.header("Filter Details")
            
            # Filter selection
            filter_options = [f['filter_title'] for f in filter_analysis]
            selected_filter = st.selectbox("Select a filter to view details:", filter_options)
            
            if selected_filter:
                filter_info = next(f for f in filter_analysis if f['filter_title'] == selected_filter)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Filter Information")
                    st.write(f"**Title:** {filter_info['filter_title']}")
                    st.write(f"**Type:** {filter_info['filter_type']}")
                    st.write(f"**Field:** {filter_info['field']}")
                    st.write(f"**Coverage:** {filter_info['coverage_percentage']:.1f}%")
                    st.write(f"**Status:** {filter_info['status'].title()}")
                    st.write(f"**Links:** {filter_info['link_count']} visualizations")
                
                with col2:
                    st.subheader("Linked Visualizations")
                    if filter_info['linked_visualizations']:
                        for viz in filter_info['linked_visualizations']:
                            st.write(f"• {viz}")
                    else:
                        st.write("No visualizations linked")
                    
                    if filter_info['listens_to_filters']:
                        st.subheader("Filter Dependencies")
                        for dep in filter_info['listens_to_filters']:
                            st.write(f"• {dep}")
            
            # Filter table
            st.subheader("All Filters Summary")
            df = pd.DataFrame(filter_analysis)
            st.dataframe(
                df[['filter_title', 'filter_type', 'coverage_percentage', 'link_count', 'status']],
                use_container_width=True
            )
        
        with tab4:
            st.header("Export Results")
            
            # Export options
            export_format = st.selectbox("Export format:", ["JSON", "CSV", "Markdown"])
            
            if st.button("Generate Export"):
                if export_format == "JSON":
                    export_data = {
                        'dashboard': dashboard,
                        'filter_analysis': filter_analysis,
                        'summary_metrics': metrics
                    }
                    json_str = json.dumps(export_data, indent=2)
                    st.download_button(
                        "Download JSON",
                        json_str,
                        file_name="filter_analysis.json",
                        mime="application/json"
                    )
                
                elif export_format == "CSV":
                    df = pd.DataFrame(filter_analysis)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        file_name="filter_analysis.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "Markdown":
                    markdown_content = f"""# LookML Filter Link Analysis Report

## Dashboard: {dashboard['name']}

### Summary
- **Total Filters**: {metrics['total_filters']}
- **Total Visualizations**: {metrics['total_visualizations']}
- **Average Coverage**: {metrics['avg_coverage']:.1f}%
- **Complete Links**: {metrics['complete_links']}
- **Partial Links**: {metrics['partial_links']}
- **Missing Links**: {metrics['missing_links']}

### Filter Details
"""
                    for filter_info in filter_analysis:
                        markdown_content += f"""
#### {filter_info['filter_title']}
- **Type**: {filter_info['filter_type']}
- **Coverage**: {filter_info['coverage_percentage']:.1f}%
- **Status**: {filter_info['status'].title()}
- **Links**: {filter_info['link_count']} visualizations
"""
                    
                    st.download_button(
                        "Download Markdown",
                        markdown_content,
                        file_name="filter_analysis.md",
                        mime="text/markdown"
                    )
    
    else:
        st.info("👆 Please load a dashboard file to begin analysis")
        
        # Show sample data info
        st.markdown("""
        ### Sample Data Available
        The application includes sample data from your `pricing_filing_analysis.dashboard.lookml` file.
        Click "Load Sample Data" in the sidebar to explore the analysis.
        """)

if __name__ == "__main__":
    main()
