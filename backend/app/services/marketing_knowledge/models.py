"""
Curato AI — Marketing Knowledge Models
Structured schemas for the centralized source of truth for business and brand alignment.
"""

from typing import List, Optional
from pydantic import BaseModel


class CampaignObject(BaseModel):
    campaign_id: str
    name: str
    objective: str
    priority: str  # e.g., "High", "Medium", "Low"
    start_date: str
    end_date: str
    target_personas: List[str]
    content_pillars: List[str]
    success_metrics: List[str]
    active: bool


class BrandKnowledgeObject(BaseModel):
    mission: str
    vision: str
    core_values: List[str]
    positioning: str
    tone: str
    messaging_pillars: List[str]
    competitive_advantages: List[str]
    unique_selling_points: List[str]
    forbidden_messaging: List[str]
    compliance_rules: List[str]
    preferred_ctas: List[str]
    preferred_industries: List[str]


class QuarterlyGoal(BaseModel):
    goal_id: str
    description: str
    target_metric: str
    current_progress: str


class MarketingKnowledge(BaseModel):
    business_domain: str
    quarterly_goals: List[QuarterlyGoal]
    campaigns: List[CampaignObject]
    brand_knowledge: BrandKnowledgeObject
    publishing_guidelines: List[str]
