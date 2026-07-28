"""
Curato AI — Priority Engine
"""

from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class PriorityEngine:
    """
    Deterministically computes the final Priority Score based on configured weights.
    Provides explainable scoring.
    """
    def __init__(self, profile_weights: dict[str, float]):
        self.weights = profile_weights
        
    def calculate_priority(self, topic: dict[str, Any], evaluations: dict[str, Any]) -> dict[str, Any]:
        """
        Takes raw topic data and the gathered evaluations, and calculates explainable priority.
        """
        title = topic.get("title", "")
        
        # Extract base scores
        freshness = topic.get("freshness_score", 0)
        confidence = topic.get("confidence_score", 0)
        virality = topic.get("virality_score", 0)
        
        # Extract evaluation scores
        opp_eval = evaluations.get("opportunity", {}).get(title, {})
        biz_eval = evaluations.get("business_alignment", {}).get(title, {})
        aud_eval = evaluations.get("audience_intent", {}).get(title, {})
        conf_eval = evaluations.get("conflict_resolver", {}).get(title, {})
        strat_eval = evaluations.get("content_strategy", {}).get(title, {})
        
        opportunity = opp_eval.get("raw_score", topic.get("opportunity_score", 0))
        biz_alignment = biz_eval.get("raw_score", 0)
        aud_intent = aud_eval.get("intent_score", 0)
        strategic_val = conf_eval.get("strategic_value_score", 0)
        
        # Weight calculations
        w_opp = self.weights.get("opportunity", 0)
        w_biz = self.weights.get("business_alignment", 0)
        w_aud = self.weights.get("audience_intent", 0)
        w_strat = self.weights.get("strategic_value", 0)
        w_viral = self.weights.get("virality", 0)
        w_fresh = self.weights.get("freshness", 0)
        w_conf = self.weights.get("confidence", 0)
        
        # Contributions
        c_opp = opportunity * w_opp
        c_biz = biz_alignment * w_biz
        c_aud = aud_intent * w_aud
        c_strat = strategic_val * w_strat
        c_viral = virality * w_viral
        c_fresh = freshness * w_fresh
        c_conf = confidence * w_conf
        
        final_score = int(c_opp + c_biz + c_aud + c_strat + c_viral + c_fresh + c_conf)
        
        # Explainable structure
        return {
            "topic": title,
            "priority_score": min(100, max(0, final_score)),
            "opportunity_score": {
                "raw_score": opportunity,
                "weight": w_opp,
                "contribution": c_opp,
                "reasoning": opp_eval.get("reasoning", "")
            },
            "business_alignment": {
                "raw_score": biz_alignment,
                "weight": w_biz,
                "contribution": c_biz,
                "reasoning": biz_eval.get("reasoning", "")
            },
            "audience_intent": {
                "raw_score": aud_intent,
                "weight": w_aud,
                "contribution": c_aud,
                "reasoning": aud_eval.get("reasoning", "")
            },
            "strategic_value": {
                "raw_score": strategic_val,
                "weight": w_strat,
                "contribution": c_strat,
                "reasoning": conf_eval.get("reasoning", ""),
                "conflict_detected": conf_eval.get("conflict_detected", False)
            },
            "virality": {
                "raw_score": virality,
                "weight": w_viral,
                "contribution": c_viral
            },
            "freshness": {
                "raw_score": freshness,
                "weight": w_fresh,
                "contribution": c_fresh
            },
            "confidence": {
                "raw_score": confidence,
                "weight": w_conf,
                "contribution": c_conf
            },
            # Metadata fields needed downstream
            "audience": aud_eval.get("audience", ""),
            "buyer_stage": aud_eval.get("buyer_stage", ""),
            "intent": aud_eval.get("intent", ""),
            "recommended_platforms": strat_eval.get("recommended_platforms", []),
            "recommended_content_format": strat_eval.get("recommended_content_format", ""),
            "marketing_objective": strat_eval.get("marketing_objective", ""),
            "why_now": strat_eval.get("why_now", ""),
            "reasoning": "Determined by priority engine based on strategic weights.",
            "confidence_score": confidence,
            "keywords": topic.get("keywords", []),
            "hashtags": topic.get("hashtags", []),
        }
