#!/usr/bin/env python3
"""
Test script for LookML Filter Link Analyzer

This script tests the core analysis functionality without requiring
Streamlit or PyVis packages.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional

class LookMLAnalyzer:
    """LookML Dashboard Filter Link Analyzer - Core functionality only"""
    
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
                                'explore': filter_data.get('explore', '')
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
                                    'fields': element_data.get('fields', [])
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
            print(f"Error loading dashboard file: {str(e)}")
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
    """Test the analyzer functionality"""
    print("🔗 LookML Filter Link Analyzer - Test")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = LookMLAnalyzer()
    
    # Load dashboard
    dashboard_file = "00_LookML_Dashboards/pricing_filing_analysis.dashboard.lookml"
    print(f"📁 Loading dashboard: {dashboard_file}")
    
    dashboard = analyzer.load_dashboard_file(dashboard_file)
    if not dashboard:
        print("❌ Failed to load dashboard")
        return
    
    print(f"✅ Loaded: {dashboard['name']}")
    print(f"📊 Filters: {len(dashboard['filters'])}")
    print(f"📈 Visualizations: {len(dashboard['visualizations'])}")
    
    # Analyze filter links
    print("\n🔍 Analyzing filter links...")
    filter_analysis = analyzer.analyze_filter_links(dashboard)
    
    # Get summary metrics
    metrics = analyzer.create_summary_metrics(dashboard, filter_analysis)
    
    # Display results
    print("\n📊 Summary Metrics:")
    print(f"  Total Filters: {metrics['total_filters']}")
    print(f"  Total Visualizations: {metrics['total_visualizations']}")
    print(f"  Average Coverage: {metrics['avg_coverage']:.1f}%")
    print(f"  Complete Links: {metrics['complete_links']}")
    print(f"  Partial Links: {metrics['partial_links']}")
    print(f"  Missing Links: {metrics['missing_links']}")
    
    # Show filter details
    print("\n🔍 Filter Analysis:")
    for filter_info in filter_analysis[:5]:  # Show first 5
        print(f"  {filter_info['filter_title']}: {filter_info['coverage_percentage']:.1f}% ({filter_info['status']})")
    
    if len(filter_analysis) > 5:
        print(f"  ... and {len(filter_analysis) - 5} more filters")
    
    # Show issues
    print("\n🚨 Issues Found:")
    if metrics['missing_links'] > 0:
        missing_filters = [f['filter_title'] for f in filter_analysis if f['status'] == 'missing']
        print(f"  {metrics['missing_links']} filters not linked to any visualization: {', '.join(missing_filters[:3])}")
    
    if metrics['partial_links'] > 0:
        print(f"  {metrics['partial_links']} filters have partial coverage")
    
    if metrics['avg_coverage'] < 75:
        print(f"  Overall coverage below recommended threshold (75%)")
    
    if metrics['missing_links'] == 0 and metrics['partial_links'] == 0:
        print("  No issues found! All filters are properly linked.")
    
    print("\n✅ Analysis complete!")
    print("🚀 To use the full interactive interface, install requirements and run:")
    print("   pip install -r requirements.txt")
    print("   python run_app.py")

if __name__ == "__main__":
    main()
