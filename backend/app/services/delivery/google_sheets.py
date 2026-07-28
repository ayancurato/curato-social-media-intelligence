"""
Curato AI — Google Sheets Delivery Service
Appends a fully structured row to the tracking spreadsheet.
"""

from typing import Any, Dict, List, Optional
from app.services.delivery.google_auth import get_sheets_service
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class GoogleSheetsDelivery:
    
    @classmethod
    def append_row(cls, row_data: List[str]) -> bool:
        """
        Appends a row of data to the configured Google Sheet.
        Expects a list matching the exact columns in the tracker.
        """
        service = get_sheets_service()
        settings = get_settings()
        sheet_id = settings.google_sheets_id
        
        if not service or not sheet_id:
            logger.warning("Google Sheets service or ID not configured, skipping append.")
            return False
            
        try:
            # We assume appending to the first sheet (Sheet1)
            range_name = "Sheet1"
            body = {
                "values": [row_data]
            }
            
            result = service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            
            logger.info("Successfully appended row to Google Sheet", updates=result.get('updates'))
            return True
            
        except Exception as e:
            logger.error("Failed to append row to Google Sheet", error=str(e))
            return False
