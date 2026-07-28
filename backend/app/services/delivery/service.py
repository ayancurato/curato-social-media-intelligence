"""
Curato AI — Delivery Orchestration Service
Extracts the final approved payload and triggers external integrations (Docs + Sheets).
"""

from typing import Any, Dict
from app.services.delivery.google_docs import GoogleDocsDelivery
from app.services.delivery.google_sheets import GoogleSheetsDelivery
from app.core.logging import get_logger
import json

logger = get_logger(__name__)

class DeliveryService:
    
    @classmethod
    def execute_delivery(cls, pipeline_context: Dict[str, Any]) -> None:
        """
        Takes the final pipeline context, generates a Google Doc, 
        and appends the tracking row to Google Sheets.
        """
        # 1. Extract data from the pipeline context
        cmo_decision = pipeline_context.get("cmo_decision", {})
        if not cmo_decision:
            logger.warning("No CMO decision found in pipeline context, skipping delivery.")
            return
            
        final_content = pipeline_context.get("final_content", [])
        if not final_content:
            return
            
        # We assume the first approved draft is the primary one
        draft = final_content[0]
        
        platform = draft.get("platform", "Unknown")
        post_type = draft.get("type", "Static")
        body = draft.get("body", "")
        hook = draft.get("hook", "")
        # For simplicity, combine hook and body as the "caption"
        caption = f"{hook}\n\n{body}"
        
        # Ad copy (if it's a visual post, maybe the agent outputted visual instructions)
        ad_copy = draft.get("visual_instructions", "N/A")
        
        # Extract hashtags from body if present, or from blueprint
        keywords = " ".join([word for word in body.split() if word.startswith("#")])
        if not keywords:
            keywords = "#Marketing #CuratoAI"
            
        # Scheduled Time from Agent 6
        schedule_time = cmo_decision.get("schedule_time", "Immediate")
        
        title = f"Curato Post — {platform} — {schedule_time}"
        
        # 2. Generate Google Doc
        content_blocks = [
            {"header": "Approved By CMO", "body": json.dumps(cmo_decision, indent=2)},
            {"header": "Final Draft", "body": caption},
            {"header": "Visuals", "body": ad_copy},
        ]
        doc_url = GoogleDocsDelivery.create_document(title=title, content_blocks=content_blocks)
        
        if doc_url:
            caption_with_link = f"{caption}\n\nFull Doc: {doc_url}"
        else:
            caption_with_link = caption
            
        # 3. Append to Google Sheets
        row = [
            platform,                # Platform to post
            post_type,               # Type of post
            ad_copy,                 # Ad copy on the creative
            caption_with_link,       # Post caption with the hook (and doc link)
            keywords,                # Keywords or Hashtag
            schedule_time            # Ideal date and time
        ]
        
        success = GoogleSheetsDelivery.append_row(row)
        
        if success:
            logger.info("Delivery pipeline completed successfully.")
        else:
            logger.warning("Delivery pipeline encountered errors appending to sheets.")
