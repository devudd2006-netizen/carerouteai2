"""
CareRoute AI - Backend test suite.

Covers the deterministic safety-critical logic:
- Red-flag emergency engine (false-positive and true-positive cases)
- Rule-based screening fallback
- Care route engine (urgency -> appropriate care level, facility ranking)
- Community Care Priority Score calculation
- API smoke tests: auth, check-in -> screening, red-flag escalation
"""
import os
import sys
import tempfile

# Use a throwaway SQLite database for API tests (must be set before app import).
_tmpdir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmpdir, 'test.db')}"
os.environ["DEBUG"] = "false"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.db.database import init_db  # noqa: E402
from app.services.red_flag_engine import evaluate_red_flags  # noqa: E402
from app.services.ai_service import _rule_based_screening  # noqa: E402
from app.services.care_route_service import (
    determine_care_level,  # noqa: E402
    rank_facilities,  # noqa: E402
    haversine_distance,  # noqa: E402
)
from app.services.community_service import calculate_priority_score  # noqa: E402


# ---------------------------------------------------------------------------
# Red-flag safety engine
# ---------------------------------------------------------------------------

class TestRedFlagEngine:
    def test_routine_symptoms_not_emergency(self):
        """Fever + cough + headache + weakness must NOT escalate to emergency."""
        symptoms = {
            "fever": True, "fever_temperature": 101.5, "cough": True,
            "headache": True, "weakness": True,
        }
        is_emergency, flags, _ = evaluate_red_flags(symptoms)
        assert is_emergency is False
        assert flags == []

    def test_mild_checkin_not_emergency(self):
        symptoms = {"headache": True, "feeling_today": "okay"}
        is_emergency, _, _ = evaluate_red_flags(symptoms)
        assert is_emergency is False

    def test_chest_pain_with_breathing_difficulty_is_emergency(self):
        symptoms = {
            "chest_discomfort": True, "breathing_difficulty": True,
            "dizziness": True, "weakness": True, "pain": True, "pain_severity": 9,
        }
        is_emergency, flags, guidance = evaluate_red_flags(symptoms)
        assert is_emergency is True
        assert len(flags) >= 2
        rules = {f["rule"] for f in flags}
        assert "chest_pain_with_breathing" in rules
        assert "EMERGENCY" in guidance.upper()

    def test_high_fever_with_breathing_difficulty(self):
        symptoms = {"fever": True, "fever_temperature": 104, "breathing_difficulty": True}
        is_emergency, flags, _ = evaluate_red_flags(symptoms)
        assert is_emergency is True
        assert any(f["rule"] == "high_fever_breathing" for f in flags)

    def test_unknown_severity_defaults_to_safe(self):
        """Missing severity data must never inflate risk."""
        symptoms = {"fever": True, "headache": True, "dizziness": True}
        is_emergency, _, _ = evaluate_red_flags(symptoms)
        assert is_emergency is False

    def test_severe_pain_alone(self):
        symptoms = {"pain": True, "pain_severity": 9}
        is_emergency, flags, _ = evaluate_red_flags(symptoms)
        assert is_emergency is True
        assert any(f["rule"] == "severe_pain" for f in flags)


# ---------------------------------------------------------------------------
# Rule-based screening fallback
# ---------------------------------------------------------------------------

class TestRuleBasedScreening:
    def test_mild_symptoms_low_urgency(self):
        result = _rule_based_screening({"headache": True})
        assert result["urgency_level"] == "low"
        assert result["possible_concerns"]
        assert "diagnos" not in result["recommended_action"].lower()

    def test_fever_moderate(self):
        result = _rule_based_screening({"fever": True, "fever_temperature": 101})
        assert result["urgency_level"] == "moderate"

    def test_breathing_difficulty_high(self):
        result = _rule_based_screening({"breathing_difficulty": True})
        assert result["urgency_level"] == "high"

    def test_no_diagnosis_language(self):
        """Screening text must never assert a disease."""
        result = _rule_based_screening({
            "fever": True, "cough": True, "breathing_difficulty": True,
            "chest_discomfort": True,
        })
        all_text = " ".join(
            c.get("concern", "") + c.get("reason", "")
            for c in result["possible_concerns"]
        ).lower()
        for phrase in ["you have pneumonia", "you have", "diagnosis:"]:
            assert phrase not in all_text


# ---------------------------------------------------------------------------
# Care route engine
# ---------------------------------------------------------------------------

class TestCareRouteEngine:
    def test_emergency_maps_to_emergency_dept(self):
        assert determine_care_level("emergency", {}) == "emergency"

    def test_high_maps_to_hospital(self):
        assert determine_care_level("high", {}) == "hospital"

    def test_moderate_maps_to_chc(self):
        assert determine_care_level("moderate", {}) == "chc"

    def test_moderate_with_red_flags_escalates_to_hospital(self):
        symptoms = {"chest_discomfort": True}
        assert determine_care_level("moderate", symptoms) == "hospital"

    def test_low_mild_maps_to_self_care(self):
        assert determine_care_level("low", {"headache": True}) == "self_care"

    def test_low_with_mild_fever_maps_to_self_care(self):
        # A mild fever below 102 with no other red flags stays self-care/monitor.
        assert determine_care_level("low", {"fever": True, "fever_temperature": 101}) == "self_care"

    def test_haversine_distance_sane(self):
        # Madurai to approx Melur ~ 20 km
        d = haversine_distance(9.9252, 78.1198, 10.0315, 78.3384)
        assert 15 < d < 30

    def test_facility_ranking_prefers_near_and_appropriate(self):
        class FakeFacility:
            def __init__(self, id, ftype, lat, lon, emergency=False):
                self.id, self.facility_type = id, ftype
                self.name = f"Facility {id}"
                self.latitude, self.longitude = lat, lon
                self.emergency_available = emergency
                self.services, self.contact_number, self.address = [], "", ""

        facilities = [
            FakeFacility(1, "hospital", 9.93, 78.12),
            FakeFacility(2, "phc", 9.94, 78.13),
            FakeFacility(3, "hospital", 10.5, 79.0, emergency=True),
        ]
        ranked = rank_facilities(facilities, 9.93, 78.12, "hospital", top_n=2)
        assert ranked[0]["id"] == 1  # nearest appropriate hospital wins
        assert len(ranked) == 2


# ---------------------------------------------------------------------------
# Community priority score
# ---------------------------------------------------------------------------

class TestCommunityPriority:
    def _community(self, **overrides):
        class C:
            name = "Test Village"
            village = "Test"
            district = "Madurai"
            latitude, longitude = 9.9, 78.1
            population = 5000
            distance_to_nearest_facility_km = 20
            has_phc = has_chc = has_hospital = has_pharmacy = False
            elderly_population_pct = 14
            children_population_pct = 24
            pregnant_women_count = 15
            accessibility_score = 0.3
        c = C()
        for k, v in overrides.items():
            setattr(c, k, v)
        return c

    def test_remote_community_scores_high(self):
        result = calculate_priority_score(self._community(), [])
        assert result["priority_score"] > 50
        assert result["priority_level"] in ("high", "critical")

    def test_well_served_community_scores_low(self):
        c = self._community(
            distance_to_nearest_facility_km=2,
            has_phc=True, has_chc=True, has_hospital=True, has_pharmacy=True,
            accessibility_score=0.9,
        )
        result = calculate_priority_score(c, [])
        assert result["priority_score"] < 40

    def test_reasons_explain_the_score(self):
        result = calculate_priority_score(self._community(), [])
        assert result["reasons"]
        assert any("km" in r for r in result["reasons"])

    def test_health_demand_raises_score(self):
        class S:
            report_count = 12
            severity_indicator = 0.8
        base = calculate_priority_score(self._community(), [])
        with_signals = calculate_priority_score(self._community(), [S(), S(), S()])
        assert with_signals["priority_score"] > base["priority_score"]


# ---------------------------------------------------------------------------
# API smoke tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


def _register_and_login(client, email, password="testpass123", role="patient"):
    client.post("/api/auth/register", json={
        "email": email, "password": password, "full_name": "Test User", "role": role,
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


class TestAuthAPI:
    def test_register_and_login(self, client):
        token = _register_and_login(client, "authuser@test.com")
        assert token.count(".") == 2  # JWT shape

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "email": "wrongpw@test.com", "password": "secret99",
            "full_name": "Wrong PW",
        })
        resp = client.post("/api/auth/login", json={
            "email": "wrongpw@test.com", "password": "not-it",
        })
        assert resp.status_code == 401

    def test_duplicate_register_rejected(self, client):
        body = {"email": "dup@test.com", "password": "secret99", "full_name": "Dup"}
        assert client.post("/api/auth/register", json=body).status_code == 201
        assert client.post("/api/auth/register", json=body).status_code == 400

    def test_me_requires_auth(self, client):
        assert client.get("/api/auth/me").status_code in (401, 403)

    def test_me_with_token(self, client):
        token = _register_and_login(client, "metest@test.com")
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "metest@test.com"


class TestHealthCheckinAPI:
    def test_checkin_moderate_flow(self, client):
        token = _register_and_login(client, "checkin@test.com")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post("/api/health/checkin", headers=headers, json={
            "feeling_today": "bad",
            "fever": True, "fever_temperature": 101.5,
            "cough": True, "headache": True, "weakness": True,
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["screening"]["urgency_level"] in ("low", "moderate", "high", "emergency")
        assert data["screening"]["care_route"]["recommended_care_level"]

        # Symptom list must be derived server-side for the timeline
        timeline = client.get("/api/health/timeline", headers=headers).json()
        checkin_entry = next(
            t for t in timeline["timeline"] if t["type"] == "health_checkin"
        )
        assert checkin_entry["data"]["symptoms"] is not None

    def test_checkin_emergency_escalation(self, client):
        token = _register_and_login(client, "emergency@test.com")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post("/api/health/checkin", headers=headers, json={
            "feeling_today": "terrible",
            "chest_discomfort": True, "breathing_difficulty": True,
            "dizziness": True, "pain": True, "pain_severity": 9,
        })
        screening = resp.json()["screening"]
        assert screening["urgency_level"] == "emergency"
        assert screening["red_flags_detected"] is True

    def test_checkin_requires_auth(self, client):
        assert client.post("/api/health/checkin", json={"feeling_today": "good"}).status_code in (401, 403)

    def test_invalid_temperature_rejected(self, client):
        token = _register_and_login(client, "badtemp@test.com")
        resp = client.post("/api/health/checkin", headers={
            "Authorization": f"Bearer {token}"
        }, json={"fever": True, "fever_temperature": "not-a-number"})
        assert resp.status_code == 422


class TestEmergencyAPI:
    def test_health_card_minimum_necessary(self, client):
        token = _register_and_login(client, "card@test.com")
        resp = client.post("/api/emergency/health-card", headers={
            "Authorization": f"Bearer {token}"
        }, json={})
        assert resp.status_code == 200
        card = resp.json()
        # Minimum necessary fields only — no full history dump
        assert "patient_name" in card
        assert "share_token" in card
        assert "timeline" not in card and "checkins" not in card


class TestFacilitiesAPI:
    def test_list_facilities(self, client):
        token = _register_and_login(client, "fac@test.com")
        resp = client.get("/api/facilities/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "facilities" in resp.json()
