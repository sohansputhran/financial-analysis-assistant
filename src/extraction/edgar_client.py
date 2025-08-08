"""
edgar_client.py
---------------
Handles SEC EDGAR API requests:
- Map ticker → CIK
- Get filing index for 10-K / 10-Q
- Download filing HTML/iXBRL
"""

import requests
import pandas as pd
import json
from pathlib import Path
import os
import dotenv
import random
import time

# Load environment variables
dotenv.load_dotenv()
NAME = os.getenv("NAME")
EMAIL = os.getenv("EMAIL")

HEADERS = {"User-Agent": f"{NAME} {EMAIL}"}

TICKER_CACHE = Path("data/ticker_cik.json")

def load_ticker_cik() -> dict:
    """Load cached ticker→CIK mapping."""
    if TICKER_CACHE.exists():
        return pd.read_json(TICKER_CACHE, orient='records', lines=True)
    raise FileNotFoundError("Ticker→CIK cache not found. Run fetch_cik.py first.")

def get_cik_for_ticker(ticker: str) -> str:
    """Return zero-padded CIK for ticker."""
    ticker_cik = load_ticker_cik()
    cik = ticker_cik[ticker_cik['ticker'] == ticker.upper()]['cik'].values[0]
    if not cik:
        raise ValueError(f"CIK not found for ticker {ticker}")
    return str(cik).zfill(10)

def get_filing_index(cik: str, form_type: str = "10-K", count: int = 5) -> pd.DataFrame:
    """Get recent filings metadata from SEC for given CIK and form type."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS)
    
    resp.raise_for_status()
    data = resp.json()

    filings = data.get("filings", {}).get("recent", {})
    df = pd.DataFrame(filings)
    df = df[df["form"] == form_type].head(count).copy()
    df["cik"] = cik
    return df

def get_filing_html_url(cik: str, req_filing: pd.Series) -> str:
    """Build URL for filing's main HTML page."""
    accession_no = req_filing["accessionNumber"]
    accession_no_nodash = accession_no.replace("-", "")
    return f"https://sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_nodash}/{req_filing['primaryDocument']}"

def download_filing_html(url: str, max_retries=3, base_delay=10) -> str:
    """
        Fetch HTML with rate limiting and retry logic
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between requests (seconds)
        Returns:
            response: requests.Response object
        """

    for attempt in range(max_retries + 1):
        try:
            # Add random delay to avoid being too predictable
            delay = base_delay + random.uniform(1, 5)
            print(f"Waiting {delay:.1f} seconds before request (attempt {attempt + 1})...")
            time.sleep(delay)

            response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code == 200:
                print("Successfully fetched data")
                return response.text
            
            elif response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', base_delay * (attempt + 1)))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
            else:
                print(f"HTTP {response.status_code}: {response.reason}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                time.sleep(base_delay * (attempt + 1))
                
    raise Exception(f"Failed to fetch {url} after {max_retries + 1} attempts")
