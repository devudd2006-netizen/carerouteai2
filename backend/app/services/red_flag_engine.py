"""
Red-Flag Safety Engine - Deterministic rule-based emergency detection.

This engine does NOT rely on an LLM. It uses hard-coded medical rules
to detect potentially life-threatening symptom combinations.
If red flags are present, risk is ALWAYS elevated to emergency level,
regardless of what the AI screening says.

DISCLAIMER: This is for educational/prototype purposes only.
It does NOT constitute medical advice or diagnosis.
"""
from typing import List, Dict, Any, Tuple

# Configurable red-flag rules
RED_FLAG_RULES: Dict[str, Dict[str, Any]] = {
    "severe_breathing_difficulty": {
        "description": "Severe breathing difficulty detected",
        "guidance": "Seek immediate emergency medical attention. Difficulty breathing can be a sign of a serious medical condition.",
        "check": lambda s: s.get("breathing_difficulty", False) and (s.get("severity") or 0) >= 4,
    },
    "severe_chest_pain": {
        "description": "Chest discomfort/pain detected",
        "guidance": "Chest discomfort can indicate a serious cardiac or respiratory condition. Seek emergency medical evaluation immediately.",
        "check": lambda s: s.get("chest_discomfort", False),
    },
    "high_fever_breathing": {
        "description": "High fever combined with breathing difficulty",
        "guidance": "A high fever combined with breathing difficulty may indicate a serious infection. Emergency medical evaluation is recommended.",
        "check": lambda s: s.get("fever", False) and (s.get("fever_temperature", 0) or 0) >= 103 and s.get("breathing_difficulty", False),
    },
    "loss_of_consciousness_symptoms": {
        "description": "Severe dizziness with weakness (possible loss of consciousness risk)",
        "guidance": "Severe dizziness combined with weakness may indicate a serious condition. Sit down, stay safe, and seek medical attention promptly.",
        "check": lambda s: s.get("dizziness", False) and s.get("weakness", False) and (s.get("severity") or 0) >= 4,
    },
    "severe_vomiting": {
        "description": "Persistent vomiting with other symptoms",
        "guidance": "Persistent vomiting, especially with other symptoms, requires medical evaluation to prevent dehydration and identify underlying causes.",
        "check": lambda s: s.get("vomiting", False) and (s.get("diarrhea", False) or s.get("fever", False) or (s.get("severity") or 0) >= 4),
    },
    "severe_pain": {
        "description": "Severe pain detected",
        "guidance": "Severe pain (level 8+) should be evaluated by a healthcare professional. If the pain is sudden and intense, seek emergency care.",
        "check": lambda s: s.get("pain", False) and (s.get("pain_severity", 0) or 0) >= 8,
    },
    "chest_pain_with_breathing": {
        "description": "Chest pain with breathing difficulty",
        "guidance": "Chest pain combined with breathing difficulty is a potentially serious combination. Seek emergency medical evaluation immediately.",
        "check": lambda s: s.get("chest_discomfort", False) and s.get("breathing_difficulty", False),
    },
    "multiple_severe_symptoms": {
        "description": "Multiple severe symptoms present simultaneously",
        "guidance": "Multiple severe symptoms occurring together warrant urgent medical evaluation.",
        # Require 4+ symptoms AND at least 2 from a clinically serious set, so a
        # common cold-like combination (e.g. mild fever + cough + headache) does
        # not falsely escalate to EMERGENCY.
        "check": lambda s: (
            sum(1 for k, v in s.items() if v is True and k != "medication_taken") >= 4
            and (
                sum(1 for k in ["breathing_difficulty", "chest_discomfort", "vomiting", "diarrhea", "dizziness"] if s.get(k, False))
                + (1 if (s.get("fever") and (s.get("fever_temperature") or 0) >= 102) else 0)
                + (1 if (s.get("pain") and (s.get("pain_severity") or 0) >= 7) else 0)
            ) >= 2
        ),
    },
    "fever_with_neuro_symptoms": {
        "description": "Fever with neurological symptoms",
        "guidance": "Fever combined with dizziness or severe headache may indicate a serious infection. Medical evaluation is recommended promptly.",
        # Fever with dizziness + weakness (possible serious infection/dehydration)
        # or fever with a severe headache (severity explicitly reported).
        # Default severity is 0 (unknown) so missing data never inflates risk.
        "check": lambda s: s.get("fever", False) and (
            (s.get("dizziness", False) and s.get("weakness", False))
            or (s.get("headache", False) and (s.get("severity") or 0) >= 4)
        ),
    },
}


def evaluate_red_flags(symptoms: Dict[str, Any]) -> Tuple[bool, List[Dict[str, str]], str]:
    """
    Evaluate symptoms against red-flag rules.
    
    Args:
        symptoms: Dictionary of symptom data with severity levels
        
    Returns:
        Tuple of (is_emergency, flagged_rules, overall_guidance)
    """
    flagged_rules = []
    
    for rule_name, rule in RED_FLAG_RULES.items():
        try:
            if rule["check"](symptoms):
                flagged_rules.append({
                    "rule": rule_name,
                    "description": rule["description"],
                    "guidance": rule["guidance"],
                })
        except (KeyError, TypeError, ValueError):
            continue
    
    is_emergency = len(flagged_rules) > 0
    
    # Compile overall guidance
    if is_emergency:
        guidance_parts = [
            "POTENTIAL EMERGENCY DETECTED.",
            "",
            "The following potentially serious symptoms have been identified:",
        ]
        for fr in flagged_rules:
            guidance_parts.append(f"• {fr['description']}")
        guidance_parts.append("")
        guidance_parts.append("Seek urgent medical attention. If you are experiencing a medical emergency, please call your local emergency number immediately.")
        guidance_parts.append("")
        guidance_parts.append("⚠️ This system provides preliminary screening only and does NOT replace professional medical evaluation.")
        overall_guidance = "\n".join(guidance_parts)
    else:
        overall_guidance = ""
    
    return is_emergency, flagged_rules, overall_guidance


# Symptom keywords that should always trigger at least HIGH urgency
HIGH_URGENCY_KEYWORDS = {
    "severe chest pain", "can't breathe", "unconscious", "seizure",
    "stroke symptoms", "heavy bleeding", "anaphylaxis", "overdose",
    "heart attack symptoms", "sudden severe headache",
}
