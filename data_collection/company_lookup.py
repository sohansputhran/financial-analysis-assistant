import yfinance as yf
import pandas as pd
import re
import os

def is_probable_ticker(text):
    s = text.strip()
    ticker_pattern = r"^[A-Z0-9\.\-]{1,6}$"
    return bool(re.fullmatch(ticker_pattern, s)) and len(s) <= 6

def search_by_ticker(ticker):
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        info = ticker_obj.info
        if info and "shortName" in info and "symbol" in info:
            return [{
                "symbol": info["symbol"],
                "shortname": info["shortName"],
                "exchange": info.get("exchange", "")
            }]
    except Exception as e:
        print(f"Error fetching info for ticker '{ticker}': {e}")
    return []

def search_by_name(name, tickers_csv="data/tickers.csv", max_results=5):
    # Search in tickers.csv for matching company names
    if not os.path.exists(tickers_csv):
        print("Ticker CSV not found. Please generate 'data/tickers.csv' first.")
        return []
    df = pd.read_csv(tickers_csv)
    matches = df[df['name'].str.contains(name, case=False, na=False)].head(max_results)
    results = []
    for _, row in matches.iterrows():
        results.append({
            "symbol": row["ticker"].upper(),
            "name": row["name"],
            "exchange": row.get("exchange", "")
        })
    return results

def lookup_company(query, tickers_csv="data/tickers.csv"):
    """
    Given a user query (ticker or company name), return list of possible matches (dicts).
    """
    if is_probable_ticker(query):
        results = search_by_ticker(query)
        if results:
            return results
        # fallback: search in CSV by ticker
        if os.path.exists(tickers_csv):
            df = pd.read_csv(tickers_csv)
            matches = df[df['ticker'].str.upper() == query.upper()]
            if not matches.empty:
                row = matches.iloc[0]
                return [{
                    "symbol": row["ticker"].upper(),
                    "name": row["name"],
                    "exchange": row.get("exchange", "")
                }]
        # Not found as ticker, try as name (rare case)
        return search_by_name(query, tickers_csv)
    else:
        # Treat as company name search
        results = search_by_name(query, tickers_csv)
        return results