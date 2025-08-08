# import streamlit as st
# from data_collection.company_lookup import lookup_company

# st.title("Gemini Financial Analyst")

# company_query = st.text_input("Enter company name or ticker (e.g. Apple or AAPL):")
# if company_query:
#     results = lookup_company(company_query)
#     if results:
#         st.write("Matching Companies:")
#         for idx, item in enumerate(results):
#             st.write(f"{item['symbol']} - {item['name']} ({item['cik']})")
#         # Optionally, let user select one if multiple results found
#     else:
#         st.warning("No matching companies found.")


import streamlit as st
from pathlib import Path
from src.extraction.edgar_client import get_cik_for_ticker, get_filing_index, get_filing_html_url, download_filing_html
from src.extraction.table_parser import parse_financial_tables
from src.utils.io import save_tables_bundle, load_latest_tables_bundle

st.set_page_config(page_title="Financial Analysis Assistant", layout="wide")

st.title("Financial Analysis Assistant")
st.caption("Local viewer for SEC filing tables (raw → cleaned later)")

with st.sidebar:
    st.subheader("Load Data")
    ticker = st.text_input("Ticker", "MSFT").strip().upper()
    form_type = st.selectbox("Form", ["10-K", "10-Q"])
    count = st.slider("How many recent filings to look at", 1, 10, 1)
    run = st.button("Fetch & Parse")

if run and ticker:
    try:
        cik = get_cik_for_ticker(ticker)
        filings = get_filing_index(cik, form_type=form_type, count=count)
        if filings.empty:
            st.error("No filings found.")
        else:
            recent_filing = filings.iloc[0]  # latest
            acc = recent_filing["accessionNumber"]
            url = get_filing_html_url(cik, recent_filing)
            html = download_filing_html(url)
            is_df, bs_df, cf_df = parse_financial_tables(html)

            bundle = {
                "ticker": ticker,
                "cik": cik,
                "form": form_type,
                "accession": acc,
                "source_url": url,
                "income_statement": is_df,
                "balance_sheet": bs_df,
                "cash_flow": cf_df,
            }
            path = save_tables_bundle(bundle)
            st.success(f"Parsed and saved: {path.name}")
            st.session_state["tables_bundle"] = bundle
    except Exception as e:
        st.exception(e)

# Try to load last saved if none in session (handy for dev)
if "tables_bundle" not in st.session_state:
    last = load_latest_tables_bundle()
    if last:
        st.session_state["tables_bundle"] = last

bundle = st.session_state.get("tables_bundle")
if not bundle:
    st.info("Use the sidebar to fetch a filing.")
else:
    st.markdown(f"**Ticker:** {bundle['ticker']}  •  **Form:** {bundle['form']}  •  **Accession:** {bundle['accession']}")
    tabs = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow", "Downloads"])

    with tabs[0]:
        st.subheader("Income Statement (raw)")
        if bundle["income_statement"] is not None:
            st.dataframe(bundle["income_statement"], use_container_width=True)
        else:
            st.warning("Not found in this filing.")

    with tabs[1]:
        st.subheader("Balance Sheet (raw)")
        if bundle["balance_sheet"] is not None:
            st.dataframe(bundle["balance_sheet"], use_container_width=True)
        else:
            st.warning("Not found in this filing.")

    with tabs[2]:
        st.subheader("Cash Flow (raw)")
        if bundle["cash_flow"] is not None:
            st.dataframe(bundle["cash_flow"], use_container_width=True)
        else:
            st.warning("Not found in this filing.")

    with tabs[3]:
        st.subheader("Download")
        from src.utils.io import dfs_to_csv_bytes
        if any([bundle["income_statement"] is not None, bundle["balance_sheet"] is not None, bundle["cash_flow"] is not None]):
            csv_zip = dfs_to_csv_bytes(bundle)
            st.download_button("Download CSV (ZIP)", data=csv_zip, file_name=f"{bundle['ticker']}_{bundle['accession']}.zip")
        else:
            st.info("Nothing to download yet.")
