# config/logging_config.py - Step by Step Explanation

import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Dict, Any

from .settings import get_config

# =============================================================================
# WHAT LOGGING LEVELS MEAN
# =============================================================================
"""
DEBUG    (10): Detailed info for diagnosing problems
INFO     (20): General information about program execution  
WARNING  (30): Something unexpected happened, but app still works
ERROR    (40): Serious problem occurred, function failed
CRITICAL (50): Very serious problem, program might crash

Example usage:
logger.debug("Processing company data...")     # Development details
logger.info("Analysis completed successfully") # Important milestones  
logger.warning("Using cached data, might be stale") # Potential issues
logger.error("Failed to fetch data from API")  # Problems that need attention
logger.critical("Database connection lost")    # Severe issues
"""

def setup_logging() -> Dict[str, Any]:
    """Set up logging configuration based on app settings."""
    
    # Get application configuration (from environment variables)
    config = get_config()
    
    # =============================================================================
    # 1. CREATE LOGS DIRECTORY
    # =============================================================================
    logs_dir = config.project_root / "logs"
    logs_dir.mkdir(exist_ok=True)  # Create if doesn't exist
    
    # =============================================================================
    # 2. SET LOGGING LEVEL FROM CONFIGURATION
    # =============================================================================
    # Convert string like "INFO" to logging constant like logging.INFO
    log_level = getattr(logging, config.log_level)
    
    # =============================================================================
    # 3. CREATE FORMATTERS (How log messages look)
    # =============================================================================
    
    # Detailed formatter for files (includes everything)
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    # Example output:
    # 2024-01-15 10:30:45,123 - src.services.gemini_client - ERROR - gemini_client.py:45 - API key not found
    
    # Simple formatter for console (easier to read during development)
    simple_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    # Example output:
    # 2024-01-15 10:30:45,123 - ERROR - API key not found
    
    # =============================================================================
    # 4. CONFIGURE ROOT LOGGER (Controls all logging in the app)
    # =============================================================================
    root_logger = logging.getLogger()  # Get the root logger
    root_logger.setLevel(log_level)    # Set minimum level to log
    root_logger.handlers.clear()       # Remove any existing handlers
    
    # =============================================================================
    # 5. CONSOLE HANDLER (Logs to terminal/console)
    # =============================================================================
    console_handler = logging.StreamHandler(sys.stdout)  # Output to console
    console_handler.setLevel(log_level)                  # Same level as root
    console_handler.setFormatter(simple_formatter)       # Use simple format
    root_logger.addHandler(console_handler)
    
    # WHY THIS MATTERS:
    # - See logs immediately while developing
    # - Debug issues in real-time
    # - Clean, readable format for development
    
    # =============================================================================
    # 6. ROTATING FILE HANDLER (Logs to files with size management)
    # =============================================================================
    file_handler = RotatingFileHandler(
        logs_dir / "app.log",           # File path
        maxBytes=10 * 1024 * 1024,      # 10MB max file size
        backupCount=5                   # Keep 5 old files (app.log.1, app.log.2, etc.)
    )
    file_handler.setLevel(log_level)    # Same level as root
    file_handler.setFormatter(detailed_formatter)  # Use detailed format
    root_logger.addHandler(file_handler)
    
    # WHY ROTATING FILES:
    # - Prevents log files from growing infinitely
    # - Keeps last 50MB of logs (5 files × 10MB each)
    # - Automatically manages old log cleanup
    # - app.log (current) → app.log.1 (previous) → app.log.2 (older) etc.
    
    # =============================================================================  
    # 7. ERROR-ONLY FILE HANDLER (Separate file for just errors)
    # =============================================================================
    error_handler = RotatingFileHandler(
        logs_dir / "error.log",         # Separate error file
        maxBytes=10 * 1024 * 1024,      # 10MB max
        backupCount=5                   # Keep 5 old error files
    )
    error_handler.setLevel(logging.ERROR)  # Only ERROR and CRITICAL messages
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # WHY SEPARATE ERROR FILE:
    # - Quickly find problems without searching through all logs
    # - Monitor error trends over time
    # - Alert systems can watch error.log specifically
    
    # =============================================================================
    # 8. CONFIGURE THIRD-PARTY LIBRARY LOGGERS (Reduce noise)
    # =============================================================================
    loggers_config = {
        "streamlit": {"level": logging.WARNING},    # Streamlit is chatty, reduce noise
        "urllib3": {"level": logging.WARNING},      # HTTP library noise reduction
        "requests": {"level": logging.WARNING},     # HTTP requests noise reduction
        "selenium": {"level": logging.WARNING},     # Web scraping noise reduction
        "matplotlib": {"level": logging.WARNING},   # Plotting library noise reduction
        "plotly": {"level": logging.WARNING},       # Plotly noise reduction
    }
    
    for logger_name, logger_config in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_config.get("level", log_level))
    
    # WHY CONFIGURE THIRD-PARTY LOGGERS:
    # - These libraries can be very verbose with DEBUG/INFO messages
    # - Focus on YOUR application's logs, not library internals
    # - Still see their WARNING/ERROR messages (important issues)
    
    # =============================================================================
    # 9. LOG THE SUCCESSFUL SETUP
    # =============================================================================
    logging.info(f"Logging configured with level: {config.log_level}")
    
    # =============================================================================
    # 10. RETURN CONFIGURATION INFO (for diagnostics)
    # =============================================================================
    return {
        "level": log_level,
        "handlers": len(root_logger.handlers),
        "log_dir": str(logs_dir)
    }

# =============================================================================
# HOW TO USE LOGGING IN YOUR CODE
# =============================================================================

"""
# In any Python file in your project:

import logging

# Get a logger for this module
logger = logging.getLogger(__name__)  # __name__ = "src.services.gemini_client"

# Use different levels appropriately:
logger.debug("Starting to process financial data")       # Development info
logger.info("Successfully fetched data for AAPL")        # Important events
logger.warning("API rate limit approaching")             # Potential issues
logger.error("Failed to parse financial statement")      # Problems
logger.critical("Database connection completely failed") # Severe issues

# Log with context:
logger.info(f"Analyzing company: {company_name}")
logger.error(f"API error: {error_message}", exc_info=True)  # Include stack trace
"""

# =============================================================================
# WHAT GETS CREATED
# =============================================================================

"""
After running setup_logging(), you get:

logs/
├── app.log        # All logs (DEBUG, INFO, WARNING, ERROR, CRITICAL)
├── app.log.1      # Previous app.log (when it rotated)
├── app.log.2      # Older app.log
├── error.log      # Only ERROR and CRITICAL messages
├── error.log.1    # Previous error.log
└── error.log.2    # Older error.log

CONSOLE OUTPUT (during development):
2024-01-15 10:30:45,123 - INFO - Starting analysis for AAPL
2024-01-15 10:30:47,456 - ERROR - Failed to fetch SEC data

FILE CONTENT (logs/app.log):
2024-01-15 10:30:45,123 - src.main - INFO - main.py:67 - Starting analysis for AAPL
2024-01-15 10:30:47,456 - src.services.sec_edgar - ERROR - sec_edgar.py:123 - Failed to fetch SEC data: Connection timeout
"""

# =============================================================================
# CONFIGURATION EXAMPLES
# =============================================================================

"""
# In .env file, you can control logging:

# Development (see everything):
LOG_LEVEL=DEBUG

# Production (only important stuff):  
LOG_LEVEL=INFO

# Troubleshooting (only problems):
LOG_LEVEL=WARNING

# Crisis mode (only serious issues):
LOG_LEVEL=ERROR
"""