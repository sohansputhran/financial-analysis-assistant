"""Financial Analysis Assistant - AI-powered financial analysis tool."""

__version__ = "0.1.0"
__author__ = "Sohan Sanjeeva Puthran"
__email__ = "puthran.sohan@gmail.com"

# src/main.py
"""Main Streamlit application for Financial Analysis Assistant."""

import streamlit as st
import logging
from pathlib import Path

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent))

from config.logging_config import setup_logging
from config.settings import get_config

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    try:
        # Load configuration
        config = get_config()
        
        # Configure Streamlit page
        st.set_page_config(
            page_title="Financial Analysis Assistant",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Apply custom CSS based on theme
        if config.theme == "dark":
            st.markdown("""
                <style>
                .main { background-color: #0e1117; }
                .sidebar .sidebar-content { background-color: #262730; }
                </style>
                """, unsafe_allow_html=True)
        
        # Main app header
        st.title("📊 Financial Analysis Assistant")
        st.markdown("*AI-powered financial analysis using Gemini AI*")
        
        # Sidebar
        with st.sidebar:
            st.header("🔧 Configuration")
            st.info("This is Sprint 1 - Basic setup complete!")
            
            # API Key status
            if config.gemini_api_key and config.gemini_api_key != "your_gemini_api_key_here":
                st.success("✅ Gemini API Key configured")
            else:
                st.error("❌ Please configure Gemini API Key in .env file")
            
            # Optional API keys
            optional_apis = [
                ("Alpha Vantage", config.alpha_vantage_api_key),
                ("Financial Modeling Prep", config.fmp_api_key)
            ]
            
            for api_name, api_key in optional_apis:
                if api_key and api_key != f"your_{api_name.lower().replace(' ', '_')}_key_here":
                    st.success(f"✅ {api_name} API configured")
                else:
                    st.warning(f"⚠️ {api_name} API not configured (optional)")
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("🏢 Company Analysis")
            
            # Company input form
            with st.form("company_input"):
                company_input = st.text_input(
                    "Enter Company Name or Ticker Symbol",
                    placeholder="e.g., Apple Inc. or AAPL",
                    help="Enter a company name or stock ticker symbol to analyze"
                )
                
                analysis_options = st.multiselect(
                    "Select Analysis Options",
                    ["Financial Statements", "Financial Ratios", "Trend Analysis", "Valuation"],
                    default=["Financial Statements", "Financial Ratios"]
                )
                
                submitted = st.form_submit_button("🔍 Analyze Company")
            
            if submitted and company_input:
                with st.spinner(f"Analyzing {company_input}..."):
                    # Placeholder for analysis logic (will be implemented in Sprint 2-3)
                    st.success(f"✅ Analysis request received for: {company_input}")
                    st.info("📋 Selected analysis: " + ", ".join(analysis_options))
                    
                    # Mock results display
                    st.subheader("📈 Analysis Results")
                    st.write("This is where analysis results will be displayed.")
                    st.write("**Status**: Ready for Sprint 2 implementation")
                    
                    # Mock data display
                    import pandas as pd
                    mock_data = pd.DataFrame({
                        "Metric": ["Revenue", "Net Income", "Total Assets", "Total Debt"],
                        "Value": ["$100B", "$25B", "$350B", "$50B"],
                        "Status": ["✅", "✅", "✅", "⚠️"]
                    })
                    st.dataframe(mock_data, hide_index=True)
        
        with col2:
            st.header("📊 Dashboard")
            
            # Configuration info
            st.subheader("⚙️ Current Configuration")
            config_data = {
                "Theme": config.theme.title(),
                "Log Level": config.log_level,
                "Cache Duration": f"{config.cache_duration_hours}h",
                "Max Companies": config.max_companies_comparison
            }
            
            for key, value in config_data.items():
                st.metric(key, value)
            
            # System status
            st.subheader("🖥️ System Status")
            st.success("✅ Configuration loaded")
            st.success("✅ Logging configured")
            st.success("✅ Directories created")
            st.info("📋 Ready for Sprint 2 development")
        
        # Footer
        st.markdown("---")
        st.markdown(
            "Built with ❤️ using Streamlit and Gemini AI | "
            f"Version {config.project_root.name} v0.1.0"
        )
        
        logger.info("Application loaded successfully")
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"An error occurred: {e}")
        st.info("Please check the logs for more details.")

if __name__ == "__main__":
    main()