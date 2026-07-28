"""
Curato AI — Blueprint Assembler (Deterministic)
"""

from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class BlueprintAssembler:
    """
    Deterministically validates, normalizes, and assembles the outputs 
    from all reasoning workers into the final JSON schema for the Content Blueprint.
    Replaces the need for a final 'Blueprint Builder LLM'.
    """

    def assemble(self, 
                 topic: dict[str, Any], 
                 angle_eval: dict[str, Any], 
                 msg_eval: dict[str, Any], 
                 brand_eval: dict[str, Any],
                 hook_eval: dict[str, Any],
                 cta_eval: dict[str, Any]) -> dict[str, Any]:
        """Assembles the final blueprint."""
        
        # Ensure we always have arrays even if LLM missed them or returned None
        secondary_angles = angle_eval.get("secondary_angles") or []
        if not isinstance(secondary_angles, list):
            secondary_angles = [secondary_angles]
            
        supporting_points = msg_eval.get("supporting_points") or []
        if not isinstance(supporting_points, list):
            supporting_points = [supporting_points]
            
        proof_points = msg_eval.get("proof_points") or []
        if not isinstance(proof_points, list):
            proof_points = [proof_points]
            
        alt_hooks = hook_eval.get("alternative_hooks") or []
        if not isinstance(alt_hooks, list):
            alt_hooks = [alt_hooks]
            
        platforms = topic.get("recommended_platforms") or ["linkedin"]
        # Normalize platforms to string for standard platform field, keep array if needed
        primary_platform = platforms[0] if platforms else "linkedin"

        return {
            "topic": topic.get("topic", ""),
            "primary_angle": angle_eval.get("primary_angle", ""),
            "secondary_angles": secondary_angles,
            "target_audience": topic.get("audience", ""),
            "buyer_stage": topic.get("buyer_stage", ""),
            "communication_goal": msg_eval.get("communication_goal", ""),
            "key_message": msg_eval.get("key_message", ""),
            "supporting_points": supporting_points,
            "proof_points": proof_points,
            "storytelling_framework": msg_eval.get("storytelling_framework", ""),
            "recommended_hook": hook_eval.get("recommended_hook", ""),
            "alternative_hooks": alt_hooks,
            "tone": brand_eval.get("tone", ""),
            "brand_voice": brand_eval.get("brand_voice", ""),
            "cta": cta_eval.get("cta", ""),
            "platform": primary_platform,
            "content_format": topic.get("recommended_content_format", ""),
            "reasoning": f"Strategy formed dynamically based on '{angle_eval.get('primary_angle', 'topic')}'."
        }
