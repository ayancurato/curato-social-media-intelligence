"""
Curato AI — Google Docs Delivery Service
Creates a beautifully formatted Google Doc containing the approved content.
"""

from typing import Any, Dict, Optional
from app.services.delivery.google_auth import get_docs_service
from app.core.logging import get_logger

logger = get_logger(__name__)

class GoogleDocsDelivery:
    
    @classmethod
    def create_document(cls, title: str, content_blocks: list[dict]) -> Optional[str]:
        """
        Creates a new Google Doc and inserts the content blocks.
        Returns the URL of the created document, or None if it fails.
        """
        service = get_docs_service()
        if not service:
            return None
            
        try:
            # 1. Create blank doc
            doc = service.documents().create(body={"title": title}).execute()
            doc_id = doc.get("documentId")
            if not doc_id:
                return None
                
            # 2. Build insertion requests (reverse order because insertions shift indices)
            requests = []
            current_index = 1
            
            # Simple insertion logic for MVP: just dump text
            text_to_insert = f"Curato AI — {title}\n\n"
            
            for block in content_blocks:
                header = block.get("header", "")
                body = block.get("body", "")
                if header:
                    text_to_insert += f"=== {header} ===\n"
                if body:
                    text_to_insert += f"{body}\n\n"
                    
            requests.append({
                "insertText": {
                    "location": {"index": 1},
                    "text": text_to_insert
                }
            })
            
            # 3. Execute update
            service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": requests}
            ).execute()
            
            url = f"https://docs.google.com/document/d/{doc_id}/edit"
            logger.info("Google Doc created successfully", url=url)
            return url
            
        except Exception as e:
            logger.error("Failed to create Google Doc", error=str(e))
            return None
