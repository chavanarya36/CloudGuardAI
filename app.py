import streamlit as st
import pandas as pd
import json
import io
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path
from utils.prediction_engine import PredictionEngine

# Page configuration
st.set_page_config(
    page_title="CloudGuard AI - Advanced Infrastructure Risk Scanner",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced Hi-Tech Styling with Dark Theme and Animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Global Dark Theme */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Animated Header with Glow Effect */
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(45deg, #00d4ff, #0099cc, #007acc, #0056b3);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        animation: gradientShift 3s ease-in-out infinite;
        text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .sub-header {
        font-size: 1.4rem;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
        letter-spacing: 0.5px;
    }
    
    /* Futuristic Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.1), transparent);
        transition: left 0.5s;
    }
    
    .metric-card:hover::before {
        left: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 16px 48px rgba(0, 212, 255, 0.2);
        border-color: rgba(0, 212, 255, 0.4);
    }
    
    /* Risk Status Indicators */
    .risk-high {
        color: #ff4757;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(255, 71, 87, 0.5);
        animation: pulse 2s infinite;
    }
    
    .risk-safe {
        color: #2ed573;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(46, 213, 115, 0.5);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Futuristic Upload Section */
    .upload-section {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(51, 65, 85, 0.6) 100%);
        backdrop-filter: blur(15px);
        padding: 3rem;
        border-radius: 20px;
        border: 2px dashed rgba(0, 212, 255, 0.3);
        margin: 2rem 0;
        position: relative;
        transition: all 0.3s ease;
    }
    
    .upload-section:hover {
        border-color: rgba(0, 212, 255, 0.6);
        box-shadow: 0 0 40px rgba(0, 212, 255, 0.2);
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(148, 163, 184, 0.2);
    }
    
    /* Button Enhancements */
    .stButton > button {
        background: linear-gradient(45deg, #00d4ff, #0099cc);
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4);
        background: linear-gradient(45deg, #0099cc, #007acc);
    }
    
    /* Progress Bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #00d4ff, #0099cc);
        border-radius: 10px;
    }
    
    /* Data Tables */
    .stDataFrame {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Text Colors */
    .stMarkdown, .stText {
        color: #e2e8f0;
    }
    
    /* Metric Widgets */
    .metric-container {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 204, 0.1) 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border: 1px solid rgba(0, 212, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.2);
    }
    
    /* Spinning Loading Animation */
    .loading-spinner {
        border: 3px solid rgba(0, 212, 255, 0.1);
        border-top: 3px solid #00d4ff;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Terminal-like Code Blocks */
    .stCode {
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, rgba(0, 212, 255, 0.1), rgba(0, 153, 204, 0.1));
        border-radius: 8px;
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

def create_risk_gauge(risk_percentage, title="Risk Level"):
    """Create a futuristic risk gauge visualization."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = risk_percentage,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'color': '#e2e8f0', 'size': 16}},
        delta = {'reference': 50, 'increasing': {'color': "#ff4757"}, 'decreasing': {'color': "#2ed573"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickcolor': '#94a3b8', 'tickfont': {'color': '#e2e8f0'}},
            'bar': {'color': "#00d4ff"},
            'bgcolor': "rgba(30, 41, 59, 0.8)",
            'borderwidth': 2,
            'bordercolor': "rgba(0, 212, 255, 0.3)",
            'steps': [
                {'range': [0, 25], 'color': "rgba(46, 213, 115, 0.3)"},
                {'range': [25, 50], 'color': "rgba(255, 193, 7, 0.3)"},
                {'range': [50, 75], 'color': "rgba(255, 152, 0, 0.3)"},
                {'range': [75, 100], 'color': "rgba(255, 71, 87, 0.3)"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 75
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': '#e2e8f0'},
        height=250
    )
    return fig

def create_risk_distribution_chart(results):
    """Create risk distribution histogram."""
    if not results:
        return None
    
    risk_scores = [r['risk_percentage'] for r in results]
    
    fig = px.histogram(
        x=risk_scores,
        nbins=20,
        title="Risk Score Distribution",
        labels={'x': 'Risk Percentage', 'y': 'Number of Files'},
        color_discrete_sequence=['#00d4ff']
    )
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': '#e2e8f0'},
        title_font_color='#e2e8f0',
        xaxis={'gridcolor': 'rgba(148, 163, 184, 0.2)', 'color': '#e2e8f0'},
        yaxis={'gridcolor': 'rgba(148, 163, 184, 0.2)', 'color': '#e2e8f0'}
    )
    
    return fig

def create_top_risks_chart(results, top_n=10):
    """Create horizontal bar chart of top risky files."""
    if not results:
        return None
    
    top_risks = sorted(results, key=lambda x: x['risk_percentage'], reverse=True)[:top_n]
    
    fig = go.Figure(go.Bar(
        y=[Path(r['file_path']).name for r in top_risks],
        x=[r['risk_percentage'] for r in top_risks],
        orientation='h',
        marker=dict(
            color=[r['risk_percentage'] for r in top_risks],
            colorscale='Viridis',
            colorbar=dict(title="Risk %", titlefont={'color': '#e2e8f0'}, tickfont={'color': '#e2e8f0'})
        )
    ))
    
    fig.update_layout(
        title=f"Top {len(top_risks)} Highest Risk Files",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': '#e2e8f0'},
        title_font_color='#e2e8f0',
        xaxis={'gridcolor': 'rgba(148, 163, 184, 0.2)', 'color': '#e2e8f0', 'title': 'Risk Percentage'},
        yaxis={'color': '#e2e8f0', 'title': 'Files'},
        height=400
    )
    
    return fig

def create_metrics_dashboard(model_info, summary=None):
    """Create an advanced metrics dashboard."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="🎯 PR-AUC Score",
            value=f"{model_info['pr_auc']:.4f}",
            delta=f"+{(model_info['pr_auc'] - 0.3)*100:.1f}% vs baseline"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="🎯 ROC-AUC Score",
            value=f"{model_info['roc_auc']:.4f}",
            delta="Excellent" if model_info['roc_auc'] > 0.9 else "Good"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="⚙️ Decision Threshold",
            value=f"{model_info['threshold']:.4f}",
            delta="Optimized"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        if summary:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric(
                label="🚨 Files Scanned",
                value=f"{summary['total_files']:,}",
                delta=f"{summary['risky_files']} high risk"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric(
                label="📊 Balanced Accuracy",
                value=f"{model_info['balanced_accuracy']:.4f}",
                delta="Stable"
            )
            st.markdown('</div>', unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'prediction_engine' not in st.session_state:
        try:
            st.session_state.prediction_engine = PredictionEngine()
        except Exception as e:
            st.error(f"Failed to initialize prediction engine: {str(e)}")
            st.stop()
    
    if 'results' not in st.session_state:
        st.session_state.results = []
    
    if 'current_mode' not in st.session_state:
        st.session_state.current_mode = "single"

def main():
    initialize_session_state()
    
    # Futuristic Header with Animation
    st.markdown('<h1 class="main-header">🛡️ CloudGuard AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">🚀 Advanced Infrastructure Risk Scanner - Powered by Next-Gen Machine Learning</p>', unsafe_allow_html=True)
    
    # Status Banner
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <span style="background: linear-gradient(45deg, #00d4ff, #0099cc); padding: 0.5rem 2rem; border-radius: 25px; color: white; font-weight: 600; font-size: 0.9rem; letter-spacing: 1px;">
            🔥 ENTERPRISE SECURITY SCANNER ACTIVE
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Advanced Sidebar with Real-time Monitoring
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; margin-bottom: 2rem; background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 153, 204, 0.1)); border-radius: 15px; border: 1px solid rgba(0, 212, 255, 0.2);">
            <h2 style="color: #00d4ff; margin: 0; font-size: 1.4rem;">�️ Mission Control</h2>
            <p style="color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 0.9rem;">Advanced Security Operations</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Real-time System Status
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(46, 213, 115, 0.1), rgba(34, 197, 94, 0.1)); padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border: 1px solid rgba(46, 213, 115, 0.2);">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="color: #2ed573; font-weight: 600;">• System Status</span>
                <span style="color: #2ed573; font-size: 0.8rem;">OPERATIONAL</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mode selection with enhanced styling
        st.markdown('<h3 style="color: #e2e8f0; margin-bottom: 1rem;">🎯 Scan Configuration</h3>', unsafe_allow_html=True)
        mode = st.radio(
            "Select Analysis Mode:",
            ["📄 Single File Analysis", "📦 Batch Processing"],
            key="scan_mode",
            help="Choose between individual file analysis or bulk processing"
        )
        st.session_state.current_mode = "single" if "Single" in mode else "batch"
        
        st.markdown('<hr style="border-color: rgba(148, 163, 184, 0.2); margin: 2rem 0;">', unsafe_allow_html=True)
        
        # Enhanced Model Information Dashboard
        st.markdown('<h3 style="color: #e2e8f0; margin-bottom: 1rem;">🧠 AI Model Intelligence</h3>', unsafe_allow_html=True)
        model_info = st.session_state.prediction_engine.model_loader.get_model_info()
        
        # Model Performance Metrics with Progress Bars
        st.markdown('<div style="margin-bottom: 1rem;">', unsafe_allow_html=True)
        
        # PR-AUC with visual indicator
        pr_auc_percent = model_info['pr_auc'] * 100
        st.markdown(f'<p style="color: #e2e8f0; margin-bottom: 0.2rem; font-size: 0.9rem;">🎯 Precision-Recall AUC: <span style="color: #00d4ff; font-weight: 600;">{model_info["pr_auc"]:.4f}</span></p>', unsafe_allow_html=True)
        st.progress(pr_auc_percent / 100)
        
        # ROC-AUC with visual indicator
        roc_auc_percent = model_info['roc_auc'] * 100
        st.markdown(f'<p style="color: #e2e8f0; margin-bottom: 0.2rem; font-size: 0.9rem;">🎯 ROC AUC: <span style="color: #2ed573; font-weight: 600;">{model_info["roc_auc"]:.4f}</span></p>', unsafe_allow_html=True)
        st.progress(roc_auc_percent / 100)
        
        # Balanced Accuracy
        bal_acc_percent = model_info['balanced_accuracy'] * 100
        st.markdown(f'<p style="color: #e2e8f0; margin-bottom: 0.2rem; font-size: 0.9rem;">⚖️ Balanced Accuracy: <span style="color: #ff9f43; font-weight: 600;">{model_info["balanced_accuracy"]:.4f}</span></p>', unsafe_allow_html=True)
        st.progress(bal_acc_percent / 100)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Model Technical Details
        with st.expander("🔧 Technical Specifications"):
            st.markdown(f"""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #94a3b8;">
            <strong>Algorithm:</strong> {model_info['model_type']}<br>
            <strong>Training Features:</strong> 32,768 sparse + 8 dense<br>
            <strong>Decision Threshold:</strong> {model_info['threshold']:.6f}<br>
            <strong>Calibration:</strong> 5-fold Sigmoid<br>
            <strong>Training Dataset:</strong> 21,107 files<br>
            <strong>Positive Rate:</strong> 2.32%
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<hr style="border-color: rgba(148, 163, 184, 0.2); margin: 2rem 0;">', unsafe_allow_html=True)
        
        # Advanced Threshold Control
        st.markdown('<h3 style="color: #e2e8f0; margin-bottom: 1rem;">⚙️ Advanced Controls</h3>', unsafe_allow_html=True)
        
        custom_threshold = st.slider(
            "🎯 Risk Sensitivity Threshold",
            min_value=0.001,
            max_value=0.999,
            value=float(model_info['threshold']),
            step=0.001,
            format="%.3f",
            help="Lower values = more sensitive detection (more files flagged as risky)"
        )
        
        use_custom_threshold = st.checkbox("🔧 Enable Custom Threshold", value=False)
        threshold_to_use = custom_threshold if use_custom_threshold else None
        
        # Threshold Impact Indicator
        if use_custom_threshold:
            if custom_threshold < model_info['threshold']:
                st.info("🔺 Higher sensitivity: More files will be flagged as risky")
            elif custom_threshold > model_info['threshold']:
                st.warning("🔻 Lower sensitivity: Fewer files will be flagged as risky")
            else:
                st.success("✅ Using optimized threshold")
    
    # Main content area
    if st.session_state.current_mode == "single":
        handle_single_file_mode(threshold_to_use)
    else:
        handle_batch_mode(threshold_to_use)

def handle_single_file_mode(threshold):
    """Handle single file upload and processing."""
    st.header("📄 Single File Analysis")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload an Infrastructure as Code file",
        type=['tf', 'yaml', 'yml', 'json', 'bicep'],
        help="Supported formats: Terraform (.tf), YAML (.yaml, .yml), JSON (.json), Bicep (.bicep)"
    )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size:,} bytes")
        with col3:
            st.metric("File Type", uploaded_file.type or "Unknown")
        
        # Process file
        try:
            # Read file content
            content = uploaded_file.read().decode('utf-8')
            
            # Show file preview
            with st.expander("📖 File Preview"):
                st.code(content[:1000] + "..." if len(content) > 1000 else content, language='text')
            
            # Predict
            with st.spinner("Analyzing file for security risks..."):
                result = st.session_state.prediction_engine.predict_single_file(
                    uploaded_file.name, content, threshold
                )
            
            # Advanced results display
            display_advanced_single_file_results(result)
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

def handle_batch_mode(threshold):
    """Handle batch file upload and processing."""
    st.header("📦 Batch Analysis")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a ZIP file containing IaC files",
        type=['zip'],
        help="Upload a ZIP archive containing your Infrastructure as Code files"
    )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Archive Name", uploaded_file.name)
        with col2:
            st.metric("Archive Size", f"{uploaded_file.size:,} bytes")
        
        # Process button
        if st.button("🔍 Analyze ZIP Archive", type="primary"):
            try:
                # Save uploaded file temporarily
                with st.spinner("Extracting and analyzing files..."):
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # Process ZIP file
                        results = st.session_state.prediction_engine.process_zip_file(
                            tmp_file_path, threshold
                        )
                        st.session_state.results = results
                        
                        # Display results
                        if results:
                            display_advanced_batch_results(results)
                        else:
                            st.warning("No supported IaC files found in the archive.")
                            
                    finally:
                        # Clean up temp file
                        os.unlink(tmp_file_path)
                        
            except Exception as e:
                st.error(f"Error processing ZIP file: {str(e)}")

def display_advanced_single_file_results(result):
    """Display advanced results for single file analysis with visualizations."""
    st.markdown('<h3 style="color: #e2e8f0; margin: 2rem 0 1rem 0;">🎯 Security Assessment Results</h3>', unsafe_allow_html=True)
    
    # Main risk assessment dashboard
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Risk gauge visualization
        risk_gauge = create_risk_gauge(result['risk_percentage'], "Security Risk Level")
        st.plotly_chart(risk_gauge, use_container_width=True)
    
    with col2:
        # Risk summary cards
        col2_1, col2_2 = st.columns(2)
        
        with col2_1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            risk_class = "risk-high" if result['is_risky'] else "risk-safe"
            st.markdown(f"""
            <h4 style="color: #e2e8f0; margin-bottom: 1rem;">Risk Classification</h4>
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">{result['decision_label'].split()[0]}</div>
                <div class="{risk_class}" style="font-size: 1.5rem; font-weight: 700;">
                    {result['decision_label'].split()[1] if len(result['decision_label'].split()) > 1 else ''}
                    {' Risk' if result['is_risky'] else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2_2:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            confidence_level = (
                "Very High" if result['risk_probability'] > 0.8 else
                "High" if result['risk_probability'] > 0.6 else
                "Medium" if result['risk_probability'] > 0.4 else
                "Low"
            )
            
            confidence_color = (
                "#ff4757" if confidence_level == "Very High" else
                "#ff9f43" if confidence_level == "High" else
                "#ffa502" if confidence_level == "Medium" else
                "#2ed573"
            )
            
            st.markdown(f"""
            <h4 style="color: #e2e8f0; margin-bottom: 1rem;">Confidence Analysis</h4>
            <div style="text-align: center;">
                <div style="font-size: 2.5rem; color: {confidence_color}; margin-bottom: 0.5rem;">
                    {result['risk_percentage']:.1f}%
                </div>
                <div style="color: {confidence_color}; font-weight: 600;">
                    {confidence_level} Confidence
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Detailed explanation section
    st.markdown('<h4 style="color: #e2e8f0; margin: 2rem 0 1rem 0;">📝 Security Analysis Report</h4>', unsafe_allow_html=True)
    
    explanation_style = "background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 153, 204, 0.1)); padding: 1.5rem; border-radius: 15px; border: 1px solid rgba(0, 212, 255, 0.2);"
    if result['is_risky']:
        explanation_style = "background: linear-gradient(135deg, rgba(255, 71, 87, 0.1), rgba(255, 107, 107, 0.1)); padding: 1.5rem; border-radius: 15px; border: 1px solid rgba(255, 71, 87, 0.2);"
    
    st.markdown(f"""
    <div style="{explanation_style}">
        <h5 style="color: #e2e8f0; margin-bottom: 1rem;">🔍 Analysis Summary</h5>
        <p style="color: #e2e8f0; font-size: 1.1rem; line-height: 1.6;">{result['explanation']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Advanced feature analysis
    with st.expander("� Advanced Feature Analysis", expanded=False):
        feature_info = result.get('feature_info', {})
        
        tab1, tab2, tab3 = st.tabs(["🗺️ Path Analysis", "🔧 Resource Tokens", "📊 Structural Features"])
        
        with tab1:
            st.markdown('<h5 style="color: #e2e8f0;">Path-based Security Indicators</h5>', unsafe_allow_html=True)
            path_tokens = feature_info.get('path_tokens', [])
            if path_tokens:
                for i, token in enumerate(path_tokens[:8]):
                    risk_indicator = "🔴" if any(risk_word in token.lower() for risk_word in ['admin', 'secret', 'private', 'key']) else "🟠"
                    st.markdown(f"&nbsp;&nbsp;{risk_indicator} `{token}`")
            else:
                st.info("No significant path tokens detected")
        
        with tab2:
            st.markdown('<h5 style="color: #e2e8f0;">Resource & Configuration Patterns</h5>', unsafe_allow_html=True)
            resource_tokens = feature_info.get('resource_tokens', [])
            if resource_tokens:
                for i, token in enumerate(resource_tokens[:8]):
                    risk_indicator = "🔴" if any(risk_word in token.lower() for risk_word in ['aws_s3', 'iam', 'admin', 'root']) else "🟢"
                    st.markdown(f"&nbsp;&nbsp;{risk_indicator} `{token}`")
            else:
                st.info("No resource-specific tokens detected")
        
        with tab3:
            st.markdown('<h5 style="color: #e2e8f0;">File Structure & Metadata</h5>', unsafe_allow_html=True)
            dense_features = feature_info.get('dense_features', {})
            if dense_features:
                # Create a visualization of dense features
                feature_df = pd.DataFrame([
                    {'Feature': k.replace('_', ' ').title(), 'Value': f"{v:.4f}" if isinstance(v, float) else str(v)}
                    for k, v in dense_features.items()
                ])
                st.dataframe(feature_df, use_container_width=True, hide_index=True)
            else:
                st.info("No structural features available")
    
    # Action recommendations
    st.markdown('<h4 style="color: #e2e8f0; margin: 2rem 0 1rem 0;">💡 Recommended Actions</h4>', unsafe_allow_html=True)
    
    if result['is_risky']:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(255, 71, 87, 0.1), rgba(255, 107, 107, 0.1)); padding: 1.5rem; border-radius: 15px; border: 1px solid rgba(255, 71, 87, 0.2);">
            <h5 style="color: #ff4757; margin-bottom: 1rem;">⚠️ High Risk Detected - Immediate Actions Required</h5>
            <ul style="color: #e2e8f0; line-height: 1.8;">
                <li>🔍 Review file for sensitive configurations</li>
                <li>🔒 Audit access permissions and security groups</li>
                <li>📋 Consider security best practices compliance</li>
                <li>📝 Document and track this finding</li>
            </ul>
        </div>
        """)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(46, 213, 115, 0.1), rgba(34, 197, 94, 0.1)); padding: 1.5rem; border-radius: 15px; border: 1px solid rgba(46, 213, 115, 0.2);">
            <h5 style="color: #2ed573; margin-bottom: 1rem;">✅ Low Risk Assessment - Monitoring Recommendations</h5>
            <ul style="color: #e2e8f0; line-height: 1.8;">
                <li>📋 Continue regular security reviews</li>
                <li>🔄 Monitor for configuration changes</li>
                <li>📈 Include in periodic compliance audits</li>
                <li>✅ File appears to follow security best practices</li>
            </ul>
        </div>
        """)

def display_advanced_batch_results(results):
    """Display advanced results for batch analysis with comprehensive visualizations."""
    if not results:
        st.warning("⚠️ No valid results to display")
        return
    
    st.markdown('<h3 style="color: #e2e8f0; margin: 2rem 0 1rem 0;">📊 Batch Analysis Intelligence Dashboard</h3>', unsafe_allow_html=True)
    
    # Calculate summary statistics
    total_files = len(results)
    risky_files = sum(1 for r in results if r['is_risky'])
    safe_files = total_files - risky_files
    avg_risk_score = sum(r['risk_percentage'] for r in results) / total_files
    
    # Executive summary dashboard
    st.markdown('<h4 style="color: #e2e8f0; margin: 1.5rem 0 1rem 0;">📊 Executive Summary</h4>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("📁 Total Files", total_files)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("🔴 High Risk", risky_files, delta=f"{(risky_files/total_files)*100:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("🟢 Low Risk", safe_files, delta=f"{(safe_files/total_files)*100:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("🎯 Avg Risk Score", f"{avg_risk_score:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Advanced visualizations dashboard
    st.markdown('<h4 style="color: #e2e8f0; margin: 2rem 0 1rem 0;">📈 Security Analytics Dashboard</h4>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔴 Risk Analysis", "🗺️ Distribution", "📄 File Details"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Risk distribution chart
            risk_dist_fig = create_risk_distribution_chart(results)
            st.plotly_chart(risk_dist_fig, use_container_width=True)
        
        with col2:
            # Top risks chart
            top_risks_fig = create_top_risks_chart(results)
            st.plotly_chart(top_risks_fig, use_container_width=True)
    
    with tab2:
        # Risk heatmap and detailed analysis
        if risky_files > 0:
            st.markdown('<h5 style="color: #ff4757; margin-bottom: 1rem;">⚠️ Critical Security Findings</h5>', unsafe_allow_html=True)
            
            # High-risk files table
            high_risk_data = []
            for result in results:
                if result['is_risky']:
                    high_risk_data.append({
                        'File Name': result['filename'],
                        'Risk Score': f"{result['risk_percentage']:.1f}%",
                        'Classification': result['decision_label'],
                        'Priority': 'Critical' if result['risk_percentage'] > 80 else 'High',
                        'Confidence': f"{result['risk_probability']:.3f}"
                    })
            
            if high_risk_data:
                df_risks = pd.DataFrame(high_risk_data)
                st.dataframe(
                    df_risks,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Risk Score": st.column_config.ProgressColumn(
                            "Risk Score",
                            help="Risk percentage",
                            min_value=0,
                            max_value=100,
                        ),
                    }
                )
        else:
            st.success("✅ No high-risk files detected in this batch!")
    
    with tab3:
        # Risk score distribution visualization
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Risk score histogram
            risk_scores = [r['risk_percentage'] for r in results]
            fig_hist = px.histogram(
                x=risk_scores,
                nbins=20,
                title="Risk Score Distribution",
                labels={'x': 'Risk Score (%)', 'y': 'Number of Files'},
                color_discrete_sequence=['#00d4ff']
            )
            fig_hist.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#e2e8f0',
                title_font_color='#e2e8f0'
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Risk categories breakdown
            categories = {
                'Critical (>80%)': sum(1 for r in results if r['risk_percentage'] > 80),
                'High (60-80%)': sum(1 for r in results if 60 < r['risk_percentage'] <= 80),
                'Medium (40-60%)': sum(1 for r in results if 40 < r['risk_percentage'] <= 60),
                'Low (<40%)': sum(1 for r in results if r['risk_percentage'] <= 40)
            }
            
            st.markdown('<h6 style="color: #e2e8f0;">Risk Categories</h6>', unsafe_allow_html=True)
            for category, count in categories.items():
                if count > 0:
                    percentage = (count / total_files) * 100
                    st.metric(category, count, delta=f"{percentage:.1f}%")
    
    with tab4:
        # Detailed file-by-file results
        st.markdown('<h5 style="color: #e2e8f0; margin-bottom: 1rem;">📄 Detailed File Analysis</h5>', unsafe_allow_html=True)
        
        # Search and filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 Search files", placeholder="Enter filename or pattern")
        with col2:
            risk_filter = st.selectbox("📊 Filter by risk", ['All', 'High Risk Only', 'Low Risk Only'])
        
        # Filter results
        filtered_results = results
        if search_term:
            filtered_results = [r for r in filtered_results if search_term.lower() in r['filename'].lower()]
        
        if risk_filter == 'High Risk Only':
            filtered_results = [r for r in filtered_results if r['is_risky']]
        elif risk_filter == 'Low Risk Only':
            filtered_results = [r for r in filtered_results if not r['is_risky']]
        
        # Display filtered results
        for i, result in enumerate(filtered_results):
            with st.expander(f"{'🔴' if result['is_risky'] else '🟢'} {result['filename']} - {result['risk_percentage']:.1f}% Risk"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Risk Assessment:** {result['decision_label']}")
                    st.markdown(f"**Explanation:** {result['explanation']}")
                    
                    if 'file_path' in result:
                        st.markdown(f"**File Path:** `{result['file_path']}`")
                
                with col2:
                    # Mini risk gauge
                    mini_gauge = create_risk_gauge(result['risk_percentage'], f"Risk Level", height=200)
                    st.plotly_chart(mini_gauge, use_container_width=True)
    
    # Export options
    st.markdown('<h4 style="color: #e2e8f0; margin: 2rem 0 1rem 0;">📤 Export & Reporting</h4>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export Summary Report", use_container_width=True):
            # Create summary report
            report_data = {
                'Analysis Date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'Total Files Analyzed': total_files,
                'High Risk Files': risky_files,
                'Low Risk Files': safe_files,
                'Average Risk Score': f"{avg_risk_score:.2f}%",
                'Risk Distribution': {
                    'Critical (>80%)': sum(1 for r in results if r['risk_percentage'] > 80),
                    'High (60-80%)': sum(1 for r in results if 60 < r['risk_percentage'] <= 80),
                    'Medium (40-60%)': sum(1 for r in results if 40 < r['risk_percentage'] <= 60),
                    'Low (<40%)': sum(1 for r in results if r['risk_percentage'] <= 40)
                }
            }
            
            st.json(report_data)
    
    with col2:
        if st.button("📋 Export Detailed CSV", use_container_width=True):
            # Create detailed CSV
            csv_data = []
            for result in results:
                csv_data.append({
                    'filename': result['filename'],
                    'risk_percentage': result['risk_percentage'],
                    'is_risky': result['is_risky'],
                    'decision_label': result['decision_label'],
                    'risk_probability': result['risk_probability'],
                    'explanation': result['explanation']
                })
            
            df_export = pd.DataFrame(csv_data)
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"batch_analysis_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name="cloudguard_analysis_results.csv",
            mime="text/csv"
        )
    
    with col2:
        # Prepare JSON data
        json_data = json.dumps(results, indent=2)
        st.download_button(
            label="📥 Download as JSON",
            data=json_data,
            file_name="cloudguard_analysis_results.json",
            mime="application/json"
        )

if __name__ == "__main__":
    # Run the hi-tech CloudGuard AI interface
    main()