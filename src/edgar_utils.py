import requests
import pandas as pd
import re
import time
from bs4 import BeautifulSoup
import random
import dotenv
from io import StringIO

# Load environment variables
dotenv.load_dotenv()

NAME = dotenv.get_key(dotenv.find_dotenv(), "NAME")
EMAIL = dotenv.get_key(dotenv.find_dotenv(), "EMAIL")

# SEC-compliant financial data extractor
class SECCompliantExtractor:
    """
    SEC-compliant financial data extractor that respects rate limits
    """

    def __init__(self, user_name=NAME, user_agent_email=EMAIL):
        """
        Initialize with proper headers for SEC compliance
        
        Args:
            user_agent_email: Your email address for SEC compliance
            user_name: Your name or application name
        Returns:
            None
        """
        self.headers = {
            'User-Agent': f'{user_name} {user_agent_email} (Educational Use)',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def extract_financial_data(self, url):
        """
        Extract financial data with rate limiting compliance
        Args:
            url: URL of the SEC filing HTML page
        Returns:
            dict: DataFrames for income statement, balance sheet, and cash flow
        """
        try:
            response = self._fetch_with_retry(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print("Parsing HTML content...")
            return self._parse_financial_tables(soup)
            
        except Exception as e:
            print(f"Error extracting financial data: {e}")
            return {}
    
    def _fetch_with_retry(self, url, max_retries=3, base_delay=10):
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
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    print("Successfully fetched data")
                    return response
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
    
    def _parse_financial_tables(self, soup):
        """
        Parse financial tables from BeautifulSoup object
        Args:
            soup (BeautifulSoup object): Parsed HTML document
        Returns:
            dict: DataFrames for income statement, balance sheet, and cash flow
        """
        # Find financial statement tables using keywords
        financial_keywords = {
            'income_statement': [
                'income statements', 'consolidated statements of income',
                'statements of operations', 'revenue', 'net income', 
                'operating income', 'gross margin', 'earnings per share'
            ],
            # 'balance_sheet': [
            #     'balance sheets', 'consolidated balance sheets', 
            #     'total assets', 'total liabilities', 'stockholders equity',
            #     'current assets', 'current liabilities', 'long-term debt'
            # ],
            # 'cash_flow': [
            #     'cash flows statements', 'consolidated statements of cash flows',
            #     'cash from operations', 'operating activities', 'operations', 
            #     'income tax', 'net income', 'financing'
            # ]
        }
        
        results = {}
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables to analyze")
        
        for stmt_type, keywords in financial_keywords.items():
            print(f"Looking for {stmt_type.replace('_', ' ').title()}...")
            
            best_table = None
            best_score = 0
            
            for table in tables:
                # Get context around the table
                context = self._get_table_context(table, soup)
                score = self._score_table_relevance(context, table, keywords)

                if score > best_score and score > 0.3:  # Minimum threshold
                    best_score = score
                    best_table = table
            
            if best_table is not None:
                df = self._extract_table_data(best_table)
                if not df.empty:
                    results[stmt_type] = df
                    print(f"  Found {stmt_type}: {df.shape[0]} rows, {df.shape[1]} columns")
                else:
                    print(f"  Found table but couldn't extract data for {stmt_type}")
            else:
                print(f"  No suitable table found for {stmt_type}")
        
        return results
    
    def _get_table_context(self, table, soup, context_chars=1000):
        """
        Get text context around a table
        Args:
            table (BeautifulSoup element): The HTML table element
            soup (BeautifulSoup object): The full HTML document
            context_chars (int): Number of characters to include before and after the table
        Returns:
            str: Cleaned text context around the table
        """

        # Convert table to string to find its position
        table_html = str(table)
        soup_html = str(soup)

        # Find where this table appears in the full document
        table_pos = soup_html.find(table_html)
        
        if table_pos == -1:         # Table not found
            return ""
        
        # Extract context before and after the table
        start = max(0, table_pos - context_chars)                                   # Don't go before document start
        end = min(len(soup_html), table_pos + len(table_html) + context_chars)      # Don't go past document end
        
        # Get the HTML snippet with context
        context_html = soup_html[start:end]

        # Parse the context HTML and extract clean text
        context_soup = BeautifulSoup(context_html, 'html.parser')
        
        # Return lowercased text for easier keyword matching
        return context_soup.get_text().lower()
    
    def _score_table_relevance(self, context, table, keywords):
        """
        Score how relevant a table is for a financial statement type
        Args:
            context (str): Text surrounding the table (headings, paragraphs nearby)
            table (BeautifulSoup element): The HTML table element
            keywords (list): Keywords specific to the financial statement type
        Returns:
            float: Relevance score between 0.0 and 1.0+
        """
        context_lower = context.lower()
        table_text = table.get_text().lower()
        
        # Score based on keyword matches in CONTEXT (surrounding text)
        # This catches titles like "CONSOLIDATED STATEMENTS OF INCOME"
        context_score = sum(1 for keyword in keywords if keyword in context_lower)
        
        # Score based on keyword matches in the TABLE itself
        # This catches column headers and row labels
        table_score = sum(1 for keyword in keywords if keyword in table_text)
        
        # Check for financial data patterns
        # Look for dollar amounts: $1,234 or $(1,234)
        has_money_pattern = bool(re.search(r'\$[\d,]+|\([\d,]+\)', table_text))

        # Look for year columns: 2023, 2024, 2025
        has_years = bool(re.search(r'20\d{2}', table_text))
        
        # Calculate final score
        score = (context_score * 0.4 + 
                 table_score * 0.4 + 
                 has_money_pattern * 0.1 + 
                 has_years * 0.1
                 )
        
        # Normalize score by number of keywords
        # This ensures all statement types have comparable scores
        return score / len(keywords)  # Normalize
    
    def _extract_table_data(self, table):
        """
        Extract data from HTML table and convert to pandas DataFrame
        Args:
            table: BeautifulSoup table element 
        Returns:
            pd.DataFrame: Cleaned financial data
        """
        try:
            # pandas.read_html() is very robust and handles complex table structures
            dfs = pd.read_html(StringIO(str(table)))
            print(dfs)
            if dfs:
                df = dfs[0]                         # Take the first (and usually only) DataFrame
                return self._clean_dataframe(df)
        except:
            pass                    # If pandas fails, fall back to manual extraction
        
        # Manual extraction (fallback for complex cases)
        rows = []
        for tr in table.find_all('tr'):                  # Iterate over table rows
            row = []
            for cell in tr.find_all(['td', 'th']):       # Get both data and header cells
                row.append(cell.get_text().strip())      # Clean cell text
            if row:                                      # Only add non-empty rows
                rows.append(row)
        
        if not rows:
            return pd.DataFrame()                        # Return empty DataFrame if no rows found

        # Use first row as column headers
        df = pd.DataFrame(rows[1:], columns=rows[0] if rows else [])
        return self._clean_dataframe(df)
    
    def _clean_dataframe(self, df):
        """
        Clean and format DataFrame
        Args:
            df (pd.DataFrame): Raw DataFrame
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        if df.empty:
            return df
        
        # Remove empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, thresh=0.6 * len(df))
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Clean monetary values
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).apply(self._clean_monetary_value)
        
        return df
    
    def _clean_monetary_value(self, value):
        """
        Clean monetary values by removing $, commas, and handling negatives
        Args:
            value (str): Raw cell value
        Returns:
            str: Cleaned value (e.g., '1234.56', '-1234.56', or '')
        """
        if pd.isna(value) or value in ['nan', 'None', '']:
            return ''
        
        value = str(value).strip()
        
        # Handle parentheses as negative
        if '(' in value and ')' in value:
            value = '-' + re.sub(r'[(),]', '', value)
        
        # Remove $ and commas but keep decimals and negatives
        value = re.sub(r'[$,]', '', value)
        
        return value

# Example usage
def main():
    """
    Main execution with multiple approaches
    """
    url = "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm"
    
    print("SEC-Compliant Financial Data Extraction")
    print("=" * 50)
    
    # Direct extraction with rate limiting
    print("\nDirect extraction with proper headers and delays")
    extractor = SECCompliantExtractor()  # Use your email
    
    try:
        financial_data = extractor.extract_financial_data(url)
        
        for stmt_type, df in financial_data.items():
            print(f"\n{stmt_type.replace('_', ' ').title()}:")
            print(f"Shape: {df.shape}")
            if not df.empty:
                filename = f"{stmt_type}.csv"
                df.to_csv(filename, index=False)
                print(f"Saved to {filename}")
    
    except Exception as e:
        print(f"Direct extraction failed: {e}")

if __name__ == "__main__":
    main()