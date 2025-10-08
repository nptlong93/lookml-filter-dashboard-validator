# 🔗 LookML Filter Link Visualizer - Streamlit + PyVis

Interactive web application for visualizing and validating LookML dashboard filter links using Streamlit and PyVis.

## 🎯 Problem Solved

**Challenge**: "I'm often seeing the case that some common filter is missed to link to some visualization in Dashboard tile."

**Solution**: Interactive web application that visualizes all filter-to-visualization connections with real-time analysis and validation.

## ✨ Features

### 🌐 **Interactive Network Visualization**
- **PyVis-powered network graphs** with drag-and-drop interaction
- **Color-coded nodes** (Green: Complete, Orange: Partial, Red: Missing, Blue: Visualizations)
- **Hover tooltips** with detailed information
- **Physics-based layout** for optimal node positioning
- **Real-time filtering** and exploration

### 📊 **Comprehensive Analysis**
- **Coverage analysis** with horizontal bar charts
- **Status distribution** pie charts
- **Statistical metrics** (average, median, min/max coverage)
- **Filter dependency mapping**
- **Missing link identification**

### 🎛️ **Interactive Controls**
- **File upload** for custom dashboard files
- **Sample data loading** for quick testing
- **Filter selection** for detailed analysis
- **Real-time filtering** and search
- **Responsive design** for all screen sizes

### 📄 **Export Capabilities**
- **JSON export** for programmatic use
- **CSV export** for spreadsheet analysis
- **Markdown export** for documentation
- **One-click download** functionality

## 🚀 Quick Start

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Launch Application
```bash
python run_app.py
```

Or directly with Streamlit:
```bash
streamlit run streamlit_app.py
```

### 3. Open in Browser
The application will automatically open at `http://localhost:8501`

## 📁 File Structure

```
LookML_one_pricing_spoke/
├── streamlit_app.py          # Main Streamlit application
├── run_app.py               # Launcher script
├── requirements.txt         # Python dependencies
├── README_Streamlit.md      # This documentation
├── 00_LookML_Dashboards/    # Dashboard files
│   ├── pricing_filing_analysis.dashboard.lookml
│   └── tiger_pricing_performance.dashboard.lookml
└── ... (other files)
```

## 🎮 How to Use

### **Step 1: Load Dashboard**
- **Upload file**: Use the file uploader in the sidebar
- **Select existing**: Choose from existing dashboard files
- **Load sample**: Click "Load Sample Data" for quick testing

### **Step 2: Explore Network**
- **Navigate to "Network Visualization" tab**
- **Drag nodes** to rearrange the layout
- **Hover over nodes** to see detailed information
- **Click and drag** to explore connections

### **Step 3: Analyze Coverage**
- **Navigate to "Coverage Analysis" tab**
- **View coverage charts** and statistics
- **Identify patterns** in filter linking
- **Spot missing connections**

### **Step 4: Review Details**
- **Navigate to "Filter Details" tab**
- **Select specific filters** to view details
- **See linked visualizations** and dependencies
- **Review comprehensive filter table**

### **Step 5: Export Results**
- **Navigate to "Export" tab**
- **Choose export format** (JSON, CSV, Markdown)
- **Download results** for further analysis

## 🔧 Technical Details

### **Architecture**
- **Frontend**: Streamlit (Python web framework)
- **Visualization**: PyVis (interactive network graphs)
- **Charts**: Plotly (interactive charts and graphs)
- **Data Processing**: Pandas (data manipulation)
- **File Parsing**: PyYAML (YAML file parsing)

### **Key Components**
1. **LookMLAnalyzer**: Core analysis logic
2. **Network Visualization**: PyVis-based interactive graphs
3. **Coverage Analysis**: Plotly-based charts
4. **Export System**: Multiple format support
5. **UI Components**: Streamlit widgets and layouts

### **Performance**
- **Real-time analysis** of dashboard files
- **Efficient network rendering** with PyVis
- **Responsive UI** with Streamlit
- **Memory efficient** data processing

## 📊 Sample Analysis Results

Based on your `pricing_filing_analysis.dashboard.lookml`:

- **Total Filters**: 20
- **Total Visualizations**: 11
- **Average Coverage**: 66.4%
- **Complete Links**: 1 filter (Expiration Date)
- **Partial Links**: 19 filters
- **Missing Links**: 0 filters

### **Key Issues Identified**
1. **Service filters missing from DMT charts** (Trade, Service Scope Group/Code)
2. **Customer filters missing from MRG charts** (9 customer-related filters)
3. **Overall coverage below threshold** (66.4% vs 75% recommended)

## 🎨 Customization

### **Network Styling**
Modify the PyVis network configuration in `create_pyvis_network()`:
```python
net.set_options("""
{
    "physics": {
        "enabled": true,
        "stabilization": {"iterations": 100}
    }
}
""")
```

### **Chart Colors**
Update color schemes in the analysis functions:
```python
colors = {
    'complete': '#4caf50',
    'partial': '#ff9800',
    'missing': '#ff6b6b'
}
```

### **UI Layout**
Modify the Streamlit layout in the main application:
```python
col1, col2, col3 = st.columns(3)
```

## 🔍 Troubleshooting

### **Common Issues**

1. **"Module not found" errors**
   - Run: `pip install -r requirements.txt`

2. **Port already in use**
   - Change port in `run_app.py`: `--server.port 8502`

3. **File not found errors**
   - Ensure dashboard files are in `00_LookML_Dashboards/` directory

4. **Network not displaying**
   - Check browser console for JavaScript errors
   - Try refreshing the page

### **Debug Mode**
Run with debug information:
```bash
streamlit run streamlit_app.py --logger.level debug
```

## 🚀 Advanced Usage

### **Custom Dashboard Loading**
```python
analyzer = LookMLAnalyzer()
dashboard = analyzer.load_dashboard_file("path/to/dashboard.lookml")
analysis = analyzer.analyze_filter_links(dashboard)
```

### **Programmatic Network Creation**
```python
net = analyzer.create_pyvis_network(dashboard, analysis)
net.save_graph("output.html")
```

### **Batch Processing**
```python
for dashboard_file in Path("dashboards/").glob("*.lookml"):
    dashboard = analyzer.load_dashboard_file(str(dashboard_file))
    analysis = analyzer.analyze_filter_links(dashboard)
    # Process results...
```

## 📈 Benefits

### **For Developers**
- **Interactive exploration** of filter relationships
- **Real-time validation** of dashboard links
- **Visual debugging** of complex filter dependencies
- **Export capabilities** for further analysis

### **For Teams**
- **Shared understanding** of dashboard structure
- **Collaborative analysis** through web interface
- **Documentation generation** through exports
- **Quality assurance** through validation

### **For Organizations**
- **Standardized analysis** process
- **Scalable solution** for multiple dashboards
- **Integration ready** with existing workflows
- **Maintainable codebase** with clear structure

## 🔄 Next Steps

1. **Run the application** and explore your dashboard
2. **Identify missing links** using the network visualization
3. **Export results** for team review
4. **Fix missing links** in your LookML files
5. **Re-run analysis** to validate improvements
6. **Integrate into workflow** for regular validation

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments
3. Check Streamlit and PyVis documentation
4. Create an issue with detailed error information

---

**This Streamlit + PyVis solution provides an interactive, user-friendly way to visualize and validate LookML dashboard filter links, directly addressing your challenge of ensuring all common filters are properly connected to visualizations!** 🎯
