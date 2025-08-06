import requests

def fetch_company_filings_json(cik):
    # Remove leading zeros for the URL, but pad cik to 10 digits for input
    cik_str = str(int(cik))
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    print(f"Fetching filings for CIK: {cik_str} from {url}")
    headers = {"User-Agent": "Your Name (your@email.com)"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

# Example: Get all filings and find latest 10-K or 10-Q
def get_latest_filing(cik, form_types=("10-K", "10-Q")):
    data = fetch_company_filings_json(cik)
    filings = data["filings"]["recent"]
    for form_type in form_types:
        for idx, form in enumerate(filings["form"]):
            if form == form_type:
                filing_url = "https://www.sec.gov" + filings["primaryDocument"][idx].replace(".htm", "") + "-index.htm"
                filing_date = filings["filingDate"][idx]
                accession_no = filings["accessionNumber"][idx].replace("-", "")
                doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no}/{filings['primaryDocument'][idx]}"
                return {
                    "form": form,
                    "filing_date": filing_date,
                    "filing_url": filing_url,
                    "doc_url": doc_url
                }
    return None
