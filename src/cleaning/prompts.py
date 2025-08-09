"""
Enhanced prompts for financial data cleaning with LLM
"""

BASE_RULES = """
You are an expert financial analyst specializing in SEC filing data cleanup and standardization.

CORE RULES:
1. UNITS & SCALE: 
   - Detect scale from context (thousands/millions/billions)
   - Apply consistent scale to ALL numeric values
   - Common indicators: "in millions", "$'000", "in thousands"

2. NUMERIC PROCESSING:
   - Parentheses (123) or -123 → negative numbers
   - Dashes, blanks, "—", "N/A" → null
   - Remove: $, commas, footnote marks (¹, ², etc.)
   - Keep decimal precision when present

3. PERIOD IDENTIFICATION:
   - Parse column headers for dates and periods
   - Format: YYYY-MM-DD (e.g., "2023-12-31")
   - Determine fiscal periods: Q1-Q4 or FY
   - Match period labels to actual dates

4. LINE ITEM MAPPING:
   - Map company-specific labels to canonical schema
   - Handle variations (e.g., "Net sales" → "Revenue")
   - Leave unmappable items as null with explanatory notes

5. DATA VALIDATION:
   - Check basic accounting identities where possible
   - Flag unusual or suspicious values in notes
   - Ensure period alignment across statements

OUTPUT: Return ONLY valid JSON. No explanatory text.
"""

CANONICAL_MAPPING = {
    "income_statement": {
        "Revenue": [
            "net sales", "total revenue", "revenues", "net revenues", 
            "sales", "total net sales", "net product sales", "product revenue"
        ],
        "CostOfRevenue": [
            "cost of sales", "cost of goods sold", "cost of revenue", 
            "cost of products sold", "cost of net sales"
        ],
        "GrossProfit": [
            "gross profit", "gross margin", "gross income"
        ],
        "OperatingExpenses": [
            "total operating expenses", "operating expenses", 
            "selling and administrative", "sg&a"
        ],
        "OperatingIncome": [
            "operating income", "operating profit", "income from operations",
            "operating earnings", "operating profit (loss)"
        ],
        "InterestExpense": [
            "interest expense", "interest", "interest on debt"
        ],
        "PretaxIncome": [
            "income before taxes", "pretax income", "earnings before tax",
            "income before income taxes"
        ],
        "IncomeTaxExpense": [
            "income tax expense", "provision for income taxes", 
            "income taxes", "tax expense"
        ],
        "NetIncome": [
            "net income", "net earnings", "profit", "net profit",
            "net income (loss)", "earnings"
        ]
    },
    "balance_sheet": {
        "CashAndCashEquivalents": [
            "cash and cash equivalents", "cash", "cash and equivalents"
        ],
        "ShortTermInvestments": [
            "short-term investments", "marketable securities", 
            "short term investments"
        ],
        "AccountsReceivableNet": [
            "accounts receivable", "receivables", "accounts receivable, net"
        ],
        "Inventory": [
            "inventory", "inventories"
        ],
        "TotalCurrentAssets": [
            "total current assets", "current assets"
        ],
        "PPENet": [
            "property, plant and equipment, net", "property and equipment", 
            "pp&e", "fixed assets"
        ],
        "TotalAssets": [
            "total assets"
        ],
        "AccountsPayable": [
            "accounts payable", "payables"
        ],
        "TotalCurrentLiabilities": [
            "total current liabilities", "current liabilities"
        ],
        "LongTermDebt": [
            "long-term debt", "long term debt", "debt", "borrowings"
        ],
        "TotalLiabilities": [
            "total liabilities"
        ],
        "CommonStockAndAPIC": [
            "common stock", "additional paid-in capital", "paid-in capital",
            "stockholders' equity", "common shares"
        ],
        "RetainedEarnings": [
            "retained earnings", "accumulated earnings"
        ],
        "TotalEquity": [
            "total equity", "shareholders' equity", "stockholders' equity",
            "total shareholders' equity"
        ]
    },
    "cash_flow": {
        "NetCashFromOperations": [
            "net cash provided by operating activities", 
            "cash from operations", "operating cash flow",
            "net cash from operating activities"
        ],
        "NetCashFromInvesting": [
            "net cash used in investing activities",
            "cash from investing", "investing cash flow",
            "net cash from investing activities"
        ],
        "NetCashFromFinancing": [
            "net cash used in financing activities",
            "cash from financing", "financing cash flow",
            "net cash from financing activities"
        ],
        "DepreciationAndAmortization": [
            "depreciation and amortization", "depreciation", "amortization"
        ],
        "ShareBasedCompensation": [
            "share-based compensation", "stock-based compensation",
            "equity compensation"
        ],
        "CapitalExpenditures": [
            "capital expenditures", "capex", "purchases of property and equipment",
            "capital investments"
        ],
        "DividendsPaid": [
            "dividends paid", "cash dividends paid", "dividend payments"
        ],
        "NetChangeInCash": [
            "net change in cash", "increase in cash", "change in cash"
        ]
    }
}

def build_comprehensive_prompt(company_info, raw_tables, detected_scale):
    """
    Build a comprehensive cleaning prompt for Gemini
    """
    scale_text, scale_value = detected_scale
    
    prompt = f"""
FINANCIAL DATA CLEANING TASK

COMPANY: {company_info.get('ticker', 'Unknown')} (CIK: {company_info.get('cik', 'Unknown')})
DETECTED SCALE: {scale_text} (numeric scale: {scale_value})

INSTRUCTIONS:
Convert the raw SEC filing tables below into clean, structured JSON format following the canonical schema.

CLEANING RULES:
1. Currency: Assume USD unless stated otherwise
2. Scale: Apply {scale_value} consistently to all numeric values
3. Numbers: Convert (123) to -123, dashes/blanks to null, remove $,commas
4. Dates: Format as YYYY-MM-DD, determine fiscal periods (Q1-Q4/FY)
5. Mapping: Use canonical names from the schema below

CANONICAL SCHEMA STRUCTURE:
{{
  "company": {{"ticker": "string", "name": "string|null", "cik": "string"}},
  "currency": "USD",
  "scale": {scale_value},
  "periods": [
    {{"label": "string", "start_date": "YYYY-MM-DD|null", "end_date": "YYYY-MM-DD", "fy": number, "fp": "Q1|Q2|Q3|Q4|FY", "is_audited": boolean}}
  ],
  "income_statement": {{
    "Revenue": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "CostOfRevenue": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "GrossProfit": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "OperatingExpenses": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "OperatingIncome": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "InterestExpense": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "OtherIncomeExpenseNet": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "PretaxIncome": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "IncomeTaxExpense": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "NetIncome": {{"values": {{"YYYY-MM-DD": number|null}}}}
  }},
  "balance_sheet": {{
    "CashAndCashEquivalents": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "ShortTermInvestments": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "AccountsReceivableNet": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "Inventory": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "TotalCurrentAssets": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "PPENet": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "TotalAssets": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "AccountsPayable": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "TotalCurrentLiabilities": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "LongTermDebt": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "TotalLiabilities": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "CommonStockAndAPIC": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "RetainedEarnings": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "TotalEquity": {{"values": {{"YYYY-MM-DD": number|null}}}}
  }},
  "cash_flow": {{
    "NetCashFromOperations": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "NetCashFromInvesting": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "NetCashFromFinancing": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "DepreciationAndAmortization": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "ShareBasedCompensation": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "CapitalExpenditures": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "DividendsPaid": {{"values": {{"YYYY-MM-DD": number|null}}}},
    "NetChangeInCash": {{"values": {{"YYYY-MM-DD": number|null}}}}
  }},
  "notes": [
    {{"type": "info|warning|error", "message": "string"}}
  ]
}}

RAW DATA TO PROCESS:

INCOME STATEMENT:
{raw_tables.get('income_statement', 'No data available')}

BALANCE SHEET:
{raw_tables.get('balance_sheet', 'No data available')}

CASH FLOW STATEMENT:
{raw_tables.get('cash_flow', 'No data available')}

ADDITIONAL CONTEXT:
{raw_tables.get('context', 'None')}

IMPORTANT: Return ONLY the JSON output. No explanations or additional text.
"""
    return prompt

def build_repair_prompt(original_response, error_message):
    """
    Build a prompt to repair failed JSON responses
    """
    return f"""
REPAIR TASK: The previous JSON response had validation errors. Please fix and return valid JSON.

ERROR DETAILS: {error_message}

PREVIOUS RESPONSE (first 1000 chars):
{original_response[:1000]}

REQUIREMENTS:
1. Fix all JSON syntax errors
2. Ensure all required fields are present
3. Use proper data types (strings, numbers, null, booleans)
4. Follow the exact schema structure
5. Return ONLY corrected JSON, no explanations

KEY SCHEMA REQUIREMENTS:
- "company": object with ticker, name, cik
- "currency": string
- "scale": number (1, 1000, 1000000, or 1000000000)
- "periods": array of period objects
- "income_statement", "balance_sheet", "cash_flow": objects with Series objects
- Each Series has "values" object with date keys and numeric/null values
- "notes": array of note objects

Return the corrected JSON now:
"""

def get_fallback_payload_template(company_info, scale=1000000):
    """
    Template for fallback payload when LLM processing fails
    """
    return {
        "company": {
            "ticker": company_info.get("ticker", "UNKNOWN"),
            "name": None,
            "cik": company_info.get("cik")
        },
        "currency": "USD",
        "scale": scale,
        "periods": [],
        "income_statement": {},
        "balance_sheet": {},
        "cash_flow": {},
        "notes": [
            {
                "type": "error",
                "message": "Automatic cleaning failed. Manual review and processing required."
            },
            {
                "type": "info", 
                "message": "Raw data was successfully extracted but could not be automatically standardized."
            }
        ]
    }

# Common line item variations for fuzzy matching
LINE_ITEM_VARIATIONS = {
    # Income Statement variations
    "revenue": ["net sales", "total revenue", "revenues", "net revenues", "sales", "total net sales"],
    "cost_of_revenue": ["cost of sales", "cost of goods sold", "cost of revenue", "cost of products sold"],
    "gross_profit": ["gross profit", "gross margin", "gross income"],
    "operating_income": ["operating income", "operating profit", "income from operations", "operating earnings"],
    "net_income": ["net income", "net earnings", "profit", "net profit", "earnings"],
    
    # Balance Sheet variations  
    "cash": ["cash and cash equivalents", "cash", "cash and equivalents"],
    "total_assets": ["total assets"],
    "total_liabilities": ["total liabilities"],
    "total_equity": ["total equity", "shareholders' equity", "stockholders' equity"],
    
    # Cash Flow variations
    "operating_cash_flow": ["net cash provided by operating activities", "cash from operations"],
    "investing_cash_flow": ["net cash used in investing activities", "cash from investing"],
    "financing_cash_flow": ["net cash used in financing activities", "cash from financing"]
}