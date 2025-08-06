import streamlit as st
from data_collection.company_lookup import lookup_company

st.title("Gemini Financial Analyst")

company_query = st.text_input("Enter company name or ticker (e.g. Apple or AAPL):")
if company_query:
    results = lookup_company(company_query)
    if results:
        st.write("Matching Companies:")
        for idx, item in enumerate(results):
            st.write(f"{item['symbol']} - {item['name']} ({item['exchange']})")
        # Optionally, let user select one if multiple results found
    else:
        st.warning("No matching companies found.")