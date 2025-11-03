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
    
    /* Global Dark Theme with Better Readability */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        font-family: 'Inter', sans-serif;
        font-size: 20px !important;
        zoom: 1.15;
    }
    
    /* Enable smooth scrolling */
    html, body, .stApp {
        overflow-y: auto !important;
        height: auto !important;
        scroll-behavior: smooth;
    }
    
    /* Increase base font sizes for better readability */
    .stMarkdown, .stText, p, div, span, label {
        font-size: 1.3rem !important;
        line-height: 1.8 !important;
    }
    
    /* Better readable labels and metrics */
    .stMetric label {
        font-size: 1.4rem !important;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        font-size: 3rem !important;
    }
    
    /* Radio buttons and checkboxes - larger text */
    .stRadio label, .stCheckbox label {
        font-size: 1.3rem !important;
    }
    
    /* File uploader text */
    .stFileUploader label {
        font-size: 1.3rem !important;
    }
    
    /* Expander headers */
    .streamlit-expanderHeader {
        font-size: 1.3rem !important;
    }
    
    /* Animated Header with Glow Effect - Much Larger */
    .main-header {
        font-size: 5.5rem !important;
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
        font-size: 2rem !important;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
        letter-spacing: 0.5px;
    }
    
    /* Headers inside content - Much larger */
    h1, h2, h3, h4, h5, h6 {
        font-size: 1.8em !important;
    }
    
    /* Sidebar text - Much Larger */
    .css-1d391kg .stMarkdown {
        font-size: 1.2rem !important;
    }
    
    /* Futuristic Metric Cards - Larger padding and text */
    .metric-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        font-size: 1.1rem;
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
    
    /* Button Enhancements - Much Larger and more readable */
    .stButton > button {
        background: linear-gradient(45deg, #00d4ff, #0099cc);
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        padding: 1.4rem 3.5rem !important;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
        font-size: 1.3rem !important;
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
    
    /* Text Colors - Much Larger and more readable */
    .stMarkdown, .stText {
        color: #e2e8f0;
        font-size: 1.2rem !important;
    }
    
    /* Sidebar text - Much Larger */
    .css-1d391kg .stMarkdown {
        font-size: 1.1rem !important;
    }
    
    /* Headers inside content */
    h1, h2, h3, h4, h5, h6 {
        font-size: 1.5em !important;
    }
    
    /* Metric Widgets - Much Larger */
    .metric-container {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 204, 0.1) 100%);
        border-radius: 15px;
        padding: 2.5rem !important;
        font-size: 1.2rem !important;
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
    
    /* Tooltip Styles */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: rgba(15, 23, 42, 0.95);
        color: #e2e8f0;
        text-align: center;
        border-radius: 6px;
        padding: 0.5rem;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.85rem;
        border: 1px solid rgba(0, 212, 255, 0.3);
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Fade-in animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Shimmer effect for loading */
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    .shimmer {
        background: linear-gradient(90deg, rgba(30, 41, 59, 0.5) 25%, rgba(0, 212, 255, 0.3) 50%, rgba(30, 41, 59, 0.5) 75%);
        background-size: 1000px 100%;
        animation: shimmer 2s infinite;
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
            colorbar=dict(
                title=dict(text="Risk %", font={'color': '#e2e8f0'}),
                tickfont={'color': '#e2e8f0'}
            )
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
    
    # New: History tracking
    if 'scan_history' not in st.session_state:
        st.session_state.scan_history = []
    
    if 'notification' not in st.session_state:
        st.session_state.notification = None
    
    if 'total_scans' not in st.session_state:
        st.session_state.total_scans = 0

@st.cache_resource
def load_prediction_engine():
    """Cached prediction engine loader for performance."""
    return PredictionEngine()

def show_notification(message, type="info"):
    """Display a toast-style notification."""
    icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
    colors = {
        "success": "#2ed573",
        "error": "#ff4757", 
        "warning": "#ffa502",
        "info": "#00d4ff"
    }
    
    st.markdown(f"""
    <div style="
        position: fixed; 
        top: 80px; 
        right: 20px; 
        background: rgba(15, 23, 42, 0.95); 
        backdrop-filter: blur(20px);
        border-left: 4px solid {colors.get(type, '#00d4ff')};
        border-radius: 8px;
        padding: 1rem 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
        color: #e2e8f0;
        min-width: 300px;
    ">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.5rem;">{icons.get(type, 'ℹ️')}</span>
            <div>
                <div style="font-weight: 600; color: {colors.get(type, '#00d4ff')}; margin-bottom: 0.25rem;">
                    {type.upper()}
                </div>
                <div style="font-size: 0.9rem;">
                    {message}
                </div>
            </div>
        </div>
    </div>
    <style>
        @keyframes slideIn {{
            from {{ transform: translateX(400px); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
    </style>
    """, unsafe_allow_html=True)

def add_to_history(scan_type, file_name, risk_score, is_risky, file_count=1):
    """Add a scan to history."""
    st.session_state.scan_history.insert(0, {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'scan_type': scan_type,
        'file_name': file_name,
        'risk_score': risk_score,
        'is_risky': is_risky,
        'file_count': file_count
    })
    # Keep only last 20 scans
    st.session_state.scan_history = st.session_state.scan_history[:20]
    st.session_state.total_scans += 1

def main():
    initialize_session_state()
    
    # Futuristic Header with Animation
    st.markdown('<h1 class="main-header">🛡️ CloudGuard AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">🚀 Advanced Infrastructure Risk Scanner - Powered by Next-Gen Machine Learning</p>', unsafe_allow_html=True)
    
    # Status Banner with Stats
    total_scans = st.session_state.total_scans
    history_count = len(st.session_state.scan_history)
    
    st.markdown(f"""
    <div style="text-align: center; margin: 2rem 0;">
        <span style="background: linear-gradient(45deg, #00d4ff, #0099cc); padding: 0.5rem 2rem; border-radius: 25px; color: white; font-weight: 600; font-size: 0.9rem; letter-spacing: 1px;">
            🔥 ENTERPRISE SECURITY SCANNER ACTIVE
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick stats dashboard (if there's history)
    if total_scans > 0:
        st.markdown('<div style="margin: 1.5rem 0;">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        recent_risky = sum(1 for s in st.session_state.scan_history if s['is_risky'])
        recent_safe = history_count - recent_risky
        avg_recent_risk = sum(s['risk_score'] for s in st.session_state.scan_history) / history_count if history_count > 0 else 0
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 153, 204, 0.1)); 
                        padding: 1rem; border-radius: 10px; text-align: center; border: 1px solid rgba(0, 212, 255, 0.2);">
                <div style="font-size: 1.8rem; font-weight: 700; color: #00d4ff;">{total_scans}</div>
                <div style="color: #94a3b8; font-size: 0.85rem;">Total Scans</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(255, 71, 87, 0.1), rgba(255, 107, 107, 0.1)); 
                        padding: 1rem; border-radius: 10px; text-align: center; border: 1px solid rgba(255, 71, 87, 0.2);">
                <div style="font-size: 1.8rem; font-weight: 700; color: #ff4757;">{recent_risky}</div>
                <div style="color: #94a3b8; font-size: 0.85rem;">High Risk Files</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(46, 213, 115, 0.1), rgba(34, 197, 94, 0.1)); 
                        padding: 1rem; border-radius: 10px; text-align: center; border: 1px solid rgba(46, 213, 115, 0.2);">
                <div style="font-size: 1.8rem; font-weight: 700; color: #2ed573;">{recent_safe}</div>
                <div style="color: #94a3b8; font-size: 0.85rem;">Low Risk Files</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(255, 159, 67, 0.1), rgba(255, 165, 2, 0.1)); 
                        padding: 1rem; border-radius: 10px; text-align: center; border: 1px solid rgba(255, 159, 67, 0.2);">
                <div style="font-size: 1.8rem; font-weight: 700; color: #ffa502;">{avg_recent_risk:.1f}%</div>
                <div style="color: #94a3b8; font-size: 0.85rem;">Avg Risk Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
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
        
        # Recent Scans History
        if st.session_state.scan_history:
            st.markdown('<h3 style="color: #e2e8f0; margin-bottom: 1rem;">📜 Recent Scans</h3>', unsafe_allow_html=True)
            
            # Show total scans badge
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 153, 204, 0.1)); 
                        padding: 0.5rem 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;">
                <span style="color: #00d4ff; font-weight: 600;">Total Scans: {st.session_state.total_scans}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Display recent scans
            for i, scan in enumerate(st.session_state.scan_history[:5]):
                risk_color = "#ff4757" if scan['is_risky'] else "#2ed573"
                risk_icon = "🔴" if scan['is_risky'] else "🟢"
                
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.5); padding: 0.75rem; border-radius: 8px; 
                            margin-bottom: 0.5rem; border-left: 3px solid {risk_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #e2e8f0; font-size: 0.85rem; font-weight: 600;">
                                {risk_icon} {scan['file_name'][:30]}{'...' if len(scan['file_name']) > 30 else ''}
                            </div>
                            <div style="color: #94a3b8; font-size: 0.75rem;">
                                {scan['timestamp']} • {scan['scan_type']}
                            </div>
                        </div>
                        <div style="color: {risk_color}; font-weight: 700; font-size: 0.9rem;">
                            {scan['risk_score']:.1f}%
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(st.session_state.scan_history) > 5:
                with st.expander(f"📋 Show all {len(st.session_state.scan_history)} scans"):
                    for scan in st.session_state.scan_history[5:]:
                        risk_color = "#ff4757" if scan['is_risky'] else "#2ed573"
                        risk_icon = "🔴" if scan['is_risky'] else "🟢"
                        st.markdown(f"""
                        <div style="font-size: 0.8rem; padding: 0.5rem; margin-bottom: 0.25rem;">
                            {risk_icon} {scan['file_name']} - <span style="color: {risk_color};">{scan['risk_score']:.1f}%</span>
                            <br><span style="color: #94a3b8; font-size: 0.7rem;">{scan['timestamp']}</span>
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
        
        st.markdown('<hr style="border-color: rgba(148, 163, 184, 0.2); margin: 2rem 0;">', unsafe_allow_html=True)
        
        # Quick Help Section
        with st.expander("💡 Quick Tips & Shortcuts"):
            st.markdown("""
            <div style="color: #e2e8f0; font-size: 0.85rem; line-height: 1.8;">
                <strong style="color: #00d4ff;">📌 Quick Actions:</strong><br>
                • Press <kbd>Ctrl+R</kbd> to refresh<br>
                • Use threshold slider for sensitivity<br>
                • Check history for past scans<br><br>
                
                <strong style="color: #00d4ff;">🎯 Best Practices:</strong><br>
                • Upload clean, well-formatted IaC files<br>
                • Review high-risk findings carefully<br>
                • Use batch mode for multiple files<br>
                • Export results for documentation<br><br>
                
                <strong style="color: #00d4ff;">🔍 Risk Levels:</strong><br>
                • <span style="color: #ff4757;">🔴 High (>60%):</span> Immediate review needed<br>
                • <span style="color: #ffa502;">🟠 Medium (40-60%):</span> Review recommended<br>
                • <span style="color: #2ed573;">🟢 Low (<40%):</span> Minimal concern<br>
            </div>
            """, unsafe_allow_html=True)
    
    # Main content area
    if st.session_state.current_mode == "single":
        handle_single_file_mode(threshold_to_use)
    else:
        handle_batch_mode(threshold_to_use)

def handle_single_file_mode(threshold):
    """Handle single file upload and processing."""
    st.header("📄 Single File Analysis")
    
    # Enhanced drag & drop zone
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.05), rgba(0, 153, 204, 0.05));
        border: 2px dashed rgba(0, 212, 255, 0.3);
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 1.5rem 0;
        transition: all 0.3s ease;
    " onmouseover="this.style.borderColor='rgba(0, 212, 255, 0.6)'; this.style.background='linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 153, 204, 0.1)';" 
       onmouseout="this.style.borderColor='rgba(0, 212, 255, 0.3)'; this.style.background='linear-gradient(135deg, rgba(0, 212, 255, 0.05), rgba(0, 153, 204, 0.05)';">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">📁</div>
        <div style="color: #e2e8f0; font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">
            Drag & Drop Your IaC File Here
        </div>
        <div style="color: #94a3b8; font-size: 0.9rem;">
            or click below to browse
        </div>
        <div style="color: #00d4ff; font-size: 0.85rem; margin-top: 0.5rem;">
            Supported: Terraform (.tf), YAML (.yaml, .yml), JSON (.json), Bicep (.bicep)
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload an Infrastructure as Code file",
        type=['tf', 'yaml', 'yml', 'json', 'bicep'],
        help="Supported formats: Terraform (.tf), YAML (.yaml, .yml), JSON (.json), Bicep (.bicep)",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # Display file info with enhanced styling
        st.markdown('<div style="margin: 2rem 0;">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="metric-container" style="text-align: center;">
                <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.5rem;">📄 FILE NAME</div>
                <div style="color: #00d4ff; font-weight: 600; word-break: break-all;">{}</div>
            </div>
            """.format(uploaded_file.name), unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="metric-container" style="text-align: center;">
                <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.5rem;">📦 FILE SIZE</div>
                <div style="color: #2ed573; font-weight: 600;">{:,} bytes</div>
            </div>
            """.format(uploaded_file.size), unsafe_allow_html=True)
        with col3:
            file_type_display = uploaded_file.type or "application/octet-stream"
            st.markdown("""
            <div class="metric-container" style="text-align: center;">
                <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.5rem;">🏷️ FILE TYPE</div>
                <div style="color: #ffa502; font-weight: 600;">{}</div>
            </div>
            """.format(file_type_display), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Process file
        try:
            # Read file content
            content = uploaded_file.read().decode('utf-8')
            
            # Show file preview with better styling
            with st.expander("📖 File Preview (First 1000 characters)", expanded=False):
                st.code(content[:1000] + ("..." if len(content) > 1000 else ""), language='text')
            
            # Analyze button with loading state
            if st.button("🔍 Analyze File Security", type="primary", use_container_width=True):
                # Loading animation
                with st.spinner(""):
                    st.markdown("""
                    <div style="text-align: center; padding: 2rem;">
                        <div class="loading-spinner" style="margin: 0 auto 1rem auto;"></div>
                        <div style="color: #00d4ff; font-weight: 600; animation: pulse 1.5s infinite;">
                            🔍 Analyzing security patterns...
                        </div>
                        <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">
                            Extracting features • Running ML model • Generating insights
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Predict
                    result = st.session_state.prediction_engine.predict_single_file(
                        uploaded_file.name, content, threshold
                    )
                    
                    # Add to history
                    add_to_history(
                        scan_type="Single File",
                        file_name=uploaded_file.name,
                        risk_score=result['risk_percentage'],
                        is_risky=result['is_risky']
                    )
                
                # Show success notification
                show_notification(
                    f"Analysis complete! Risk score: {result['risk_percentage']:.1f}%",
                    "success" if not result['is_risky'] else "warning"
                )
                
                # Display results
                display_advanced_single_file_results(result)
            
        except Exception as e:
            show_notification(f"Error processing file: {str(e)}", "error")
            st.error(f"❌ Error processing file: {str(e)}")

def handle_batch_mode(threshold):
    """Handle batch file upload and processing."""
    st.header("📦 Batch Analysis")
    
    # Enhanced drag & drop zone for ZIP
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(138, 43, 226, 0.05), rgba(75, 0, 130, 0.05));
        border: 2px dashed rgba(138, 43, 226, 0.3);
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 1.5rem 0;
        transition: all 0.3s ease;
    " onmouseover="this.style.borderColor='rgba(138, 43, 226, 0.6)'; this.style.background='linear-gradient(135deg, rgba(138, 43, 226, 0.1), rgba(75, 0, 130, 0.1)';" 
       onmouseout="this.style.borderColor='rgba(138, 43, 226, 0.3)'; this.style.background='linear-gradient(135deg, rgba(138, 43, 226, 0.05), rgba(75, 0, 130, 0.05)';">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">📦</div>
        <div style="color: #e2e8f0; font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">
            Drag & Drop Your ZIP Archive Here
        </div>
        <div style="color: #94a3b8; font-size: 0.9rem;">
            or click below to browse
        </div>
        <div style="color: #a855f7; font-size: 0.85rem; margin-top: 0.5rem;">
            Upload a ZIP containing multiple IaC files for bulk analysis
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a ZIP file containing IaC files",
        type=['zip'],
        help="Upload a ZIP archive containing your Infrastructure as Code files",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # Display file info with enhanced styling
        st.markdown('<div style="margin: 2rem 0;">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="metric-container" style="text-align: center;">
                <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.5rem;">📦 ARCHIVE NAME</div>
                <div style="color: #a855f7; font-weight: 600; word-break: break-all;">{}</div>
            </div>
            """.format(uploaded_file.name), unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="metric-container" style="text-align: center;">
                <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.5rem;">💾 ARCHIVE SIZE</div>
                <div style="color: #2ed573; font-weight: 600;">{:,} bytes</div>
            </div>
            """.format(uploaded_file.size), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Process button with enhanced styling
        if st.button("🔍 Analyze ZIP Archive", type="primary", use_container_width=True):
            try:
                # Enhanced loading state
                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                
                with st.spinner(""):
                    status_placeholder.markdown("""
                    <div style="text-align: center; padding: 2rem;">
                        <div class="loading-spinner" style="margin: 0 auto 1rem auto;"></div>
                        <div style="color: #a855f7; font-weight: 600; font-size: 1.2rem; margin-bottom: 0.5rem;">
                            🔍 Extracting and Analyzing Archive
                        </div>
                        <div style="color: #94a3b8; font-size: 0.9rem;">
                            This may take a moment...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Simulate progress
                    progress_bar = progress_placeholder.progress(0)
                    for i in range(0, 30, 10):
                        time.sleep(0.3)
                        progress_bar.progress(i)
                    
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        progress_bar.progress(40)
                        status_placeholder.markdown("""
                        <div style="text-align: center; color: #00d4ff;">
                            📂 Extracting files...
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Process ZIP file
                        results = st.session_state.prediction_engine.process_zip_file(
                            tmp_file_path, threshold
                        )
                        
                        progress_bar.progress(100)
                        st.session_state.results = results
                        
                        # Clear loading indicators
                        progress_placeholder.empty()
                        status_placeholder.empty()
                        
                        # Display results
                        if results:
                            # Add to history
                            avg_risk = sum(r['risk_percentage'] for r in results) / len(results)
                            risky_count = sum(1 for r in results if r['is_risky'])
                            
                            add_to_history(
                                scan_type="Batch",
                                file_name=f"{uploaded_file.name} ({len(results)} files)",
                                risk_score=avg_risk,
                                is_risky=(risky_count > 0),
                                file_count=len(results)
                            )
                            
                            # Show success notification
                            show_notification(
                                f"Batch analysis complete! Analyzed {len(results)} files. {risky_count} high-risk files detected.",
                                "success" if risky_count == 0 else "warning"
                            )
                            
                            display_advanced_batch_results(results)
                        else:
                            status_placeholder.warning("⚠️ No supported IaC files found in the archive.")
                            
                    finally:
                        # Clean up temp file
                        os.unlink(tmp_file_path)
                        
            except Exception as e:
                show_notification(f"Error processing ZIP file: {str(e)}", "error")
                st.error(f"❌ Error processing ZIP file: {str(e)}")

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
            final_label = result.get('final_label') or result.get('risk_band') or 'N/A'
            band = result.get('risk_band') or 'N/A'
            st.markdown(f"""
            <h4 style=\"color: #e2e8f0; margin-bottom: 1rem;\">Risk Classification</h4>
            <div style=\"text-align: center;\">
                <div style=\"font-size: 1.5rem; font-weight: 700;\">{final_label}</div>
                <div style=\"color:#94a3b8; font-size:0.85rem;\">Heuristic Band: {band}<br/>Model: {result['decision_label']} @ {result['risk_percentage']:.1f}% (thr {result.get('decision_threshold',0)*100:.1f}%)</div>
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

    # Heuristic signals
    h_reasons = result.get('heuristic_reasons') or []
    if h_reasons:
        st.caption("Heuristic signals: " + ", ".join(h_reasons))
    
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
    with st.expander("🧠 Advanced Feature Analysis", expanded=False):
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
                        'File Name': result.get('filename') or Path(result['file_path']).name,
                        'Risk Score': f"{result['risk_percentage']:.1f}%",
                        'Band': result.get('risk_band', ''),
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
            risk_filter = st.selectbox("📊 Filter by risk", ['All', 'High Risk Only', 'Medium Risk Only', 'Low Risk Only'])
        
        # Filter results
        filtered_results = results
        if search_term:
            filtered_results = [r for r in filtered_results if search_term.lower() in r['filename'].lower()]
        
        if risk_filter == 'High Risk Only':
            filtered_results = [r for r in filtered_results if (r.get('risk_band') == 'High Risk')]
        elif risk_filter == 'Medium Risk Only':
            filtered_results = [r for r in filtered_results if (r.get('risk_band') == 'Medium Risk')]
        elif risk_filter == 'Low Risk Only':
            filtered_results = [r for r in filtered_results if (r.get('risk_band') == 'Low Risk')]
        
        # Display filtered results
        for i, result in enumerate(filtered_results):
            icon = '🔴' if (result.get('risk_band') == 'High Risk' or result['is_risky']) else ('�' if result.get('risk_band') == 'Medium Risk' else '🟢')
            with st.expander(f"{icon} {result.get('filename') or Path(result['file_path']).name} - {result['risk_percentage']:.1f}% Risk | {result.get('risk_band','')} "):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Heuristic Band:** {result.get('risk_band','')}")
                    st.markdown(f"**Model Assessment:** {result['decision_label']} (thr {result.get('decision_threshold', 0)*100:.1f}%)")
                    st.markdown(f"**Explanation:** {result['explanation']}")
                    h_reasons = result.get('heuristic_reasons') or []
                    if h_reasons:
                        st.caption("Signals: " + ", ".join(h_reasons))
                    
                    if 'file_path' in result:
                        st.markdown(f"**File Path:** `{result['file_path']}`")
                
                with col2:
                    # Mini risk gauge
                    mini_gauge = create_risk_gauge(result['risk_percentage'], f"Risk Level")
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
                    'filename': result.get('filename') or Path(result['file_path']).name,
                    'risk_percentage': result['risk_percentage'],
                    'risk_band': result.get('risk_band',''),
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
        # Prepare CSV from all results
        csv_rows = []
        for r in results:
            csv_rows.append({
                'filename': r.get('filename') or Path(r['file_path']).name,
                'risk_percentage': r['risk_percentage'],
                'risk_band': r.get('risk_band',''),
                'is_risky': r['is_risky'],
                'decision_label': r['decision_label'],
                'risk_probability': r['risk_probability'],
                'explanation': r['explanation']
            })
        df_dl = pd.DataFrame(csv_rows)
        csv_str = df_dl.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_str,
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