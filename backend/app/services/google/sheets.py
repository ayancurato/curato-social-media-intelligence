"""
Curato AI — Google Sheets Service (Interface Only)

Abstract interface for Google Sheets integration.
Implementation will be added when Google APIs are configured.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class GoogleSheetsService:
    """
    Service abstraction for Google Sheets integration.

    All methods raise NotImplementedError — this is intentional.
    Implement when Google service account credentials are configured.
    """

    async def update_row(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        row_data: dict[str, Any],
        row_number: int | None = None,
    ) -> dict[str, Any]:
        """
        Update a specific row in a Google Sheet.

        Returns:
            dict with update confirmation details
        """
        raise NotImplementedError("Google Sheets integration not yet implemented.")

    async def append_row(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        row_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Append a new row to a Google Sheet.

        Returns:
            dict with 'row_number' and 'range'
        """
        raise NotImplementedError("Google Sheets integration not yet implemented.")

    async def read_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        range_: str = "A:Z",
    ) -> list[list[Any]]:
        """
        Read data from a Google Sheet.

        Returns:
            2D list of cell values
        """
        raise NotImplementedError("Google Sheets integration not yet implemented.")
