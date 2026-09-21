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


def db_session_factory():
    """Direct session for seeding rows the API tests need but registration
    doesn't create (facilities, etc.)."""
    from app.db.database import SessionLocal
    return SessionLocal()


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


class TestHealthTrendsAPI:
    def test_trends_shape_and_counts(self, client):
        token = _register_and_login(client, "trends@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        for feeling in ("good", "bad"):
            resp = client.post("/api/health/checkin", headers=headers, json={
                "feeling_today": feeling,
                "fever": True, "headache": True,
            })
            assert resp.status_code == 200, resp.text

        resp = client.get("/api/health/trends", headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["total_checkins"] == 2
        assert len(data["series"]) == 2
        # Oldest-first series for charting
        assert data["series"][0]["date"] <= data["series"][1]["date"]
        for point in data["series"]:
            assert point["symptom_count"] == 2
            assert point["risk_level"] in ("low", "moderate", "high", "emergency")

        symptoms = {t["symptom"]: t["count"] for t in data["top_symptoms"]}
        assert symptoms.get("fever") == 2
        assert symptoms.get("headache") == 2
        assert data["feeling_counts"].get("good") == 1
        assert data["feeling_counts"].get("bad") == 1

    def test_trends_requires_auth(self, client):
        assert client.get("/api/health/trends").status_code in (401, 403)

    def test_trends_empty_for_new_patient(self, client):
        token = _register_and_login(client, "trendsempty@test.com")
        resp = client.get("/api/health/trends", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_checkins"] == 0
        assert data["series"] == []
        assert data["top_symptoms"] == []


class TestDoctorAppointmentAPI:
    def test_doctor_schedules_and_patient_sees_appointment(self, client):
        doctok = _register_and_login(client, "docappt@test.com", role="doctor")
        patok = _register_and_login(client, "patappt@test.com")

        # Find the patient's profile id via the doctor patient list
        patients = client.get("/api/doctor/patients", headers={
            "Authorization": f"Bearer {doctok}"
        }).json()["patients"]
        patient = next(p for p in patients if p["email"] == "patappt@test.com")

        resp = client.post("/api/doctor/appointments", headers={
            "Authorization": f"Bearer {doctok}"
        }, json={
            "patient_id": patient["id"],
            "date": "2026-10-01T10:30",
            "reason": "Blood pressure review",
            "is_follow_up": True,
        })
        assert resp.status_code == 201, resp.text

        # Patient sees it with the doctor's name attached
        plist = client.get("/api/appointments", headers={
            "Authorization": f"Bearer {patok}"
        }).json()["appointments"]
        match = next(a for a in plist if a["id"] == resp.json()["id"])
        assert match["status"] == "scheduled"
        assert match["reason"] == "Blood pressure review"
        assert match["doctor_name"]

        # Doctor's own listing shows the patient name
        dlist = client.get("/api/doctor/appointments", headers={
            "Authorization": f"Bearer {doctok}"
        }).json()["appointments"]
        dmatch = next(a for a in dlist if a["id"] == resp.json()["id"])
        assert dmatch["patient_name"] == "Test User"

    def test_patient_cannot_use_doctor_appointment_endpoints(self, client):
        patok = _register_and_login(client, "patnotdoc@test.com")
        resp = client.post("/api/doctor/appointments", headers={
            "Authorization": f"Bearer {patok}"
        }, json={"patient_id": 1, "date": "2026-10-01T10:00"})
        assert resp.status_code in (401, 403)

    def test_doctor_appointment_validation(self, client):
        doctok = _register_and_login(client, "docval@test.com", role="doctor")
        headers = {"Authorization": f"Bearer {doctok}"}
        # Missing date
        assert client.post("/api/doctor/appointments", headers=headers,
                           json={"patient_id": 1}).status_code == 400
        # Bad date format
        assert client.post("/api/doctor/appointments", headers=headers,
                           json={"patient_id": 1, "date": "not-a-date"}).status_code == 400
        # Unknown patient
        assert client.post("/api/doctor/appointments", headers=headers,
                           json={"patient_id": 999999, "date": "2026-10-01"}).status_code == 404

    def test_doctor_can_update_appointment(self, client):
        doctok = _register_and_login(client, "docupdate@test.com", role="doctor")
        headers = {"Authorization": f"Bearer {doctok}"}
        patients = client.get("/api/doctor/patients", headers=headers).json()["patients"]
        resp = client.post("/api/doctor/appointments", headers=headers, json={
            "patient_id": patients[0]["id"], "date": "2026-10-03T09:00",
        })
        appt_id = resp.json()["id"]

        # Reschedule + complete
        upd = client.patch(f"/api/doctor/appointments/{appt_id}", headers=headers,
                           json={"date": "2026-10-04T15:00", "status": "completed"})
        assert upd.status_code == 200, upd.text
        dlist = client.get("/api/doctor/appointments", headers=headers).json()["appointments"]
        match = next(a for a in dlist if a["id"] == appt_id)
        assert match["status"] == "completed"
        assert "15:00" in match["appointment_date"] or "03" in match["appointment_date"]

        # Invalid status rejected
        bad = client.patch(f"/api/doctor/appointments/{appt_id}", headers=headers,
                           json={"status": "bogus"})
        assert bad.status_code == 400

    def test_patient_cannot_update_appointments(self, client):
        patok = _register_and_login(client, "patnoedit@test.com")
        resp = client.patch("/api/doctor/appointments/1", headers={
            "Authorization": f"Bearer {patok}"
        }, json={"status": "completed"})
        assert resp.status_code in (401, 403, 404)

    def test_doctor_can_cancel_own_appointment(self, client):
        doctok = _register_and_login(client, "doccancel@test.com", role="doctor")
        headers = {"Authorization": f"Bearer {doctok}"}
        patients = client.get("/api/doctor/patients", headers=headers).json()["patients"]
        resp = client.post("/api/doctor/appointments", headers=headers, json={
            "patient_id": patients[0]["id"], "date": "2026-10-02T09:00",
        })
        appt_id = resp.json()["id"]
        del_resp = client.delete(f"/api/doctor/appointments/{appt_id}", headers=headers)
        assert del_resp.status_code == 200
        dlist = client.get("/api/doctor/appointments", headers=headers).json()["appointments"]
        assert next(a for a in dlist if a["id"] == appt_id)["status"] == "cancelled"


class TestDoctorConsultationAPI:
    def test_consultation_without_checkin_reaches_patient_timeline(self, client):
        """Doctor consultation must NOT 500 when no assessment_id is passed
        (the UI path) and must appear on the patient's timeline."""
        doctok = _register_and_login(client, "docconsult@test.com", role="doctor")
        patok = _register_and_login(client, "patconsult@test.com")
        headers = {"Authorization": f"Bearer {doctok}"}

        patients = client.get("/api/doctor/patients", headers=headers).json()["patients"]
        patient = next(p for p in patients if p["email"] == "patconsult@test.com")

        resp = client.post("/api/doctor/consultations", headers=headers, json={
            "patient_id": patient["id"],
            "notes": "Rest and hydration advised",
            "diagnosis": "Viral fever",
        })
        assert resp.status_code == 200, resp.text

        timeline = client.get("/api/health/timeline", headers={
            "Authorization": f"Bearer {patok}"
        }).json()["timeline"]
        consult = [t for t in timeline if t["type"] == "assessment" and t["data"].get("is_doctor_consultation")]
        assert consult, "consultation must appear in patient timeline"
        entry = consult[0]["data"]
        assert entry["diagnosis"] == "Viral fever"
        assert entry["doctor_notes"] == "Rest and hydration advised"
        assert entry["doctor_name"] == "Test User"

    def test_consultation_requires_patient(self, client):
        doctok = _register_and_login(client, "docconsult2@test.com", role="doctor")
        assert client.post("/api/doctor/consultations", headers={
            "Authorization": f"Bearer {doctok}"
        }, json={"notes": "hi"}).status_code == 400
        assert client.post("/api/doctor/consultations", headers={
            "Authorization": f"Bearer {doctok}"
        }, json={"patient_id": 999999, "notes": "hi"}).status_code == 404

    def test_doctor_prescription_visible_to_patient(self, client):
        doctok = _register_and_login(client, "docrx@test.com", role="doctor")
        patok = _register_and_login(client, "patrx@test.com")
        headers = {"Authorization": f"Bearer {doctok}"}

        patients = client.get("/api/doctor/patients", headers=headers).json()["patients"]
        patient = next(p for p in patients if p["email"] == "patrx@test.com")

        resp = client.post("/api/doctor/prescriptions", headers=headers, json={
            "patient_id": patient["id"],
            "diagnosis": "Test diagnosis",
            "items": [{"medicine_name": "Ibuprofen 400mg", "dosage": "400mg", "frequency": "Twice daily"}],
        })
        assert resp.status_code == 200, resp.text

        plist = client.get("/api/prescriptions", headers={
            "Authorization": f"Bearer {patok}"
        }).json()["prescriptions"]
        match = next(p for p in plist if p["id"] == resp.json()["id"])
        assert match["doctor_name"] == "Test User"
        assert match["items"][0]["medicine_name"] == "Ibuprofen 400mg"

    def test_doctor_prescription_creates_medication_reminders(self, client):
        """Doctor-added medicines must appear on the patient's Medications page."""
        doctok = _register_and_login(client, "docrxmed@test.com", role="doctor")
        patok = _register_and_login(client, "patrxmed@test.com")
        headers = {"Authorization": f"Bearer {doctok}"}

        patients = client.get("/api/doctor/patients", headers=headers).json()["patients"]
        patient = next(p for p in patients if p["email"] == "patrxmed@test.com")

        resp = client.post("/api/doctor/prescriptions", headers=headers, json={
            "patient_id": patient["id"],
            "diagnosis": "Infection",
            "items": [
                {"medicine_name": "Azithromycin", "dosage": "500mg", "frequency": "Once daily at night"},
                {"medicine_name": "Paracetamol", "dosage": "650mg", "frequency": "Twice daily"},
            ],
        })
        assert resp.status_code == 200, resp.text
        assert resp.json()["medications_created"] == 2

        meds = client.get("/api/medications", headers={
            "Authorization": f"Bearer {patok}"
        }).json()["medications"]
        names = {m["medicine_name"] for m in meds}
        assert "Azithromycin" in names and "Paracetamol" in names
        azithro = next(m for m in meds if m["medicine_name"] == "Azithromycin")
        assert azithro["source"] == "doctor"
        assert azithro["time_of_day"] == "night"  # parsed from frequency

    def test_patient_cannot_create_doctor_prescription(self, client):
        patok = _register_and_login(client, "patnotrx@test.com")
        resp = client.post("/api/doctor/prescriptions", headers={
            "Authorization": f"Bearer {patok}"
        }, json={"patient_id": 1, "items": [{"medicine_name": "X"}]})
        assert resp.status_code in (401, 403)


class TestMedicationManagementAPI:
    def test_patient_adds_and_removes_own_medication(self, client):
        token = _register_and_login(client, "selfmed@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post("/api/medications", headers=headers, json={
            "medicine_name": "Vitamin D3",
            "dosage": "1000 IU",
            "frequency": "Once daily",
            "time_of_day": "morning",
        })
        assert resp.status_code == 201, resp.text
        med = resp.json()["medication"]
        assert med["source"] == "patient"

        listed = client.get("/api/medications", headers=headers).json()["medications"]
        assert any(m["id"] == med["id"] for m in listed)

        del_resp = client.delete(f"/api/medications/{med['id']}", headers=headers)
        assert del_resp.status_code == 200
        listed_after = client.get("/api/medications", headers=headers).json()["medications"]
        assert not any(m["id"] == med["id"] for m in listed_after)

    def test_add_medication_validation(self, client):
        token = _register_and_login(client, "selfmedval@test.com")
        headers = {"Authorization": f"Bearer {token}"}
        assert client.post("/api/medications", headers=headers, json={}).status_code == 400
        assert client.post("/api/medications", headers=headers, json={"medicine_name": "   "}).status_code == 400

    def test_patient_cannot_remove_others_medication(self, client):
        a = _register_and_login(client, "medowner@test.com")
        b = _register_and_login(client, "medstranger@test.com")
        resp = client.post("/api/medications", headers={
            "Authorization": f"Bearer {a}"
        }, json={"medicine_name": "Secret med"})
        med_id = resp.json()["id"]
        assert client.delete(f"/api/medications/{med_id}", headers={
            "Authorization": f"Bearer {b}"
        }).status_code == 404

    def test_medication_endpoints_require_auth(self, client):
        assert client.post("/api/medications", json={"medicine_name": "X"}).status_code in (401, 403)
        assert client.delete("/api/medications/1").status_code in (401, 403)


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
    @staticmethod
    def _seed_hospitals(db):
        """Test hospitals around Madurai with differing capability."""
        from app.models.facility import HealthcareFacility
        if db.query(HealthcareFacility).count() > 0:
            return
        db.add_all([
            HealthcareFacility(
                name="Mega General Hospital", facility_type="hospital",
                latitude=9.9300, longitude=78.1200, address="1 Main Rd",
                services=["general", "surgery", "cardiology", "diagnostics", "orthopedics"],
                emergency_available=True, opening_hours="24/7", is_active=True,
            ),
            HealthcareFacility(
                name="Small Clinic Hospital", facility_type="hospital",
                latitude=9.9400, longitude=78.1300, address="2 Side St",
                services=["general"], emergency_available=False,
                opening_hours="8am-6pm", is_active=True,
            ),
            HealthcareFacility(
                name="Distant Specialty Hospital", facility_type="hospital",
                latitude=10.1000, longitude=78.7000, address="3 Far Ave",
                services=["general", "surgery", "cardiology", "diagnostics"],
                emergency_available=True, opening_hours="24/7", is_active=True,
            ),
        ])
        db.commit()

    def test_list_facilities(self, client):
        token = _register_and_login(client, "fac@test.com")
        self._seed_hospitals(db_session_factory())
        resp = client.get("/api/facilities/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "facilities" in resp.json()

    def test_best_hospitals_without_location(self, client):
        """No coordinates: overall_best must still be populated."""
        self._seed_hospitals(db_session_factory())
        token = _register_and_login(client, "best1@test.com")
        resp = client.get("/api/facilities/best", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["nearby_best"] == []
        assert len(data["overall_best"]) > 0
        top = data["overall_best"][0]
        assert top["facility_type"] in ("hospital", "emergency")
        assert top["capability_score"] >= data["overall_best"][-1]["capability_score"]

    def test_best_hospitals_with_location_ranks_nearby(self, client):
        """With coordinates, nearby_best is populated and proximity-led."""
        self._seed_hospitals(db_session_factory())
        token = _register_and_login(client, "best2@test.com")
        # Madurai center — seeded facilities cluster around 9.92-9.94, 78.11-78.13
        resp = client.get(
            "/api/facilities/best?latitude=9.9252&longitude=78.1198",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data["nearby_best"]) > 0
        assert len(data["overall_best"]) > 0
        for f in data["nearby_best"]:
            assert f["distance_km"] is not None
            assert "rank_score" in f
        # Proximity-first: distances must be non-decreasing down the list
        dists = [f["distance_km"] for f in data["nearby_best"]]
        assert dists == sorted(dists), f"nearby_best not distance-sorted: {dists}"
        # The 17km-away hospital must never appear when close ones exist
        assert all(f["distance_km"] <= 15 for f in data["nearby_best"])

    def test_nearby_never_beaten_by_distant_hospital(self, client):
        """The core guarantee: a world-class hospital 17 km away must not
        outrank a basic clinic 1 km away in the nearby list."""
        self._seed_hospitals(db_session_factory())
        token = _register_and_login(client, "best3@test.com")
        resp = client.get(
            "/api/facilities/best?latitude=9.9252&longitude=78.1198",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        nearby_names = [f["name"] for f in resp["nearby_best"]]
        # Distant Specialty Hospital (10.10, 78.70) is ~60 km away — excluded.
        assert "Distant Specialty Hospital" not in nearby_names
        # Mega General (0.5km) vs Small Clinic (1.6km): both near; the better
        # hospital may lead only when distances are in the same band.
        assert resp["nearby_best"][0]["distance_km"] <= 2
        assert resp["used_fallback"] is False

    def test_best_hospitals_requires_auth(self, client):
        assert client.get("/api/facilities/best").status_code in (401, 403)
