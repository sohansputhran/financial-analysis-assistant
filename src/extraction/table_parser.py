"""
table_parser.py
---------------
Parses HTML/iXBRL filings to extract:
- Income Statement
- Balance Sheet
- Cash Flow Statement

Uses BeautifulSoup + Pandas to output raw DataFrames.
"""

from bs4 import BeautifulSoup
import pandas as pd
import re
from typing import Tuple
from io import StringIO
import dotenv

# Load environment variables
dotenv.load_dotenv()

NAME = dotenv.get_key(dotenv.find_dotenv(), "NAME")
EMAIL = dotenv.get_key(dotenv.find_dotenv(), "EMAIL")

def parse_financial_tables(html_text: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Extract Income Statement, Balance Sheet, and Cash Flow tables from SEC HTML filing.
    Returns: (income_df, balance_df, cashflow_df)
    """
    try:
        soup = BeautifulSoup(html_text, 'html.parser')

        print("Parsing HTML content...")
        return _parse_financial_tables(soup)

    except Exception as e:
        print(f"Error extracting financial data: {e}")
        return {}


def _parse_financial_tables(soup):
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
        'balance_sheet': [
            'balance sheets', 'consolidated balance sheets', 
            'total assets', 'total liabilities', 'stockholders equity',
            'current assets', 'current liabilities', 'long-term debt'
        ],
        'cash_flow': [
            'cash flows statements', 'consolidated statements of cash flows',
            'cash from operations', 'operating activities', 'operations', 
            'income tax', 'net income', 'financing'
        ]
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
            context = _get_table_context(table, soup)
            score = _score_table_relevance(context, table, keywords)

            if score > best_score and score > 0.3:  # Minimum threshold
                best_score = score
                best_table = table
        print(best_table)
        if best_table is not None:
            df = _extract_table_data(best_table)
            if not df.empty:
                results[stmt_type] = df
                print(f"  Found {stmt_type}: {df.shape[0]} rows, {df.shape[1]} columns")
            else:
                print(f"  Found table but couldn't extract data for {stmt_type}")
        else:
            print(f"  No suitable table found for {stmt_type}")
    
    return results

def _get_table_context(table, soup, context_chars=1000):
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

def _score_table_relevance(context, table, keywords):
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

def _extract_table_data(table):
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
            return df
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
    return df
