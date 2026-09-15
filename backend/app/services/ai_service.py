"""
AI Service - Google Gemini integration with safe fallback.

Handles AI-powered health screening, concern generation,
risk assessment, and clinical summaries.

IMPORTANT: AI never diagnoses, prescribes, or replaces doctors.
All outputs are labeled as preliminary screening.
"""
import json
import logging
from typing import Dict, Any, Optional, List

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Try to import Google Generative AI SDK
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = bool(settings.GEMINI_API_KEY)
    if GEMINI_AVAILABLE:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI SDK not installed. Using rule-based fallback.")


async def ai_health_screening(
    symptoms: Dict[str, Any],
    patient_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    AI-assisted health preliminary screening.
    
    Returns possible health concerns, urgency level, and recommendations.
    NEVER returns a diagnosis or prescription.
    """
    if GEMINI_AVAILABLE and settings.GEMINI_API_KEY:
        return await _gemini_screening(symptoms, patient_context)
    return _rule_based_screening(symptoms, patient_context)


async def _gemini_screening(
    symptoms: Dict[str, Any],
    patient_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Use Gemini API for health screening."""
    context_str = ""
    if patient_context:
        context_str = f"\nPatient context: Age={patient_context.get('age', 'unknown')}, "
        context_str += f"Existing conditions={patient_context.get('chronic_conditions', 'none')}, "
        context_str += f"Allergies={patient_context.get('allergies', 'none')}, "
        context_str += f"Recent medications={patient_context.get('current_medications', 'none')}"

    prompt = f"""You are a healthcare preliminary screening assistant.
Analyze the following symptom data and provide a preliminary health screening.
You must NEVER diagnose a disease. You must NEVER prescribe medication.

Provide your response as JSON with this exact structure:
{{
    "possible_concerns": [
        {{
            "concern": "brief description of possible concern area",
            "reason": "why this may be relevant based on symptoms",
            "relevance": "high/medium/low"
        }}
    ],
    "urgency_level": "low/moderate/high/emergency",
    "reasons": ["list of reasons for this assessment"],
    "recommended_action": "clear next step recommendation",
    "warning_signs": ["symptoms or conditions that require urgent attention"],
    "care_route_recommendation": "type of facility recommended"
}}

Symptom data:
{json.dumps(symptoms, default=str)}
{context_str}

Remember:
- NEVER say "You have [disease]"
- Use language like "may be associated with", "possible concern", "preliminary screening indicates"
- Always recommend professional medical evaluation
- For emergency level, mention seeking immediate medical attention"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Extract JSON from response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        result = json.loads(text)
        result["ai_service_used"] = "gemini"
        return result
    except Exception as e:
        logger.error(f"Gemini screening failed: {e}")
        result = _rule_based_screening(symptoms, patient_context)
        result["ai_service_used"] = "rule_based_fallback"
        result["fallback_reason"] = f"AI service temporarily unavailable: {str(e)[:100]}"
        return result


def _rule_based_screening(
    symptoms: Dict[str, Any],
    patient_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Rule-based health screening fallback.
    Conservative - tends toward higher urgency when uncertain.
    """
    possible_concerns = []
    reasons = []
    urgency = "low"
    warning_signs = []
    recommended_action = ""
    care_route = ""
    
    symptom_count = sum(1 for k, v in symptoms.items() if v is True and k not in ["medication_taken"])
    
    # Breathing difficulty
    if symptoms.get("breathing_difficulty"):
        urgency = max(urgency, "high", key=["low", "moderate", "high", "emergency"].index)
        possible_concerns.append({
            "concern": "Respiratory symptoms detected",
            "reason": "Breathing difficulty may be associated with respiratory or cardiovascular conditions",
            "relevance": "high",
        })
        reasons.append("Breathing difficulty is a significant symptom that warrants medical evaluation")
        warning_signs.append("If breathing becomes severely difficult, seek emergency care immediately")
        care_route = "hospital"
    
    # Chest discomfort
    if symptoms.get("chest_discomfort"):
        urgency = "emergency" if urgency in ["high", "emergency"] else "high"
        possible_concerns.append({
            "concern": "Chest discomfort detected",
            "reason": "Chest discomfort may be associated with cardiac, respiratory, or musculoskeletal conditions",
            "relevance": "high",
        })
        reasons.append("Chest discomfort requires medical evaluation to rule out serious conditions")
        warning_signs.append("If chest pain is severe or accompanied by arm pain, sweating, or nausea, seek emergency care")
        care_route = "hospital"
    
    # Fever
    if symptoms.get("fever"):
        temp = symptoms.get("fever_temperature", 100)
        if temp and temp >= 103:
            urgency = "high" if urgency in ["low", "moderate"] else urgency
            possible_concerns.append({
                "concern": "High fever detected",
                "reason": f"A temperature of {temp}°F may indicate significant infection or inflammation",
                "relevance": "high",
            })
        else:
            possible_concerns.append({
                "concern": "Fever detected",
                "reason": "Fever may be associated with infection or inflammatory conditions",
                "relevance": "medium",
            })
            if urgency == "low":
                urgency = "moderate"
        reasons.append("Fever is the body's response to infection or illness")
    
    # Pain
    if symptoms.get("pain"):
        severity = symptoms.get("pain_severity", 5) or 5
        if severity >= 8:
            urgency = "high" if urgency in ["low", "moderate"] else urgency
            possible_concerns.append({
                "concern": f"Severe pain ({severity}/10) in {symptoms.get('pain_location', 'unspecified area')}",
                "reason": "Severe pain requires medical evaluation",
                "relevance": "high",
            })
        elif severity >= 5:
            possible_concerns.append({
                "concern": f"Moderate pain ({severity}/10) in {symptoms.get('pain_location', 'unspecified area')}",
                "reason": "Pain may be associated with various conditions that should be evaluated",
                "relevance": "medium",
            })
            if urgency == "low":
                urgency = "moderate"
        reasons.append(f"Pain level {severity}/10 reported in {symptoms.get('pain_location', 'unspecified area')}")
    
    # Dizziness + weakness
    if symptoms.get("dizziness") and symptoms.get("weakness"):
        urgency = "moderate" if urgency == "low" else urgency
        possible_concerns.append({
            "concern": "Dizziness and weakness detected",
            "reason": "These symptoms together may be associated with various conditions including dehydration, anemia, or cardiovascular issues",
            "relevance": "medium",
        })
        warning_signs.append("If dizziness is severe or accompanied by fainting, seek immediate medical attention")
    
    # Headache
    if symptoms.get("headache"):
        possible_concerns.append({
            "concern": "Headache reported",
            "reason": "Headache may be associated with tension, dehydration, infection, or other conditions",
            "relevance": "medium",
        })
    
    # Cough
    if symptoms.get("cough"):
        possible_concerns.append({
            "concern": "Cough reported",
            "reason": "Cough may be associated with respiratory infection, allergy, or other conditions",
            "relevance": "low" if urgency == "low" else "medium",
        })
    
    # Vomiting / diarrhea
    if symptoms.get("vomiting") or symptoms.get("diarrhea"):
        urgency = "moderate" if urgency == "low" else urgency
        possible_concerns.append({
            "concern": "Gastrointestinal symptoms detected",
            "reason": "Vomiting or diarrhea may be associated with infection, food-related illness, or other conditions",
            "relevance": "medium",
        })
        warning_signs.append("Stay hydrated. Seek medical care if symptoms persist or worsen")
    
    # Multiple symptoms
    if symptom_count >= 4:
        urgency = "moderate" if urgency == "low" else urgency
        possible_concerns.append({
            "concern": f"Multiple symptoms reported ({symptom_count} symptoms)",
            "reason": "Multiple simultaneous symptoms warrant thorough medical evaluation",
            "relevance": "medium",
        })
    
    # Default care route
    if not care_route:
        care_level_map = {
            "low": "Self-care monitoring and follow-up as needed",
            "moderate": "Primary Health Centre or local clinic",
            "high": "Community Health Centre or Hospital",
            "emergency": "Emergency Department immediately",
        }
        care_route = care_level_map.get(urgency, "Primary Health Centre")
    
    # Default recommended action
    if not recommended_action:
        action_map = {
            "low": "Monitor your symptoms. If they persist for more than a few days or worsen, consider visiting a healthcare provider.",
            "moderate": "Consider visiting a healthcare provider within the next day or two for evaluation.",
            "high": "Seek medical evaluation soon. Contact a healthcare professional or visit a clinic.",
            "emergency": "Seek urgent medical attention. If symptoms are severe, call emergency services or go to the nearest emergency department.",
        }
        recommended_action = action_map.get(urgency, "Consult a healthcare professional.")
    
    # Add default warning signs
    if not warning_signs:
        warning_signs = [
            "If symptoms suddenly worsen, seek immediate medical attention",
            "If you experience chest pain, severe breathing difficulty, or loss of consciousness, call emergency services",
        ]
    
    return {
        "possible_concerns": possible_concerns,
        "urgency_level": urgency,
        "reasons": reasons,
        "recommended_action": recommended_action,
        "warning_signs": warning_signs,
        "care_route_recommendation": care_route,
        "ai_service_used": "rule_based",
    }


async def ai_doctor_summary(
    patient_data: Dict[str, Any],
    checkin_data: Dict[str, Any],
    history_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generate doctor-ready handover summary."""
    if GEMINI_AVAILABLE and settings.GEMINI_API_KEY:
        try:
            prompt = f"""Generate a concise doctor-ready handover summary from this patient data.
Format as JSON with fields: summary, current_symptoms, relevant_history, medications, alerts, recommended_tests.

Patient: {json.dumps(patient_data, default=str)}
Current check-in: {json.dumps(checkin_data, default=str)}
History: {json.dumps(history_data or [], default=str)}"""
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            result = json.loads(text)
            result["source"] = "AI-generated summary"
            return result
        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
    
    # Fallback: compile basic summary
    summary_parts = []
    if checkin_data.get("symptoms"):
        summary_parts.append(f"Current symptoms: {', '.join(checkin_data['symptoms'])}")
    if patient_data.get("chronic_conditions"):
        summary_parts.append(f"Chronic conditions: {patient_data['chronic_conditions']}")
    if patient_data.get("allergies"):
        summary_parts.append(f"Allergies: {patient_data['allergies']}")
    
    return {
        "summary": "; ".join(summary_parts) if summary_parts else "No significant data available for summary.",
        "current_symptoms": checkin_data.get("symptoms", []),
        "relevant_history": history_data or [],
        "medications": patient_data.get("current_medications", []),
        "alerts": [],
        "recommended_tests": [],
        "source": "System-compiled summary (AI unavailable)",
    }


async def ai_prescription_extract(
    document_text: str,
) -> Dict[str, Any]:
    """Extract prescription information from OCR text."""
    if GEMINI_AVAILABLE and settings.GEMINI_API_KEY:
        try:
            prompt = f"""Extract prescription information from this text.
Return JSON with: medicines (list of {{name, dosage, frequency, duration, instructions}}), 
doctor_name, diagnosis, notes, confidence.

IMPORTANT: If any field is uncertain or not clearly readable, set confidence to low.
Never invent information. If a field cannot be determined, set it to null.

Text:
{document_text}"""
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            result = json.loads(text)
            result["source"] = "AI extraction"
            return result
        except Exception as e:
            logger.error(f"Prescription extraction failed: {e}")
    
    return {
        "medicines": [],
        "doctor_name": None,
        "diagnosis": None,
        "notes": "AI extraction unavailable. Please enter prescription details manually.",
        "confidence": "unavailable",
        "source": "Manual entry required (AI unavailable)",
    }


async def ai_community_insights(
    community_data: List[Dict[str, Any]],
    health_signals: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate community health insights from aggregated data."""
    if GEMINI_AVAILABLE and settings.GEMINI_API_KEY:
        try:
            prompt = f"""Analyze this community health data and provide insights.
Do NOT confirm any outbreaks. Use language like "unusual symptom cluster detected".

Return JSON with: trends, insights, recommendations, priority_areas.

Community data: {json.dumps(community_data[:20], default=str)}
Health signals: {json.dumps(health_signals[:20], default=str)}"""
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text)
        except Exception as e:
            logger.error(f"Community insights failed: {e}")
    
    # Rule-based fallback
    total_signals = sum(s.get("report_count", 1) for s in health_signals)
    signal_types = set(s.get("symptom_category", "") for s in health_signals)
    
    return {
        "trends": [{"type": t, "count": total_signals} for t in signal_types if t],
        "insights": [
            f"Total health signals monitored: {total_signals}",
            f"Symptom categories observed: {len(signal_types)}",
        ],
        "recommendations": [
            "Continue monitoring symptom trends",
            "Ensure healthcare facility accessibility",
        ],
        "priority_areas": [],
        "source": "Rule-based analysis (AI unavailable)",
    }
