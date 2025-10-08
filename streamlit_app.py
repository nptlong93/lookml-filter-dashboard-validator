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
    page_title="LookML Filter Dashboard Validator",
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
                                # Use single_value_title as fallback if title is empty
                                title = element_data.get('title', '')
                                if not title:
                                    title = element_data.get('single_value_title', '')
                                
                                visualizations.append({
                                    'title': title,
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
    
    def create_pyvis_network(self, dashboard: Dict, filter_analysis: List[Dict], 
                           min_coverage: float = 0, max_links: int = 100, 
                           layout: str = "barnesHut", show_filters: bool = True, 
                           show_visualizations: bool = True, 
                           min_node_size: int = 10, max_node_size: int = 50) -> Network:
        """Create PyVis network visualization with filtering options"""
        net = Network(
            height="600px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#333333",
            directed=True
        )
        
        # Configure physics based on layout
        if layout == "barnesHut":
            physics_config = {
                "enabled": True,
                "stabilization": {"iterations": 100},
                "barnesHut": {
                    "gravitationalConstant": -2000,
                    "centralGravity": 0.1,
                    "springLength": 200,
                    "springConstant": 0.05,
                    "damping": 0.09
                }
            }
        elif layout == "forceAtlas2Based":
            physics_config = {
                "enabled": True,
                "stabilization": {"iterations": 100},
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 100,
                    "springConstant": 0.08,
                    "damping": 0.4
                }
            }
        else:  # hierarchical
            physics_config = {
                "enabled": True,
                "hierarchicalRepulsion": {
                    "centralGravity": 0.0,
                    "springLength": 100,
                    "springConstant": 0.01,
                    "nodeDistance": 120,
                    "damping": 0.09
                }
            }
        
        net.set_options(f"""
        {{
            "physics": {json.dumps(physics_config)},
            "interaction": {{
                "hover": true,
                "tooltipDelay": 200,
                "hideEdgesOnDrag": true,
                "hideNodesOnDrag": false
            }},
            "nodes": {{
                "font": {{
                    "size": 12,
                    "color": "#333333"
                }},
                "borderWidth": 1,
                "borderWidthSelected": 3
            }},
            "edges": {{
                "font": {{
                    "size": 10,
                    "color": "#666666"
                }},
                "smooth": {{
                    "enabled": true,
                    "type": "continuous"
                }}
            }}
        }}
        """)
        
        # Filter data based on parameters
        filtered_analysis = [
            f for f in filter_analysis 
            if f['coverage_percentage'] >= min_coverage and f['link_count'] <= max_links
        ]
        
        # Add filter nodes
        if show_filters:
            for filter_info in filtered_analysis:
                status = filter_info['status']
                color = filter_info['status_color']
                
                # Node size based on link count with scaling
                size = min(max_node_size, max(min_node_size, filter_info['link_count'] * 2))
                
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
        if show_visualizations:
            for viz in dashboard['visualizations']:
                filter_count = len(viz['listen'])
                size = min(max_node_size, max(min_node_size, filter_count * 2))
                
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
        
        # Add edges for filter-to-visualization links (only for visible nodes)
        if show_filters and show_visualizations:
            for viz in dashboard['visualizations']:
                for filter_title in viz['listen'].keys():
                    # Only add edge if both nodes are visible
                    filter_visible = any(f['filter_title'] == filter_title for f in filtered_analysis)
                    if filter_visible:
                        net.add_edge(
                            filter_title,
                            viz['title'],
                            color='#667eea',
                            width=2,
                            title=f"Filter Link: {filter_title} → {viz['title']}"
                        )
        
        # Add edges for filter dependencies (only for visible filters)
        if show_filters:
            for filter_info in filtered_analysis:
                for dep in filter_info['listens_to_filters']:
                    # Only add edge if dependency filter is also visible
                    dep_visible = any(f['filter_title'] == dep for f in filtered_analysis)
                    if dep_visible:
                        net.add_edge(
                            dep,
                            filter_info['filter_title'],
                            color='#96ceb4',
                            width=1,
                            title=f"Filter Dependency: {dep} → {filter_info['filter_title']}"
                        )
        
        return net
    
    def create_erd_network(self, dashboard: Dict, filter_analysis: List[Dict], 
                          min_coverage: float = 0, max_links: int = 100, 
                          show_filters: bool = True, show_visualizations: bool = True,
                          value_name_filter: str = "") -> Network:
        """Create proper database-style ERD with table-like entities"""
        net = Network(
            height="700px",
            width="100%",
            bgcolor="#f8f9fa",
            font_color="#333333",
            directed=True
        )
        
        # Configure physics for proper database ERD layout
        net.set_options("""
        {
            "physics": {
                "enabled": true,
                "stabilization": {"iterations": 500},
                "hierarchicalRepulsion": {
                    "centralGravity": 0.0,
                    "springLength": 400,
                    "springConstant": 0.001,
                    "nodeDistance": 400,
                    "damping": 0.1
                }
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 300,
                "hideEdgesOnDrag": false,
                "hideNodesOnDrag": false,
                "zoomView": true,
                "dragView": true
            },
            "nodes": {
                "shape": "box",
                "font": {
                    "size": 12,
                    "color": "#333333",
                    "face": "monospace"
                },
                "borderWidth": 3,
                "borderWidthSelected": 5,
                "shadow": {
                    "enabled": true,
                    "color": "rgba(0,0,0,0.3)",
                    "size": 8,
                    "x": 3,
                    "y": 3
                },
                "margin": 30,
                "widthConstraint": {
                    "minimum": 200,
                    "maximum": 300
                },
                "heightConstraint": {
                    "minimum": 100,
                    "maximum": 200
                }
            },
            "edges": {
                "font": {
                    "size": 10,
                    "color": "#444444",
                    "face": "arial"
                },
                "smooth": {
                    "enabled": true,
                    "type": "straightCross",
                    "roundness": 0.0
                },
                "arrows": {
                    "to": {
                        "enabled": true,
                        "scaleFactor": 1.5,
                        "type": "arrow"
                    }
                },
                "length": 300,
                "width": 3,
                "color": {
                    "color": "#666666",
                    "highlight": "#007bff"
                }
            }
        }
        """)
        
        # Filter data based on parameters
        filtered_analysis = [
            f for f in filter_analysis 
            if f['coverage_percentage'] >= min_coverage and f['link_count'] <= max_links
        ]
        
        # Apply value name filter if provided
        if value_name_filter:
            filtered_analysis = [
                f for f in filtered_analysis 
                if value_name_filter.lower() in f['filter_title'].lower() or 
                   value_name_filter.lower() in f.get('field', '').lower()
            ]
        
        # Add filter nodes as database tables
        if show_filters:
            for filter_info in filtered_analysis:
                status = filter_info['status']
                color = filter_info['status_color']
                
                # Create database table-style label
                table_header = f"┌─ FILTER: {filter_info['filter_title']} ─┐"
                table_separator = "├" + "─" * (len(table_header) - 2) + "┤"
                table_type = f"│ Type: {filter_info['filter_type']:<20} │"
                table_field = f"│ Field: {filter_info['field'][:20]:<20} │"
                table_coverage = f"│ Coverage: {filter_info['coverage_percentage']:.1f}%{'':<12} │"
                table_links = f"│ Links: {filter_info['link_count']:<22} │"
                table_status = f"│ Status: {status.upper():<20} │"
                table_footer = "└" + "─" * (len(table_header) - 2) + "┘"
                
                label = f"{table_header}\n{table_separator}\n{table_type}\n{table_field}\n{table_coverage}\n{table_links}\n{table_status}\n{table_footer}"
                
                net.add_node(
                    filter_info['filter_title'],
                    label=label,
                    color=color,
                    size=40,  # Larger for table format
                    title=f"""
                    Filter: {filter_info['filter_title']}
                    Type: {filter_info['filter_type']}
                    Field: {filter_info['field']}
                    Coverage: {filter_info['coverage_percentage']:.1f}%
                    Links: {filter_info['link_count']}
                    Status: {status.title()}
                    """,
                    group="filter",
                    shape="box"
                )
        
        # Add visualization nodes as database tables
        if show_visualizations:
            for viz in dashboard['visualizations']:
                filter_count = len(viz['listen'])
                
                # Create database table-style label for visualizations
                table_header = f"┌─ VIZ: {viz['title'][:25]} ─┐"
                table_separator = "├" + "─" * (len(table_header) - 2) + "┤"
                table_type = f"│ Type: {viz['type']:<20} │"
                table_explore = f"│ Explore: {viz['explore'][:18]:<18} │"
                table_filters = f"│ Filters: {filter_count:<21} │"
                table_position = f"│ Pos: {viz['row']},{viz['col']}{'':<23} │"
                table_footer = "└" + "─" * (len(table_header) - 2) + "┘"
                
                label = f"{table_header}\n{table_separator}\n{table_type}\n{table_explore}\n{table_filters}\n{table_position}\n{table_footer}"
                
                net.add_node(
                    viz['title'],
                    label=label,
                    color='#2196f3',
                    size=40,  # Larger for table format
                    title=f"""
                    Visualization: {viz['title']}
                    Type: {viz['type']}
                    Explore: {viz['explore']}
                    Filters: {filter_count}
                    Position: Row {viz['row']}, Col {viz['col']}
                    """,
                    group="visualization",
                    shape="box"
                )
        
        # Add edges for filter-to-visualization links (only for visible nodes)
        if show_filters and show_visualizations:
            for viz in dashboard['visualizations']:
                for filter_title in viz['listen'].keys():
                    # Only add edge if both nodes are visible
                    filter_visible = any(f['filter_title'] == filter_title for f in filtered_analysis)
                    if filter_visible:
                        net.add_edge(
                            filter_title,
                            viz['title'],
                            color='#667eea',
                            width=2,
                            title=f"Filter Link: {filter_title} → {viz['title']}"
                        )
        
        # Add edges for filter dependencies (only for visible filters)
        if show_filters:
            for filter_info in filtered_analysis:
                for dep in filter_info['listens_to_filters']:
                    # Only add edge if dependency filter is also visible
                    dep_visible = any(f['filter_title'] == dep for f in filtered_analysis)
                    if dep_visible:
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
        
        # Color based on status - need to match the sorted order
        color_map = {info['filter_title']: info['status_color'] for info in filter_analysis}
        colors = [color_map[title] for title in df_sorted['filter_title']]
        
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
    # Initialize required session_state keys
    if 'current_dashboard' not in st.session_state:
        st.session_state.current_dashboard = None
    if 'filter_analysis' not in st.session_state:
        st.session_state.filter_analysis = []
    
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
        
        # Handle uploaded file
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.lookml') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Load the uploaded dashboard
            dashboard = st.session_state.analyzer.load_dashboard_file(tmp_file_path)
            if dashboard:
                st.success(f"✅ Loaded: {dashboard['name']}")
                st.session_state.current_dashboard = dashboard
                st.session_state.filter_analysis = st.session_state.analyzer.analyze_filter_links(dashboard)
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
        
        # Or select from existing files (prefer sample_dashboards if available)
        default_dash_dir = Path("00_LookML_Dashboards")
        sample_dash_dir = Path("sample_dashboards")
        search_dir = sample_dash_dir if sample_dash_dir.exists() else default_dash_dir
        dashboard_files = list(search_dir.glob("*.lookml"))
        
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
        else:
            st.info("📁 No sample dashboard files found. Please upload a LookML file above to get started.")
        
    
    # Main content
    if st.session_state.current_dashboard and st.session_state.filter_analysis:
        dashboard = st.session_state.current_dashboard
        filter_analysis = st.session_state.filter_analysis
        
        # Summary metrics
        metrics = st.session_state.analyzer.create_summary_metrics(dashboard, filter_analysis)
        
        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Filters", metrics['total_filters'])
        with col2:
            st.metric("Visualizations", metrics['total_visualizations'])
        with col3:
            st.metric("Complete Links", metrics['complete_links'])
        with col4:
            st.metric("Partial Links", metrics['partial_links'])
        with col5:
            st.metric("Missing Links", metrics['missing_links'])
        
        # Tabs
        tab1, tab2 = st.tabs(["📊 Filter Analysis & Details", "📄 Export"])
        
        with tab1:
            st.header("Filter Analysis & Details")
            
            # Coverage chart
            coverage_fig = st.session_state.analyzer.create_coverage_chart(filter_analysis)
            st.plotly_chart(coverage_fig, use_container_width=True)
            
            st.markdown("---")
            
            # Explore Statistics Section
            st.subheader("📊 Explore Statistics")
            
            # Calculate explore statistics
            explore_stats = {}
            for viz in dashboard['visualizations']:
                explore = viz['explore']
                if explore not in explore_stats:
                    explore_stats[explore] = {
                        'total_tiles': 0,
                        'tile_has_filter': 0,
                        'tile_has_no_filter': 0,
                        'tiles': []
                    }
                explore_stats[explore]['total_tiles'] += 1
                explore_stats[explore]['tiles'].append(viz['title'])
            
            # Calculate linked tiles per explore (unique tiles that have at least one filter)
            for explore, stats in explore_stats.items():
                tile_has_filter = set()
                for viz in dashboard['visualizations']:
                    if viz['explore'] == explore and viz['listen']:  # Has at least one filter
                        tile_has_filter.add(viz['title'])
                stats['tile_has_filter'] = len(tile_has_filter)
            
            # Calculate unlinked tiles per explore
            for explore, stats in explore_stats.items():
                stats['tile_has_no_filter'] = stats['total_tiles'] - stats['tile_has_filter']
            
            # Display explore statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Total Explores Used:** {len(explore_stats)}")
                st.write(f"**Total Tiles:** {sum(stats['total_tiles'] for stats in explore_stats.values())}")
            
            with col2:
                # Show explore breakdown
                for explore, stats in explore_stats.items():
                    coverage_pct = (stats['tile_has_filter'] / stats['total_tiles'] * 100) if stats['total_tiles'] > 0 else 0
                    st.write(f"**{explore}:** {stats['total_tiles']} tiles ({coverage_pct:.1f}% filter coverage)")
            
            # Detailed explore breakdown table
            st.subheader("📋 Explore Breakdown")
            explore_data = []
            for explore, stats in explore_stats.items():
                coverage_pct = (stats['tile_has_filter'] / stats['total_tiles'] * 100) if stats['total_tiles'] > 0 else 0
                explore_data.append({
                    'Explore': explore,
                    'Total Tiles': stats['total_tiles'],
                    'Tile has filter': stats['tile_has_filter'],
                    'Tile has no filter': stats['tile_has_no_filter'],
                    'Coverage %': f"{coverage_pct:.1f}%"
                })
            
            if explore_data:
                df_explore = pd.DataFrame(explore_data)
                st.dataframe(df_explore, use_container_width=True)
            
            st.markdown("---")
            
            # Filter Details Section
            st.subheader("🔍 Individual Filter Analysis")
            st.markdown("Select a filter below to see detailed information about its connections and missing visualizations.")
            
            # Filter selection
            filter_options = [f['filter_title'] for f in filter_analysis]
            selected_filter = st.selectbox("Select a filter to view details:", filter_options)
            
            # Quick summary of all filters
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                complete_filters = len([f for f in filter_analysis if f['status'] == 'complete'])
                st.metric("Complete Filters", complete_filters)
            with col2:
                partial_filters = len([f for f in filter_analysis if f['status'] == 'partial'])
                st.metric("Partial Filters", partial_filters)
            with col3:
                missing_filters = len([f for f in filter_analysis if f['status'] == 'missing'])
                st.metric("Missing Filters", missing_filters)
            st.markdown("---")
            
            if selected_filter:
                filter_info = next(f for f in filter_analysis if f['filter_title'] == selected_filter)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Filter Information")
                    st.write(f"**Title:** {filter_info['filter_title']}")
                    st.write(f"**Type:** {filter_info['filter_type']}")
                    st.write(f"**Field:** {filter_info['field']}")
                    
                    # Enhanced coverage display
                    total_viz = len(dashboard['visualizations'])
                    linked_count = filter_info['link_count']
                    unlinked_count = total_viz - linked_count
                    
                    st.write(f"**Coverage:** {filter_info['coverage_percentage']:.1f}%")
                    st.write(f"**Status:** {filter_info['status'].title()}")
                    
                    # Calculate explore coverage for this filter
                    linked_explores = set()
                    for viz_title in filter_info['linked_visualizations']:
                        viz_details = next((v for v in dashboard['visualizations'] if v['title'] == viz_title), None)
                        if viz_details and viz_details['explore']:
                            linked_explores.add(viz_details['explore'])
                    
                    # Get total explores in dashboard
                    all_explores = set()
                    for viz in dashboard['visualizations']:
                        if viz['explore']:
                            all_explores.add(viz['explore'])
                    
                    # Show covered explores as a list
                    if linked_explores:
                        st.write(f"**Covers Explores:** {', '.join(sorted(linked_explores))}")
                    else:
                        st.write("**Covers Explores:** None")
                    
                    # Create charts for visualization and explore coverage
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        # Visualization coverage pie chart
                        viz_data = {
                            'Linked': linked_count,
                            'Unlinked': unlinked_count
                        }
                        fig_viz = go.Figure(data=[go.Pie(
                            labels=list(viz_data.keys()),
                            values=list(viz_data.values()),
                            hole=0.4,
                            marker_colors=['#4CAF50', '#FF9800']
                        )])
                        fig_viz.update_layout(
                            title=f"Visualization Coverage<br><sub>{linked_count} out of {total_viz}</sub>",
                            showlegend=True,
                            height=300,
                            margin=dict(t=50, b=0, l=0, r=0)
                        )
                        st.plotly_chart(fig_viz, use_container_width=True)
                    
                    with col_chart2:
                        # Explore coverage pie chart
                        explore_data = {
                            'Covered': len(linked_explores),
                            'Not Covered': len(all_explores) - len(linked_explores)
                        }
                        fig_explore = go.Figure(data=[go.Pie(
                            labels=list(explore_data.keys()),
                            values=list(explore_data.values()),
                            hole=0.4,
                            marker_colors=['#2196F3', '#FFC107']
                        )])
                        fig_explore.update_layout(
                            title=f"Explore Coverage<br><sub>{len(linked_explores)} out of {len(all_explores)}</sub>",
                            showlegend=True,
                            height=300,
                            margin=dict(t=50, b=0, l=0, r=0)
                        )
                        st.plotly_chart(fig_explore, use_container_width=True)
                    
                    # Visual coverage indicator
                    if filter_info['coverage_percentage'] == 100:
                        st.success("🎉 Complete coverage - all visualizations linked!")
                    elif filter_info['coverage_percentage'] > 50:
                        st.warning(f"⚠️ Partial coverage - {unlinked_count} visualizations not applied to this filter")
                    else:
                        st.error(f"❌ Low coverage - {unlinked_count} visualizations not applied to this filter")
                
                with col2:
                    st.subheader("Linked Visualizations")
                    if filter_info['linked_visualizations']:
                        for viz_title in filter_info['linked_visualizations']:
                            # Find the visualization details to get explore info
                            viz_details = next((v for v in dashboard['visualizations'] if v['title'] == viz_title), None)
                            if viz_details and viz_details['explore']:
                                st.write(f"✅ {viz_title} *({viz_details['explore']})*")
                            else:
                                st.write(f"✅ {viz_title}")
                    else:
                        st.write("No visualizations linked")
                    
                    # Show unlinked visualizations for this specific filter
                    all_viz_titles = [viz['title'] for viz in dashboard['visualizations']]
                    linked_viz_titles = filter_info['linked_visualizations']
                    unlinked_viz_titles = [viz for viz in all_viz_titles if viz not in linked_viz_titles]
                    
                    if unlinked_viz_titles:
                        st.subheader("❌ Unlinked Visualizations")
                        st.write(f"*This filter is not applied to {len(unlinked_viz_titles)} out of {len(all_viz_titles)} visualizations*")
                        for viz_title in unlinked_viz_titles:
                            # Find the visualization details to get explore info
                            viz_details = next((v for v in dashboard['visualizations'] if v['title'] == viz_title), None)
                            if viz_details and viz_details['explore']:
                                st.write(f"• {viz_title} *({viz_details['explore']})*")
                            else:
                                st.write(f"• {viz_title}")
                    
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
        
        with tab2:
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
        
        # Show upload instructions
        st.markdown("""
        ### Get Started
        
        **Option 1: Upload a LookML File**
        - Use the file uploader in the sidebar to upload your `.lookml` dashboard file
        - Supported formats: `.lookml`, `.yaml`, `.yml`
        
        **Option 2: Use Sample Files (if available)**
        - If sample dashboard files are available, you can select them from the dropdown in the sidebar
        
        **What You'll Get:**
        - Interactive filter coverage analysis
        - Explore statistics and breakdown
        - Individual filter analysis with charts
        - Export capabilities for your analysis results
        """)
        
        # Show example of what the app does
        st.markdown("""
        ### What This App Does
        
        This LookML Filter Dashboard Validator helps you:
        
        📊 **Analyze Filter Coverage**
        - See which visualizations are linked to each filter
        - Identify missing filter connections
        - Get coverage percentages and statistics
        
        🔍 **Explore Analysis**
        - Understand how many explores your dashboard uses
        - See filter coverage across different explores
        - Identify which explores need more filter attention
        
        📈 **Interactive Visualizations**
        - Pie charts showing coverage breakdown
        - Bar charts for filter analysis
        - Detailed individual filter insights
        
        📄 **Export Results**
        - Download analysis as JSON, CSV, or Markdown
        - Share findings with your team
        """)

if __name__ == "__main__":
    main()
