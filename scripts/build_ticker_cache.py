import requests
import pandas as pd
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()
NAME = os.getenv("NAME")
EMAIL = os.getenv("EMAIL")

def get_ticker_cik_mapping():
    print("Fetching ticker to CIK mapping from SEC...")
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": f"{NAME} {EMAIL}"}
    r = requests.get(url, headers=headers)
    print(f"Response status: {r.status_code}")
    r.raise_for_status()
    data = r.json()  # shape: {"0": {"ticker":"AAPL","cik_str":320193,"title":"Apple Inc."}, ...}

    mapping = {}
    for rec in data.values():
        t = rec["ticker"].upper()
        c = str(rec["cik_str"]).zfill(10)
        mapping[t] = c
    # Turn into a DataFrame for easier searching
    df = pd.DataFrame([
        {
            "ticker": v["ticker"].upper(),
            "cik": str(v["cik_str"]).zfill(10),
            "name": v["title"]
        } for v in mapping.values()
    ])
    
    df = df.drop_duplicates(subset="ticker")

    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ticker_cik.json")
    df.to_json(output_path, orient="records", lines=True)
    print(f"✅ Saved {len(df)} tickers to: {output_path}")

if __name__ == "__main__":
    print("Starting ticker with cik fetching...")
    get_ticker_cik_mapping()
    print("Ticker with cik fetching complete!")