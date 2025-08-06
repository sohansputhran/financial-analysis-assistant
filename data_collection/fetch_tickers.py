import requests
import json
import pandas as pd
import os

# URLs for exchange symbol lists
sources = {
    "nasdaq": "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_full_tickers.json",
    "nyse": "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse/nyse_full_tickers.json",
    "amex": "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/amex/amex_full_tickers.json"
}

def fetch_all_tickers():
    records = []

    for exchange, url in sources.items():
        print(f"Fetching from {exchange.upper()}...")
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            # print(data[:5])  # Print first 5 entries for debugging
            for entry in data:
                records.append({
                    "ticker": entry.get("symbol", ""),
                    "name": entry.get("name", ""),
                    "exchange": exchange.upper()
                })
        else:
            print(f"❌ Failed to fetch from {exchange.upper()} ({res.status_code})")

    df = pd.DataFrame(records).drop_duplicates(subset="ticker")
    df = df[df["ticker"].str.isupper()]  # Filter clean tickers

    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "tickers.csv")
    df.to_csv(output_path, index=False)
    print(f"✅ Saved {len(df)} tickers to: {output_path}")

if __name__ == "__main__":
    print("Starting ticker fetching...")
    fetch_all_tickers()
    print("Ticker fetching complete!")