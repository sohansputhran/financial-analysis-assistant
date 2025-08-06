# Financial Analysis Assistant

An open-source Streamlit application that leverages AI and public data to automate financial analysis for any US publicly traded company.  
**Input a company name or ticker. Get the latest SEC filings, advanced data extraction, financial ratios, and interactive visualizations—all in one place!**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com/)
[![Google AI](https://img.shields.io/badge/Google%20AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
---

## 🚀 Features

- **Intelligent Company Lookup:** Enter either a ticker symbol or a company name; the app maps input to the correct SEC CIK, ensuring accuracy.
- **Latest Financial Filings:** Automatically fetches the most recent 10-K and 10-Q filings directly from the SEC EDGAR database.
- **Scalable & Modular:** Easily extendable codebase for rapid addition of new features (AI models, data sources, visualizations).

---

## 🛠️ Tech Stack

- **Python** (pandas, requests, yfinance)
- **Streamlit** (for UI)
- **SEC EDGAR API** (official filings)
- **AI/LLMs**: Google Gemini or other LLMs (for document extraction & analysis)
- **Data**: [SEC ticker-to-CIK mapping](https://www.sec.gov/files/company_tickers.json), custom ticker CSV

---

## ✅ Current Progress

- [x] **User Input Flexibility:** Lookup by ticker or company name.
- [x] **Accurate Ticker → CIK Mapping:** Pulls official mapping from the SEC.
- [x] **Fetches Latest Filings:** Retrieves the most recent 10-K/10-Q for any US public company.
- [ ] **Basic Filing Download & Preview:** Download filings as HTML for further parsing/analysis.

---

## 🔮 Future Roadmap

- [ ] **AI-Powered Data Extraction:** Use Gemini AI (or another LLM) to extract key tables (Income Statement, Balance Sheet, Cash Flow) from filings.
- [ ] **Financial Ratio Calculation:** Automate calculation of profitability, liquidity, and leverage ratios.
- [ ] **Interactive Dashboard:** Visualize statements, ratios, and trends in Streamlit.
- [ ] **Automated Valuation Models:** DCF and comparables analysis.
- [ ] **Multi-Company Comparison:** Side-by-side analysis for peer benchmarking.
- [ ] **Downloadable Reports:** Export data and analysis in CSV or PDF.
- [ ] **User Authentication (Optional):** Save analyses and custom reports for registered users.

---

## 💡 Usage

```bash
# (Install requirements)
pip install -r requirements.txt

# (Run the app)
streamlit run app.py
```

Enter a company name or ticker (e.g., AAPL or Apple Inc).

The app finds the correct SEC CIK and fetches the latest financial filings.

Preview and (soon) analyze company financials directly in the browser.

## 📁 Project Structure
```
.
├── app.py                    # Streamlit app entry point
├── src/
│   ├── edgar_utils.py        # Fetch SEC filings and handle CIK lookup
│   ├── llm_utils.py          # (Planned) Gemini/LLM integration for extraction
│   └── finance_utils.py      # (Planned) Ratio calculation & financial logic
├── data/
│   └── company_cik.csv           # (Optional) Local ticker data
├── data_collection/
│   ├── fetch_cik.py          # Fetch all the company names, tickers and cik for all publicly traded companies
│   └── fetch_tickers.py      # Fetch all the company names, tickers and exchange for all publicly traded companies
├── requirements.txt
└── README.md
```

## 🤝 Contributing

PRs, suggestions, and feature requests are welcome!
If you use or extend this project, please consider starring or contributing.

## 📬 Contact

Sohan Puthran on [LinkedIn](https://www.linkedin.com/in/sohansputhran/)

**⭐️ Star this repo if you find it helpful!**