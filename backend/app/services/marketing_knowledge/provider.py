"""
Curato AI — Marketing Knowledge Provider
Abstract interface and JSON implementation for the centralized source of marketing truth.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Optional

from app.services.marketing_knowledge.models import MarketingKnowledge


class MarketingKnowledgeProvider(ABC):
    """
    Abstract interface for retrieving marketing knowledge.
    """
    @abstractmethod
    async def get_knowledge(self) -> MarketingKnowledge:
        pass


class LocalJSONMarketingProvider(MarketingKnowledgeProvider):
    """
    Implementation that reads marketing knowledge from a local JSON file.
    Can be replaced later by a CMSProvider or NotionProvider.
    """
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(os.path.dirname(__file__), "default_data.json")

    async def get_knowledge(self) -> MarketingKnowledge:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return MarketingKnowledge(**data)


# Global instance
marketing_provider = LocalJSONMarketingProvider()
