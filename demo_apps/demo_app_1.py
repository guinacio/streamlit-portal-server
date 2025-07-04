import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for security import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simple_security import require_portal_access

st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Protect against direct port access and validate session tokens (App ID 1)
require_portal_access(app_id=1)

st.title("📊 Analytics Dashboard Demo")
st.markdown("This is a sample analytics dashboard for testing the Streamlit Portal")

# Sidebar
st.sidebar.header("Settings")
date_range = st.sidebar.slider("Days of data", 1, 30, 7)
chart_type = st.sidebar.selectbox("Chart Type", ["Line", "Bar", "Area"])

# Generate sample data
@st.cache_data
def generate_data(days):
    dates = [datetime.now() - timedelta(days=i) for i in range(days)]
    data = {
        'Date': dates,
        'Sales': np.random.normal(1000, 200, days),
        'Users': np.random.normal(500, 100, days),
        'Revenue': np.random.normal(5000, 1000, days)
    }
    return pd.DataFrame(data)

df = generate_data(date_range)

# Metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Sales", f"{df['Sales'].sum():.0f}", f"{df['Sales'].iloc[-1] - df['Sales'].iloc[-2]:.0f}")

with col2:
    st.metric("Total Users", f"{df['Users'].sum():.0f}", f"{df['Users'].iloc[-1] - df['Users'].iloc[-2]:.0f}")

with col3:
    st.metric("Total Revenue", f"${df['Revenue'].sum():.0f}", f"${df['Revenue'].iloc[-1] - df['Revenue'].iloc[-2]:.0f}")

# Charts
st.subheader("Performance Over Time")

col1, col2 = st.columns(2)

with col1:
    if chart_type == "Line":
        fig = px.line(df, x='Date', y='Sales', title='Sales Trend')
    elif chart_type == "Bar":
        fig = px.bar(df, x='Date', y='Sales', title='Sales Trend')
    else:
        fig = px.area(df, x='Date', y='Sales', title='Sales Trend')
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = px.scatter(df, x='Users', y='Revenue', title='Users vs Revenue', 
                      color='Sales', size='Sales')
    st.plotly_chart(fig2, use_container_width=True)

# Data table
st.subheader("Raw Data")
st.dataframe(df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("🚀 **Demo App 1 - Analytics Dashboard** | Running on port 8502") 