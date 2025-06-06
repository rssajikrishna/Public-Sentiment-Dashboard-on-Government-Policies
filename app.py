import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
from textblob import TextBlob
import requests
import json
from collections import Counter
import time
from data_scraper import SocialMediaScraper

scraper = SocialMediaScraper()
data = scraper.scrape_policy_data('Digital India', days_back=7)
# Page config
st.set_page_config(
    page_title="Public Sentiment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

class SentimentAnalyzer:
    def __init__(self):
        self.policy_keywords = {
            'Digital India': ['digital india', 'digitization', 'e-governance', 'digital payment'],
            'Swachh Bharat': ['swachh bharat', 'clean india', 'cleanliness', 'toilet construction'],
            'Make in India': ['make in india', 'manufacturing', 'atmanirbhar', 'self reliant'],
            'Jan Dhan Yojana': ['jan dhan', 'bank account', 'financial inclusion'],
            'Ayushman Bharat': ['ayushman bharat', 'healthcare', 'health insurance', 'pmjay']
        }
        
    def clean_text(self, text):
        """Clean and preprocess text data"""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'@\w+|#\w+', '', text)
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def get_sentiment(self, text):
        """Get sentiment score using TextBlob"""
        if not text:
            return 0, 'neutral'
        
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            return polarity, 'positive'
        elif polarity < -0.1:
            return polarity, 'negative'
        else:
            return polarity, 'neutral'
    
    def classify_policy(self, text):
        """Classify text into policy categories"""
        text_lower = text.lower()
        for policy, keywords in self.policy_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return policy
        return 'General'
    
    def extract_region(self, text):
        """Extract region information from text"""
        regions = ['mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata', 'hyderabad', 
                  'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur']
        
        text_lower = text.lower()
        for region in regions:
            if region in text_lower:
                return region.title()
        return 'Unknown'

class DataGenerator:
    """Generate sample social media data for demonstration"""
    
    def __init__(self):
        self.sample_posts = [
            "Digital India initiative has made government services more accessible online",
            "Swachh Bharat mission has improved cleanliness in our city significantly",
            "Make in India policy is boosting local manufacturing jobs",
            "Jan Dhan Yojana helped my family open their first bank account",
            "Ayushman Bharat provides good healthcare coverage for poor families",
            "Digital payments are now easier thanks to government initiatives",
            "Clean India mission still needs more work in rural areas",
            "Manufacturing sector growing well under current policies",
            "Financial inclusion programs reaching remote villages effectively",
            "Healthcare reforms showing positive results in urban areas",
            "Government's digital push facing challenges in rural connectivity",
            "Cleanliness drives working well in my neighborhood",
            "Local industries benefiting from government manufacturing policies",
            "Banking services improved significantly in last few years",
            "Health insurance schemes helping middle class families"
        ]
        
        self.regions = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad']
        self.platforms = ['Twitter', 'Reddit', 'YouTube']
    
    def generate_sample_data(self, num_posts=500):
        """Generate sample social media data"""
        data = []
        start_date = datetime.now() - timedelta(days=90)
        
        for i in range(num_posts):
            # Random post selection and modification
            base_post = np.random.choice(self.sample_posts)
            
            # Add some variation to make posts unique
            if np.random.random() < 0.3:
                sentiments = ['great', 'excellent', 'amazing', 'poor', 'terrible', 'disappointing']
                base_post = f"{base_post} {np.random.choice(sentiments)}"
            
            # Random date within last 90 days
            random_days = np.random.randint(0, 90)
            post_date = start_date + timedelta(days=random_days)
            
            data.append({
                'date': post_date,
                'text': base_post,
                'platform': np.random.choice(self.platforms),
                'region': np.random.choice(self.regions),
                'likes': np.random.randint(1, 1000),
                'shares': np.random.randint(0, 100)
            })
        
        return pd.DataFrame(data)

def main():
    st.markdown('<h1 class="main-header">🏛️ Public Sentiment Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### Analyzing Government Policy Sentiment from Social Media")
    
    # Initialize components
    analyzer = SentimentAnalyzer()
    data_gen = DataGenerator()
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    
    # Data source selection
    data_source = st.sidebar.selectbox(
        "Select Data Source",
        ["Sample Data (Demo)", "Upload CSV File"]
    )
    
    # Load data
    if data_source == "Upload CSV File":
        uploaded_file = st.sidebar.file_uploader("Choose CSV file", type="csv")
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
        else:
            st.warning("Please upload a CSV file or use sample data")
            return
    else:
        # Generate sample data
        with st.spinner("Generating sample data..."):
            df = data_gen.generate_sample_data(500)
    
    # Process data
    with st.spinner("Processing sentiment analysis..."):
        # Clean text
        df['cleaned_text'] = df['text'].apply(analyzer.clean_text)
        
        # Get sentiment
        sentiment_data = df['cleaned_text'].apply(analyzer.get_sentiment)
        df['sentiment_score'] = sentiment_data.apply(lambda x: x[0])
        df['sentiment_label'] = sentiment_data.apply(lambda x: x[1])
        
        # Classify policy
        df['policy'] = df['cleaned_text'].apply(analyzer.classify_policy)
        
        # Extract region (if not already present)
        if 'region' not in df.columns:
            df['region'] = df['cleaned_text'].apply(analyzer.extract_region)
        
        # Convert date
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
    
    # Filters
    st.sidebar.subheader("Filters")
    
    # Date range filter
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(df['date'].min().date(), df['date'].max().date()),
        min_value=df['date'].min().date(),
        max_value=df['date'].max().date()
    )
    
    # Policy filter
    policies = ['All'] + list(df['policy'].unique())
    selected_policy = st.sidebar.selectbox("Select Policy", policies)
    
    # Region filter
    regions = ['All'] + list(df['region'].unique())
    selected_region = st.sidebar.selectbox("Select Region", regions)
    
    # Platform filter
    platforms = ['All'] + list(df['platform'].unique())
    selected_platform = st.sidebar.selectbox("Select Platform", platforms)
    
    # Apply filters
    filtered_df = df.copy()
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['date'].dt.date >= date_range[0]) & 
            (filtered_df['date'].dt.date <= date_range[1])
        ]
    
    if selected_policy != 'All':
        filtered_df = filtered_df[filtered_df['policy'] == selected_policy]
    
    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['region'] == selected_region]
    
    if selected_platform != 'All':
        filtered_df = filtered_df[filtered_df['platform'] == selected_platform]
    
    if filtered_df.empty:
        st.error("No data available for selected filters")
        return
    
    # Main dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Posts", len(filtered_df))
    
    with col2:
        positive_pct = len(filtered_df[filtered_df['sentiment_label'] == 'positive']) / len(filtered_df) * 100
        st.metric("Positive Sentiment", f"{positive_pct:.1f}%")
    
    with col3:
        avg_sentiment = filtered_df['sentiment_score'].mean()
        st.metric("Average Sentiment", f"{avg_sentiment:.3f}")
    
    with col4:
        total_engagement = filtered_df['likes'].sum() if 'likes' in filtered_df.columns else 0
        st.metric("Total Likes", f"{total_engagement:,}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sentiment Distribution")
        sentiment_counts = filtered_df['sentiment_label'].value_counts()
        fig_pie = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            color_discrete_map={'positive': '#2E8B57', 'neutral': '#FFD700', 'negative': '#DC143C'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Sentiment by Policy")
        policy_sentiment = filtered_df.groupby(['policy', 'sentiment_label']).size().reset_index(name='count')
        fig_bar = px.bar(
            policy_sentiment,
            x='policy',
            y='count',
            color='sentiment_label',
            color_discrete_map={'positive': '#2E8B57', 'neutral': '#FFD700', 'negative': '#DC143C'}
        )
        fig_bar.update_xaxes(tickangle=45)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Sentiment trends over time
    st.subheader("Sentiment Trends Over Time")
    monthly_sentiment = filtered_df.groupby(['month', 'sentiment_label']).size().reset_index(name='count')
    monthly_sentiment['month_str'] = monthly_sentiment['month'].astype(str)
    
    fig_line = px.line(
        monthly_sentiment,
        x='month_str',
        y='count',
        color='sentiment_label',
        color_discrete_map={'positive': '#2E8B57', 'neutral': '#FFD700', 'negative': '#DC143C'}
    )
    fig_line.update_xaxes(title="Month")
    fig_line.update_yaxes(title="Number of Posts")
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Regional analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sentiment by Region")
        region_sentiment = filtered_df.groupby('region')['sentiment_score'].mean().sort_values(ascending=False)
        fig_region = px.bar(
            x=region_sentiment.index,
            y=region_sentiment.values,
            color=region_sentiment.values,
            color_continuous_scale='RdYlGn'
        )
        fig_region.update_xaxes(title="Region", tickangle=45)
        fig_region.update_yaxes(title="Average Sentiment Score")
        st.plotly_chart(fig_region, use_container_width=True)
    
    with col2:
        st.subheader("Platform Analysis")
        platform_sentiment = filtered_df.groupby('platform')['sentiment_score'].mean().sort_values(ascending=False)
        fig_platform = px.bar(
            x=platform_sentiment.index,
            y=platform_sentiment.values,
            color=platform_sentiment.values,
            color_continuous_scale='RdYlBu'
        )
        fig_platform.update_xaxes(title="Platform")
        fig_platform.update_yaxes(title="Average Sentiment Score")
        st.plotly_chart(fig_platform, use_container_width=True)
    
    # Key insights
    st.subheader("📈 Key Insights")
    
    insights = []
    
    # Most positive policy
    policy_avg_sentiment = filtered_df.groupby('policy')['sentiment_score'].mean()
    most_positive_policy = policy_avg_sentiment.idxmax()
    insights.append(f"**Most Positive Policy**: {most_positive_policy} (avg sentiment: {policy_avg_sentiment.max():.3f})")
    
    # Most negative policy
    most_negative_policy = policy_avg_sentiment.idxmin()
    insights.append(f"**Most Criticized Policy**: {most_negative_policy} (avg sentiment: {policy_avg_sentiment.min():.3f})")
    
    # Best performing region
    region_avg_sentiment = filtered_df.groupby('region')['sentiment_score'].mean()
    best_region = region_avg_sentiment.idxmax()
    insights.append(f"**Most Positive Region**: {best_region} (avg sentiment: {region_avg_sentiment.max():.3f})")
    
    # Platform insights
    platform_avg_sentiment = filtered_df.groupby('platform')['sentiment_score'].mean()
    best_platform = platform_avg_sentiment.idxmax()
    insights.append(f"**Most Positive Platform**: {best_platform} (avg sentiment: {platform_avg_sentiment.max():.3f})")
    
    for insight in insights:
        st.markdown(f"• {insight}")
    
    # Recent posts sample
    st.subheader("📝 Recent Posts Sample")
    recent_posts = filtered_df.nlargest(5, 'date')[['date', 'text', 'sentiment_label', 'policy', 'platform']]
    st.dataframe(recent_posts, use_container_width=True)
    
    # Export functionality
    st.subheader("📊 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download Processed Data"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"sentiment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Generate Summary Report"):
            summary = f"""
# Sentiment Analysis Summary Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
- Total Posts Analyzed: {len(filtered_df)}
- Date Range: {filtered_df['date'].min().strftime('%Y-%m-%d')} to {filtered_df['date'].max().strftime('%Y-%m-%d')}
- Average Sentiment Score: {filtered_df['sentiment_score'].mean():.3f}

## Sentiment Distribution
- Positive: {len(filtered_df[filtered_df['sentiment_label'] == 'positive'])} ({len(filtered_df[filtered_df['sentiment_label'] == 'positive'])/len(filtered_df)*100:.1f}%)
- Neutral: {len(filtered_df[filtered_df['sentiment_label'] == 'neutral'])} ({len(filtered_df[filtered_df['sentiment_label'] == 'neutral'])/len(filtered_df)*100:.1f}%)
- Negative: {len(filtered_df[filtered_df['sentiment_label'] == 'negative'])} ({len(filtered_df[filtered_df['sentiment_label'] == 'negative'])/len(filtered_df)*100:.1f}%)

## Key Findings
- Most Positive Policy: {most_positive_policy}
- Most Criticized Policy: {most_negative_policy}
- Best Performing Region: {best_region}
- Most Positive Platform: {best_platform}
            """
            
            st.download_button(
                label="Download Report",
                data=summary,
                file_name=f"sentiment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )

if __name__ == "__main__":
    main()