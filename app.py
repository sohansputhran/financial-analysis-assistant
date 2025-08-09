import streamlit as st
import pandas as pd
from pathlib import Path
import traceback
from src.extraction.edgar_client import get_cik_for_ticker, get_filing_index, get_filing_html_url, download_filing_html
from src.extraction.table_parser import parse_financial_tables
from src.utils.io import save_tables_bundle, load_latest_tables_bundle, save_clean_payload, load_clean_payload_from
from src.cleaning.llm_cleaner import init_gemini, clean_with_gemini, validate_data_quality
from src.cleaning.canonical_schema import Payload
import os

st.set_page_config(page_title="Financial Analysis Assistant", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏦 Financial Analysis Assistant")
st.caption("Extract and clean SEC filing data with AI")

# Sidebar for data extraction
with st.sidebar:
    st.subheader("📥 Extract Data")
    ticker = st.text_input("Ticker Symbol", "MSFT").strip().upper()
    form_type = st.selectbox("Form Type", ["10-K", "10-Q"])
    count = st.slider("Recent filings to search", 1, 10, 1)
    
    extract_btn = st.button("🚀 Fetch & Parse", use_container_width=True)
    
    st.divider()
    
    # Environment check
    st.subheader("🔧 Environment")
    gemini_key = st.text_input("Gemini API Key", type="password", 
                              help="Enter your Google Gemini API key for cleaning")
    if gemini_key:
        import os
        os.environ["GEMINI_API_KEY"] = gemini_key
        st.success("✅ API key set")
    elif not st.session_state.get("gemini_checked"):
        if os.getenv("GEMINI_API_KEY"):
            st.success("✅ API key found in environment")
        else:
            st.error("❌ No API key found")
        st.session_state["gemini_checked"] = True

# Main extraction logic
if extract_btn and ticker:
    with st.spinner(f"Fetching {form_type} data for {ticker}..."):
        try:
            # Get company info
            cik = get_cik_for_ticker(ticker)
            st.info(f"Found CIK: {cik}")
            
            # Get filings
            filings = get_filing_index(cik, form_type=form_type, count=count)
            if filings.empty:
                st.error("❌ No filings found for this ticker and form type.")
            else:
                # Process most recent filing
                recent_filing = filings.iloc[0]
                accession = recent_filing["accessionNumber"]
                filing_date = recent_filing.get("filingDate", "Unknown")
                
                st.info(f"Processing filing: {accession} (Filed: {filing_date})")
                
                # Download and parse
                url = get_filing_html_url(cik, recent_filing)
                html = download_filing_html(url)
                is_df, bs_df, cf_df = parse_financial_tables(html)
                
                # Create bundle
                bundle = {
                    "ticker": ticker,
                    "cik": cik,
                    "form": form_type,
                    "accession": accession,
                    "filing_date": filing_date,
                    "source_url": url,
                    "income_statement": is_df,
                    "balance_sheet": bs_df,
                    "cash_flow": cf_df,
                }
                
                # Save and store in session
                path = save_tables_bundle(bundle)
                st.session_state["tables_bundle"] = bundle
                st.session_state.pop("clean_payload", None)  # Clear previous cleaning
                
                st.markdown(f"""
                <div class="success-box">
                    <strong>✅ Success!</strong><br>
                    Parsed and saved: {path.name}<br>
                    Found {len([df for df in [is_df, bs_df, cf_df] if df is not None])} financial statements
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"❌ Error during extraction: {str(e)}")
            with st.expander("View error details"):
                st.code(traceback.format_exc())

# Load last saved data if none in session
if "tables_bundle" not in st.session_state:
    last_bundle = load_latest_tables_bundle()
    if last_bundle:
        st.session_state["tables_bundle"] = last_bundle

# Display extracted data
bundle = st.session_state.get("tables_bundle")
if not bundle:
    st.info("👆 Use the sidebar to fetch SEC filing data.")
else:
    # Header info
    st.markdown(f"""
    **📊 Current Data:** {bundle['ticker']} • {bundle['form']} • {bundle['accession']} 
    • Filed: {bundle.get('filing_date', 'Unknown')}
    """)
    
    # Raw data tabs
    tabs = st.tabs(["📈 Income Statement", "📊 Balance Sheet", "💰 Cash Flow", "📁 Downloads"])
    
    def display_dataframe(df, statement_name):
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True, height=400)
            st.caption(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        else:
            st.warning(f"❌ {statement_name} not found in this filing")
    
    with tabs[0]:
        st.subheader("Income Statement (Raw)")
        display_dataframe(bundle["income_statement"], "Income Statement")
    
    with tabs[1]:
        st.subheader("Balance Sheet (Raw)")
        display_dataframe(bundle["balance_sheet"], "Balance Sheet")
    
    with tabs[2]:
        st.subheader("Cash Flow Statement (Raw)")
        display_dataframe(bundle["cash_flow"], "Cash Flow Statement")
    
    with tabs[3]:
        st.subheader("Download Raw Data")
        from src.utils.io import dfs_to_csv_bytes
        
        available_statements = [df for df in [bundle["income_statement"], 
                                            bundle["balance_sheet"], 
                                            bundle["cash_flow"]] if df is not None]
        
        if available_statements:
            csv_zip = dfs_to_csv_bytes(bundle)
            st.download_button(
                "📥 Download CSV (ZIP)", 
                data=csv_zip, 
                file_name=f"{bundle['ticker']}_{bundle['accession']}_raw.zip",
                mime="application/zip"
            )
        else:
            st.info("No data available for download")
    
    st.divider()
    
    # AI Cleaning Section
    st.subheader("🤖 AI Data Cleaning")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Use Google's Gemini AI to clean and standardize the financial data")
    with col2:
        clean_btn = st.button("🧹 Clean with AI", use_container_width=True, type="primary")
    
    if clean_btn:
        # Check API key
        if not os.getenv("GEMINI_API_KEY"):
            st.error("❌ Please set your Gemini API key in the sidebar first")
        else:
            with st.spinner("🤖 AI is cleaning the data... This may take a moment."):
                try:
                    # Initialize model
                    model = init_gemini()
                    
                    # Prepare company info
                    company = {
                        "cik": bundle["cik"],
                        "ticker": bundle["ticker"],
                        "name": None  # Could be extracted from filing if needed
                    }
                    
                    # Clean with Gemini
                    payload = clean_with_gemini(
                        model,
                        company,
                        bundle["income_statement"],
                        bundle["balance_sheet"],
                        bundle["cash_flow"],
                        extra_context=f"Form: {bundle['form']} URL: {bundle['source_url']}"
                    )
                    
                    # Validate quality
                    quality_report = validate_data_quality(payload)
                    
                    # Save cleaned data
                    latest_folder = Path("data/processed")
                    if latest_folder.exists():
                        folders = sorted([p for p in latest_folder.iterdir() if p.is_dir()], reverse=True)
                        if folders:
                            save_clean_payload(folders[0], payload.dict())
                    
                    # Store in session
                    st.session_state["clean_payload"] = payload.dict()
                    st.session_state["quality_report"] = quality_report
                    
                    st.markdown("""
                    <div class="success-box">
                        <strong>✅ Cleaning Complete!</strong><br>
                        Data has been successfully cleaned and standardized using AI
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show quality report
                    if quality_report["warnings"]:
                        with st.expander("⚠️ Quality Warnings", expanded=False):
                            for warning in quality_report["warnings"]:
                                st.warning(warning)
                    
                    # Show stats
                    stats = quality_report["stats"]
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Periods", stats["periods_count"])
                    with col2:
                        st.metric("Income Items", stats["income_statement_items"])
                    with col3:
                        st.metric("Balance Items", stats["balance_sheet_items"])
                    with col4:
                        st.metric("Cash Flow Items", stats["cash_flow_items"])
                    
                except Exception as e:
                    st.error(f"❌ Cleaning failed: {str(e)}")
                    with st.expander("View error details"):
                        st.code(traceback.format_exc())
    
    # Display cleaned data if available
    clean_payload = st.session_state.get("clean_payload")
    
    # Try to load from disk if not in session
    if not clean_payload:
        try:
            dirs = sorted([p for p in Path("data/processed").iterdir() if p.is_dir()], reverse=True)
            if dirs:
                clean_payload = load_clean_payload_from(dirs[0])
                if clean_payload:
                    st.session_state["clean_payload"] = clean_payload
        except Exception:
            pass
    
    if clean_payload:
        st.divider()
        st.subheader("✨ Cleaned & Standardized Data")
        
        # Metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Currency", clean_payload.get("currency", "N/A"))
        with col2:
            scale_val = clean_payload.get("scale", 1)
            scale_label = {
                1: "Ones",
                1_000: "Thousands", 
                1_000_000: "Millions",
                1_000_000_000: "Billions"
            }.get(scale_val, str(scale_val))
            st.metric("Scale", scale_label)
        with col3:
            periods = clean_payload.get("periods", [])
            st.metric("Periods", len(periods))
        
        # Period details
        if periods:
            with st.expander("📅 Period Details", expanded=False):
                period_df = pd.DataFrame(periods)
                st.dataframe(period_df, use_container_width=True)
        
        # Financial statements as clean tables
        def create_clean_dataframe(block_data):
            if not block_data:
                return pd.DataFrame()
            
            rows = []
            for line_item, series_data in block_data.items():
                if isinstance(series_data, dict) and "values" in series_data:
                    row = {"Line Item": line_item}
                    row.update(series_data["values"])
                    rows.append(row)
            
            if not rows:
                return pd.DataFrame()
            
            df = pd.DataFrame(rows).set_index("Line Item")
            
            # Format columns as dates if they look like dates
            for col in df.columns:
                if pd.to_datetime(col, errors='coerce') is not pd.NaT:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except:
                        pass
            
            return df
        
        # Display cleaned statements in tabs
        clean_tabs = st.tabs(["📈 Income Statement", "📊 Balance Sheet", "💰 Cash Flow"])
        
        with clean_tabs[0]:
            is_clean_df = create_clean_dataframe(clean_payload.get("income_statement"))
            if not is_clean_df.empty:
                st.dataframe(is_clean_df, use_container_width=True)
            else:
                st.info("No income statement data available")
        
        with clean_tabs[1]:
            bs_clean_df = create_clean_dataframe(clean_payload.get("balance_sheet"))
            if not bs_clean_df.empty:
                st.dataframe(bs_clean_df, use_container_width=True)
            else:
                st.info("No balance sheet data available")
        
        with clean_tabs[2]:
            cf_clean_df = create_clean_dataframe(clean_payload.get("cash_flow"))
            if not cf_clean_df.empty:
                st.dataframe(cf_clean_df, use_container_width=True)
            else:
                st.info("No cash flow data available")
        
        # Download cleaned data
        st.subheader("📥 Download Cleaned Data")
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON download
            import json
            json_data = json.dumps(clean_payload, indent=2)
            st.download_button(
                "📄 Download JSON",
                data=json_data,
                file_name=f"{bundle['ticker']}_{bundle['accession']}_cleaned.json",
                mime="application/json"
            )
        
        with col2:
            # CSV download (if we have dataframes)
            available_clean_dfs = []
            for name, df in [("income_statement", is_clean_df), 
                           ("balance_sheet", bs_clean_df), 
                           ("cash_flow", cf_clean_df)]:
                if not df.empty:
                    available_clean_dfs.append((name, df))
            
            if available_clean_dfs:
                import io
                import zipfile
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for name, df in available_clean_dfs:
                        csv_data = df.to_csv()
                        zip_file.writestr(f"{name}_cleaned.csv", csv_data)
                
                st.download_button(
                    "📊 Download CSV (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"{bundle['ticker']}_{bundle['accession']}_cleaned.zip",
                    mime="application/zip"
                )

# Footer
st.divider()
st.caption("💡 Tip: Set your Gemini API key in the sidebar to enable AI cleaning features")