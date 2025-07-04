import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw
import io
import sys
import os

# Add parent directory to path for security import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simple_security import require_portal_access

st.set_page_config(
    page_title="ML Model Playground",
    page_icon="🤖",
    layout="wide"
)

# Protect against direct port access and validate session tokens (App ID 2)
require_portal_access(app_id=2)

st.title("🤖 ML Model Playground")
st.markdown("Interactive machine learning demo application")

# Sidebar
st.sidebar.header("Model Configuration")
model_type = st.sidebar.selectbox("Model Type", ["Linear Regression", "Classification", "Clustering"])
sample_size = st.sidebar.slider("Sample Size", 50, 500, 100)

# Generate data based on model type
@st.cache_data
def generate_ml_data(model_type, size):
    np.random.seed(42)
    
    if model_type == "Linear Regression":
        x = np.random.randn(size)
        y = 2 * x + 1 + np.random.randn(size) * 0.5
        return pd.DataFrame({'X': x, 'Y': y})
    
    elif model_type == "Classification":
        x1 = np.random.randn(size//2) + 2
        y1 = np.random.randn(size//2) + 2
        x2 = np.random.randn(size//2) - 2
        y2 = np.random.randn(size//2) - 2
        
        data = pd.DataFrame({
            'X': np.concatenate([x1, x2]),
            'Y': np.concatenate([y1, y2]),
            'Class': ['A'] * (size//2) + ['B'] * (size//2)
        })
        return data
    
    else:  # Clustering
        centers = [(2, 2), (-2, -2), (2, -2)]
        data = []
        for center in centers:
            cluster_size = size // 3
            x = np.random.randn(cluster_size) * 0.8 + center[0]
            y = np.random.randn(cluster_size) * 0.8 + center[1]
            data.extend(list(zip(x, y)))
        
        df = pd.DataFrame(data, columns=['X', 'Y'])
        return df

data = generate_ml_data(model_type, sample_size)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"{model_type} Visualization")
    
    if model_type == "Classification":
        import plotly.express as px
        fig = px.scatter(data, x='X', y='Y', color='Class', 
                        title=f"{model_type} Data")
        st.plotly_chart(fig, use_container_width=True)
    else:
        import plotly.express as px
        fig = px.scatter(data, x='X', y='Y', 
                        title=f"{model_type} Data")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Model Statistics")
    
    st.metric("Data Points", len(data))
    st.metric("Features", len(data.columns))
    
    if model_type == "Classification":
        class_counts = data['Class'].value_counts()
        st.write("Class Distribution:")
        st.bar_chart(class_counts)
    else:
        st.metric("Mean X", f"{data['X'].mean():.2f}")
        st.metric("Mean Y", f"{data['Y'].mean():.2f}")

# Model training simulation
st.subheader("Model Training")

if st.button("🚀 Train Model"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        progress_bar.progress(i + 1)
        status_text.text(f'Training... {i+1}%')
        
    status_text.text('Training complete!')
    
    # Fake model results
    st.success("Model trained successfully!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Accuracy", "94.5%")
    with col2:
        st.metric("Training Time", "2.3s")
    with col3:
        st.metric("Model Size", "1.2MB")

# Feature importance (fake)
st.subheader("Feature Importance")
features = ['Feature 1', 'Feature 2', 'Feature 3', 'Feature 4']
importance = np.random.rand(4)
importance_df = pd.DataFrame({
    'Feature': features,
    'Importance': importance
})

st.bar_chart(importance_df.set_index('Feature'))

# Data preview
st.subheader("Data Preview")
st.dataframe(data.head(10), use_container_width=True)

# Footer
st.markdown("---")
st.markdown("🤖 **Demo App 2 - ML Playground** | Running on port 8503") 