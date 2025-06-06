#!/usr/bin/env python3
"""
Deployment helper script for Public Sentiment Dashboard
This script helps set up and deploy the application
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print("✅ Python version:", sys.version.split()[0])
    return True

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False

def setup_environment():
    """Set up environment file"""
    env_template = ".env.template"
    env_file = ".env"
    
    if not os.path.exists(env_file):
        if os.path.exists(env_template):
            shutil.copy(env_template, env_file)
            print(f"✅ Created {env_file} from template")
            print("📝 Please edit .env file with your API keys")
        else:
            # Create basic .env file
            with open(env_file, 'w') as f:
                f.write("# Social Media API Keys\n")
                f.write("TWITTER_BEARER_TOKEN=your_token_here\n")
                f.write("YOUTUBE_API_KEY=your_key_here\n")
            print(f"✅ Created basic {env_file} file")
    else:
        print(f"✅ {env_file} already exists")

def create_sample_data():
    """Create sample data directory and file"""
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    sample_file = sample_dir / "sample_posts.csv"
    if not sample_file.exists():
        sample_data = """date,text,platform,region,likes,shares
2025-01-01,Digital India initiative is transforming governance,Twitter,Mumbai,150,25
2025-01-02,Swachh Bharat mission improving cleanliness in cities,Reddit,Delhi,89,12
2025-01-03,Make in India boosting manufacturing sector significantly,YouTube,Bangalore,200,45
2025-01-04,Jan Dhan Yojana helping financial inclusion in villages,Twitter,Chennai,175,30
2025-01-05,Ayushman Bharat providing healthcare access to poor,Reddit,Kolkata,120,18
2025-01-06,Digital payments becoming popular due to government push,Twitter,Hyderabad,95,15
2025-01-07,Clean India campaign needs more focus on rural areas,YouTube,Pune,80,8
2025-01-08,Manufacturing policies creating jobs in industrial sectors,Twitter,Ahmedabad,110,22
2025-01-09,Banking services improved significantly in remote areas,Reddit,Jaipur,65,9
2025-01-10,Healthcare reforms showing positive results nationwide,YouTube,Lucknow,140,35"""
        
        with open(sample_file, 'w') as f:
            f.write(sample_data)
        print(f"✅ Created {sample_file}")
    else:
        print(f"✅ {sample_file} already exists")

def check_streamlit():
    """Check if Streamlit is working"""
    try:
        import streamlit
        print(f"✅ Streamlit version: {streamlit.__version__}")
        return True
    except ImportError:
        print("❌ Streamlit not found")
        return False

def run_tests():
    """Run basic tests"""
    print("🧪 Running basic tests...")
    
    # Test imports
    try:
        import pandas as pd
        import plotly.express as px
        import textblob
        print("✅ All required modules can be imported")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test TextBlob
    try:
        from textblob import TextBlob
        blob = TextBlob("This is a test sentence")
        sentiment = blob.sentiment.polarity
        print(f"✅ TextBlob working (test sentiment: {sentiment:.3f})")
    except Exception as e:
        print(f"❌ TextBlob error: {e}")
        return False
    
    return True

def start_application():
    """Start the Streamlit application"""
    print("🚀 Starting Streamlit application...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

def main():
    """Main deployment function"""
    print("🏛️ Public Sentiment Dashboard - Deployment Setup")
    print("=" * 50)
    
    # Check system requirements
    if not check_python_version():
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Setup environment
    setup_environment()
    
    # Create sample data
    create_sample_data()
    
    # Check Streamlit
    if not check_streamlit():
        return
    
    # Run tests
    if not run_tests():
        print("⚠️ Some tests failed, but you can still try running the app")
    
    print("\n✅ Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys (optional for demo)")
    print("2. Run: streamlit run app.py")
    print("3. Open browser to: http://localhost:8501")
    
    # Ask if user wants to start now
    response = input("\n🚀 Start the application now? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        start_application()

if __name__ == "__main__":
    main()