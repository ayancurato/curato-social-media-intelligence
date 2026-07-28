"""
Curato AI — Google Workspace Auth
Handles Service Account authentication for Google APIs.
"""

from typing import Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build, Resource

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_google_credentials() -> Optional[Credentials]:
    """Load the Google Service Account credentials."""
    settings = get_settings()
    key_path = settings.google_service_account_key_path
    
    if not key_path:
        logger.warning("GOOGLE_SERVICE_ACCOUNT_KEY_PATH is not set.")
        return None
        
    try:
        return Credentials.from_service_account_file(key_path, scopes=SCOPES)
    except Exception as e:
        logger.error("Failed to load Google credentials", error=str(e), path=key_path)
        return None

def get_docs_service() -> Optional[Resource]:
    creds = get_google_credentials()
    if not creds:
        return None
    return build('docs', 'v1', credentials=creds, cache_discovery=False)

def get_sheets_service() -> Optional[Resource]:
    creds = get_google_credentials()
    if not creds:
        return None
    return build('sheets', 'v4', credentials=creds, cache_discovery=False)
