"""
Curato AI — Google Docs Service (Interface Only)

Abstract interface for Google Docs integration.
Implementation will be added when Google APIs are configured.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class GoogleDocsService:
    """
    Service abstraction for Google Docs integration.

    All methods raise NotImplementedError — this is intentional.
    Implement when Google service account credentials are configured.
    """

    async def create_document(
        self,
        title: str,
        content: str,
        folder_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new Google Doc with the given content.

        Returns:
            dict with 'document_id' and 'url'
        """
        # TODO: Implement with Google Docs API
        # from google.oauth2 import service_account
        # from googleapiclient.discovery import build
        raise NotImplementedError(
            "Google Docs integration not yet implemented. "
            "Configure GOOGLE_SERVICE_ACCOUNT_KEY_PATH in .env."
        )

    async def export_content(
        self,
        content: list[dict[str, Any]],
        template_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Export content drafts to a Google Doc.

        Args:
            content: List of content draft objects.
            template_id: Optional Google Doc template to use.

        Returns:
            dict with 'document_id', 'url', and 'title'
        """
        raise NotImplementedError("Google Docs integration not yet implemented.")

    async def update_document(
        self,
        document_id: str,
        content: str,
    ) -> dict[str, Any]:
        """Update an existing Google Doc."""
        raise NotImplementedError("Google Docs integration not yet implemented.")
