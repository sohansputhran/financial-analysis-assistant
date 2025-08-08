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
            print(best_table)
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
            # print(dfs)
            if dfs:
                df = dfs[0]
                print(df)                         # Take the first (and usually only) DataFrame
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
        df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)
        

        df.to_csv("Removed_Empty_Rows_Columns.csv", index=False)
        # Handle multi-level headers (common in SEC filings)
        df = self._consolidate_headers(df)
        df.to_csv("Consolidated_Headers.csv", index=False)
        # Remove duplicate columns
        df = self._remove_duplicate_columns(df)
        df.to_csv("Removed_Duplicate_Columns.csv", index=False)
        # Clean and standardize column names
        df.columns = self._clean_column_names(df.columns)
        df.to_csv("Removed_Empty_Rows_Columns.csv", index=False)
        # Remove rows that are actually header rows or separators
        df = self._remove_header_rows(df)
        df.to_csv("Removed_Header_Rows.csv", index=False)

        # Clean monetary values
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).apply(self._clean_monetary_value)
        df.to_csv("Cleaned_Monetary_Values.csv", index=False)
        # Step 7: Remove any remaining empty rows after cleaning
        df = df.dropna(how='all').reset_index(drop=True)
        
        # Step 8: Remove rows that are mostly empty (less than 2 non-empty cells)
        df = self._remove_sparse_rows(df)

        return df
    
    def _consolidate_headers(self, df):
        """
        Handle multi-level headers common in SEC filings
        """
        # Check if first row contains header information
        first_row = df.iloc[0] if len(df) > 0 else None
        second_row = df.iloc[1] if len(df) > 1 else None
        
        # If first row has few non-empty values and second row looks like headers
        if (first_row is not None and second_row is not None and 
            first_row.notna().sum() <= 2 and second_row.notna().sum() > first_row.notna().sum()):
            
            # Combine first and second row to create better column names
            new_columns = []
            for i, (col1, col2) in enumerate(zip(first_row, second_row)):
                col1_str = str(col1) if pd.notna(col1) else ""
                col2_str = str(col2) if pd.notna(col2) else ""
                
                # Combine non-empty parts
                if col1_str.strip() and col2_str.strip() and col1_str.strip() != col2_str.strip():
                    combined = f"{col1_str.strip()} {col2_str.strip()}"
                elif col2_str.strip():
                    combined = col2_str.strip()
                elif col1_str.strip():
                    combined = col1_str.strip()
                else:
                    combined = f"Column_{i}"
                
                new_columns.append(combined)
            
            # Update columns and remove the header rows
            df.columns = new_columns
            df = df.iloc[2:].reset_index(drop=True)
            
            print("Applied multi-header consolidation")
        
        return df

    def _remove_duplicate_columns(self, df):
        """
        Remove duplicate columns by checking for exact matches
        Args:
            df (pd.DataFrame): DataFrame to clean
        Returns:
            pd.DataFrame: DataFrame with duplicate columns removed
        """
        # Find columns with duplicate names
        seen_columns = {}
        new_columns = []
        
        for col in df.columns:
            col_str = str(col).strip()
            if col_str in seen_columns:
                # Check if the column content is actually different
                if not df[col].equals(df[seen_columns[col_str]]):
                    # Different content, rename it
                    new_columns.append(f"{col_str}_duplicate_{seen_columns[col_str] + 1}")
                    seen_columns[col_str] += 1
                else:
                    # Same content, mark for removal
                    new_columns.append(f"__REMOVE__{col_str}")
            else:
                seen_columns[col_str] = 0
                new_columns.append(col_str)
        
        # Update column names
        df.columns = new_columns
        
        # Remove columns marked for removal
        df = df.loc[:, ~df.columns.str.startswith('__REMOVE__')]
        
        # Also remove columns that are completely identical to others
        df = df.loc[:, ~df.columns.duplicated()]
        
        return df
    
    def _clean_column_names(self, columns):
        """
        Clean and standardize column names
        Args:
            columns (pd.Index): Original column names
        Returns:
            list: Cleaned column names
        """
        clean_columns = []
    
        for i, col in enumerate(columns):
            col_str = str(col).strip()
            
            # Remove common pandas multi-index artifacts
            col_str = re.sub(r'Unnamed: \d+', '', col_str)
            col_str = re.sub(r'level_\d+', '', col_str)
            
            # Clean up whitespace and special characters
            col_str = re.sub(r'\s+', ' ', col_str)  # Multiple spaces to single
            col_str = col_str.replace('\n', ' ').replace('\t', ' ')
            col_str = col_str.strip()
            
            # If column name is still empty or just numbers, create a meaningful name
            if not col_str or col_str.isdigit() or col_str in ['nan', 'None']:
                if i == 0:
                    col_str = "Description"
                else:
                    col_str = f"Column_{i}"
            
            clean_columns.append(col_str)
        
        return clean_columns

    def _remove_header_rows(self, df):
        """
        Remove rows that are actually header rows or separators
        Args:
            df (pd.DataFrame): DataFrame to clean
        Returns:
            pd.DataFrame: DataFrame with header rows removed
        """
        if df.empty:
            return df
        
        rows_to_remove = []
        
        for idx, row in df.iterrows():
            row_text = ' '.join([str(val) for val in row if pd.notna(val)]).lower()
            
            # Check if row contains header-like text
            header_indicators = [
                'year ended', 'months ended', 'as of', 'for the', 
                'in millions', 'in thousands', 'except per share',
                'unaudited', 'audited', 'consolidated', 'see accompanying'
            ]
            
            # Check if row is mostly the same repeated value (separator row)
            non_empty_values = [str(val).strip() for val in row if pd.notna(val) and str(val).strip()]
            if len(set(non_empty_values)) <= 1 and len(non_empty_values) > 1:
                rows_to_remove.append(idx)
                continue
            
            # Check for header indicators
            if any(indicator in row_text for indicator in header_indicators):
                rows_to_remove.append(idx)
                continue
            
            # Check if first column contains only year numbers (likely a header)
            first_col_val = str(row.iloc[0]).strip()
            if first_col_val.isdigit() and len(first_col_val) == 4 and first_col_val.startswith('20'):
                # Only remove if this pattern appears in multiple consecutive rows
                continue
        
        if rows_to_remove:
            df = df.drop(rows_to_remove).reset_index(drop=True)
            print(f"Removed {len(rows_to_remove)} header/separator rows")
        
        return df

    def _remove_sparse_rows(self, df):
        """
        Remove rows that are mostly empty (less than 2 non-empty cells)
        Args:
            df (pd.DataFrame): DataFrame to clean
        Returns:
            pd.DataFrame: DataFrame with sparse rows removed
        """
        if df.empty:
            return df
        
        # Calculate minimum number of non-empty cells required
        min_cells = max(2, len(df.columns) // 3)  # At least 2 cells or 1/3 of columns
        
        # Count non-empty cells per row
        row_counts = df.notna().sum(axis=1)
        
        # Keep rows with sufficient non-empty cells
        mask = row_counts >= min_cells
        
        removed_count = (~mask).sum()
        if removed_count > 0:
            print(f"Removed {removed_count} sparse rows (< {min_cells} non-empty cells)")
        
        return df[mask].reset_index(drop=True)

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
    # url = "https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm"
    # url = "https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000032019323000010/aapl-20230930.htm"
    url = 'https://www.sec.gov/Archives/edgar/data/70858/000007085825000139/bac-20241231.htm'
    
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