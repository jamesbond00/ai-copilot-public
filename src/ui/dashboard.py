"""
Streamlit dashboard for AI Copilot.
"""

import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configure page
st.set_page_config(
    page_title="AI Copilot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")


def call_api(endpoint: str, params: dict = None) -> dict:
    """Make API call to the backend."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API call failed: {e}")
        return {}


def main():
    """Main dashboard function."""
    
    # Header
    st.title("🤖 AI Copilot Dashboard")
    st.markdown("Intelligent monitoring and logging analysis")
    
    # Sidebar
    st.sidebar.header("Configuration")
    
    # Time range selection
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 24 hours", "Last 7 days", "Last 30 days"],
        index=0
    )
    
    time_mapping = {
        "Last 24 hours": 24,
        "Last 7 days": 168,
        "Last 30 days": 720
    }
    hours_back = time_mapping[time_range]
    
    # Analysis type selection
    analysis_type = st.sidebar.selectbox(
        "Analysis Type",
        ["Daily Summary", "Error Analysis", "Performance Analysis"],
        index=0
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 Analysis Results")
        
        # Health check
        with st.expander("System Health", expanded=False):
            health = call_api("/health")
            if health:
                status = health.get("status", "unknown")
                color = "🟢" if status == "healthy" else "🟡" if status == "degraded" else "🔴"
                st.write(f"{color} Status: {status.title()}")
                st.write(f"Monitoring System Connected: {health.get('monitoring_system_connected', False)}")
                st.write(f"Last Check: {health.get('timestamp', 'Unknown')}")
        
        # Analysis results
        if st.button("🔄 Run Analysis", type="primary"):
            with st.spinner("Analyzing logs..."):
                if analysis_type == "Daily Summary":
                    result = call_api("/summary/daily", {"days_back": hours_back // 24})
                elif analysis_type == "Error Analysis":
                    result = call_api("/analysis/errors", {"hours_back": hours_back})
                elif analysis_type == "Performance Analysis":
                    result = call_api("/analysis/performance", {"hours_back": hours_back})
                
                if result:
                    display_analysis_results(result)
    
    with col2:
        st.header("⚡ Quick Actions")
        
        # Quick summary
        if st.button("📋 Daily Summary"):
            with st.spinner("Generating summary..."):
                result = call_api("/summary/daily")
                if result:
                    st.success("Summary generated!")
                    st.json(result)
        
        # Error analysis
        if st.button("🚨 Error Analysis"):
            with st.spinner("Analyzing errors..."):
                result = call_api("/analysis/errors")
                if result:
                    st.success("Error analysis complete!")
                    st.json(result)
        
        # Performance analysis
        if st.button("⚡ Performance Analysis"):
            with st.spinner("Analyzing performance..."):
                result = call_api("/analysis/performance")
                if result:
                    st.success("Performance analysis complete!")
                    st.json(result)


def display_analysis_results(result: dict):
    """Display analysis results in a formatted way."""
    
    # Summary
    st.subheader("📝 Summary")
    st.write(result.get("summary", "No summary available"))
    
    # Key insights
    st.subheader("🔍 Key Insights")
    insights = result.get("key_insights", [])
    if insights:
        for i, insight in enumerate(insights, 1):
            st.write(f"{i}. {insight}")
    else:
        st.write("No key insights available")
    
    # Recommendations
    st.subheader("💡 Recommendations")
    recommendations = result.get("recommendations", [])
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    else:
        st.write("No recommendations available")
    
    # Confidence score
    confidence = result.get("confidence_score", 0)
    st.subheader("🎯 Confidence Score")
    
    # Create confidence gauge
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = confidence * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Confidence (%)"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Metadata
    st.subheader("📊 Analysis Metadata")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Confidence", f"{confidence:.2f}")
    
    with col2:
        log_count = result.get("log_count", 0)
        st.metric("Logs Analyzed", log_count)
    
    with col3:
        timestamp = result.get("analysis_timestamp", datetime.now())
        st.metric("Analysis Time", timestamp.strftime("%H:%M:%S"))


if __name__ == "__main__":
    main()
