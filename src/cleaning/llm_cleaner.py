import os
import json
import logging
import google.generativeai as genai
from pydantic import ValidationError
from typing import Dict, Any, Optional
from .canonical_schema import Payload
from .prompts import BASE_RULES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _df_to_tsv(df, max_rows=120, max_cols=12):
    """Convert DataFrame to TSV string with size limits."""
    if df is None or df.empty:
        return ""
    
    df_clean = df.copy()
    
    # Handle size limits
    if len(df_clean) > max_rows:
        df_clean = df_clean.iloc[:max_rows]
        logger.info(f"Truncated DataFrame to {max_rows} rows")
    
    if len(df_clean.columns) > max_cols:
        df_clean = df_clean.iloc[:, :max_cols]
        logger.info(f"Truncated DataFrame to {max_cols} columns")
    
    # Clean up column names and data
    df_clean.columns = [str(col).strip() for col in df_clean.columns]
    
    return df_clean.to_csv(index=False, sep="\t", na_rep="")

def _detect_units_hint(*texts) -> str:
    """Detect unit scale from text content."""
    joined = " ".join([str(t).lower() for t in texts if t])
    
    # Check for different unit indicators
    if any(phrase in joined for phrase in ["in billions", "billions of dollars", "(in billions)"]):
        return "(in billions)"
    elif any(phrase in joined for phrase in ["in millions", "millions of dollars", "(in millions)"]):
        return "(in millions)"
    elif any(phrase in joined for phrase in ["in thousands", "thousands of dollars", "(in thousands)"]):
        return "(in thousands)"
    
    return ""

def _schema_hint_text():
    """Provide schema structure hint for the LLM."""
    return """
    Required JSON structure:
    {
        "company": {"cik": "...", "name": "...", "ticker": "..."},
        "currency": "USD",
        "scale": 1000000,
        "periods": [{"label": "...", "end_date": "YYYY-MM-DD", "fp": "FY|Q1|Q2|Q3|Q4", ...}],
        "income_statement": {"Revenue": {"values": {"2023-12-31": 123.45}}, ...},
        "balance_sheet": {...},
        "cash_flow": {...},
        "notes": []
    }
    """

def init_gemini(model="gemini-1.5-flash") -> Optional[genai.GenerativeModel]:
    """Initialize Gemini model with proper error handling."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not set")
            raise RuntimeError("GEMINI_API_KEY not found. Please set it in your environment.")
        
        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel(model)
        logger.info(f"Successfully initialized {model}")
        return model_instance
        
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        raise

def _build_cleaning_prompt(company: Dict[str, Any], raw_tables: Dict[str, str], units_hint: str) -> Dict[str, Any]:
    """Build the prompt for LLM cleaning."""
    return {
        "system": "You are a financial data cleaner for SEC filings. Convert raw financial tables into clean, structured JSON.",
        "rules": BASE_RULES,
        "task": "Clean the provided financial data and return ONLY valid JSON matching the schema.",
        "input": {
            "company": company,
            "raw_tables": raw_tables,
            "units_detected": units_hint,
            "schema_structure": _schema_hint_text()
        },
        "instructions": [
            "Parse all numeric values carefully (handle parentheses as negative, dashes as null)",
            "Map company-specific line items to canonical schema keys",
            "Detect and apply consistent scaling (1, 1000, 1000000, or 1000000000)",
            "Infer period information (fiscal year, quarter, dates)",
            "Return ONLY the JSON object, no additional text"
        ]
    }

def clean_with_gemini(
    model: genai.GenerativeModel,
    company: Dict[str, Any],
    is_df,
    bs_df, 
    cf_df,
    extra_context: str = ""
) -> Payload:
    """Clean financial data using Gemini LLM."""
    
    logger.info(f"Starting cleaning process for {company.get('ticker', 'Unknown')}")
    
    try:
        # Convert DataFrames to TSV
        is_tsv = _df_to_tsv(is_df)
        bs_tsv = _df_to_tsv(bs_df)
        cf_tsv = _df_to_tsv(cf_df)
        
        # Detect units
        units_hint = _detect_units_hint(is_tsv, bs_tsv, cf_tsv, extra_context)
        logger.info(f"Detected units: {units_hint}")
        
        raw_tables = {
            "income_statement": is_tsv,
            "balance_sheet": bs_tsv,
            "cash_flow": cf_tsv,
            "context": f"{units_hint}\n{extra_context}".strip()
        }
        
        # Build prompt
        prompt_data = _build_cleaning_prompt(company, raw_tables, units_hint)
        
        # Generate content
        logger.info("Sending request to Gemini...")
        response = model.generate_content(
            [json.dumps(prompt_data, indent=2)],
            generation_config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
                "max_output_tokens": 8192
            },
        )
        
        response_text = response.text.strip()
        logger.info(f"Received response of length: {len(response_text)}")
        
        # Parse and validate
        try:
            data = json.loads(response_text)
            payload = Payload(**data)
            logger.info("Successfully validated payload")
            return payload
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"First attempt failed: {e}")
            return _repair_json_response(model, prompt_data, response_text, str(e))
            
    except Exception as e:
        logger.error(f"Error in clean_with_gemini: {e}")
        raise

def _repair_json_response(
    model: genai.GenerativeModel,
    original_prompt: Dict[str, Any],
    failed_response: str,
    error_message: str
) -> Payload:
    """Attempt to repair malformed JSON response."""
    
    logger.info("Attempting to repair JSON response...")
    
    repair_prompt = {
        "system": "You are fixing a malformed JSON response for financial data cleaning.",
        "original_request": original_prompt,
        "failed_output": failed_response[:5000],  # Limit size
        "error": error_message,
        "task": "Return corrected JSON that validates against the schema. No explanations."
    }
    
    try:
        repair_response = model.generate_content(
            [json.dumps(repair_prompt, indent=2)],
            generation_config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
                "max_output_tokens": 8192
            },
        )
        
        repaired_data = json.loads(repair_response.text.strip())
        payload = Payload(**repaired_data)
        logger.info("Successfully repaired and validated payload")
        return payload
        
    except Exception as e:
        logger.error(f"Repair attempt failed: {e}")
        raise RuntimeError(f"Failed to clean data after repair attempt: {e}")

def validate_data_quality(payload: Payload) -> Dict[str, Any]:
    """Validate the quality of cleaned data."""
    
    quality_report = {
        "warnings": [],
        "stats": {
            "periods_count": len(payload.periods),
            "income_statement_items": len(payload.income_statement),
            "balance_sheet_items": len(payload.balance_sheet),
            "cash_flow_items": len(payload.cash_flow)
        }
    }
    
    # Check for empty sections
    if not payload.income_statement:
        quality_report["warnings"].append("Income statement is empty")
    if not payload.balance_sheet:
        quality_report["warnings"].append("Balance sheet is empty")
    if not payload.cash_flow:
        quality_report["warnings"].append("Cash flow is empty")
    
    # Check for reasonable scale
    if payload.scale not in [1, 1_000, 1_000_000, 1_000_000_000]:
        quality_report["warnings"].append(f"Unusual scale detected: {payload.scale}")
    
    return quality_report