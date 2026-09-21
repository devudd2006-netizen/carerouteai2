"""
CareRoute AI - Database Seed Script

Creates demo data for all features:
- 10 patients, 5 doctors, admin
- 15 healthcare facilities
- 10 communities/villages
- Health check-ins, assessments, prescriptions
- Care plans, medication reminders
- Community health signals and priority scores
- Medical camp recommendations

Run: python -m backend.seed_database
"""
import sys
import os
import json
import random
from datetime import datetime, timedelta, date, timezone

# Windows consoles often default to cp1252 and cannot print emoji.
# Reconfigure stdout/stderr to UTF-8 so seed output always works.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import SessionLocal, init_db
from app.models.user import User, UserRole
from app.models.patient import PatientProfile, EmergencyContact, DoctorProfile
from app.models.health import (
    HealthCheckin, HealthAssessment, CarePlan,
    MedicationReminder, MedicationLog, Appointment
)
from app.models.document import MedicalDocument, Prescription, PrescriptionItem
from app.models.facility import HealthcareFacility
from app.models.community import Community, CommunityHealthSignal, CommunityPriorityScore, MedicalCampRecommendation
from app.core.auth import hash_password

# --- Seed Data ---

PATIENTS = [
    {"name": "Fowmiya R", "email": "fowmiya@demo.com", "gender": "female", "dob": "1995-03-15", "blood": "B+", "village": "Kannanur", "district": "Madurai", "state": "Tamil Nadu", "lat": 10.0168, "lon": 78.2001, "allergies": "Peanuts", "conditions": "None"},
    {"name": "Ravi Kumar", "email": "ravi@demo.com", "gender": "male", "dob": "1985-07-22", "blood": "O+", "village": "Thiruparankundram", "district": "Madurai", "state": "Tamil Nadu", "lat": 9.9853, "lon": 78.1200, "allergies": "None", "conditions": "Diabetes Type 2"},
    {"name": "Lakshmi Devi", "email": "lakshmi@demo.com", "gender": "female", "dob": "1970-11-08", "blood": "A+", "village": "Alanganallur", "district": "Madurai", "state": "Tamil Nadu", "lat": 9.9635, "lon": 78.0886, "allergies": "Sulfa drugs", "conditions": "Hypertension"},
    {"name": "Murugan S", "email": "murugan@demo.com", "gender": "male", "dob": "1962-01-30", "blood": "AB+", "village": "Melur", "district": "Madurai", "state": "Tamil Nadu", "lat": 10.0315, "lon": 78.3384, "allergies": "Penicillin", "conditions": "Asthma"},
    {"name": "Priya Sharma", "email": "priya@demo.com", "gender": "female", "dob": "1998-09-12", "blood": "O-", "village": "Usilampatti", "district": "Madurai", "state": "Tamil Nadu", "lat": 9.9763, "lon": 77.8375, "allergies": "None", "conditions": "None"},
    {"name": "Kumar Rajan", "email": "kumar@demo.com", "gender": "male", "dob": "1980-05-18", "blood": "B-", "village": "Sedapatti", "district": "Madurai", "state": "Tamil Nadu", "lat": 9.9500, "lon": 77.9000, "allergies": "None", "conditions": "Hypertension, Diabetes"},
    {"name": "Anitha K", "email": "anitha@demo.com", "gender": "female", "dob": "1990-04-25", "blood": "A-", "village": "Thalakavur", "district": "Madurai", "state": "Tamil Nadu", "lat": 10.0100, "lon": 78.1500, "allergies": "None", "conditions": "Asthma"},
    {"name": "Senthil M", "email": "senthil@demo.com", "gender": "male", "dob": "1975-12-03", "blood": "O+", "village": "Vasudevanallur", "district": "Tirunelveli", "state": "Tamil Nadu", "lat": 9.6843, "lon": 77.6333, "allergies": "Aspirin", "conditions": "Heart disease"},
    {"name": "Meena Lakshmi", "email": "meena@demo.com", "gender": "female", "dob": "2001-08-17", "blood": "B+", "village": "Ramanathapuram", "district": "Madurai", "state": "Tamil Nadu", "lat": 9.9250, "lon": 78.0800, "allergies": "None", "conditions": "None"},
    {"name": "Venkatesh P", "email": "venkatesh@demo.com", "gender": "male", "dob": "1958-06-09", "blood": "A+", "village": "Palamedu", "district": "Madurai", "state": "Tamil Nadu", "lat": 9.9700, "lon": 78.1300, "allergies": "None", "conditions": "Diabetes Type 2, Hypertension"},
]

DOCTORS = [
    {"name": "Dr. Arun Krishnan", "email": "dr.arun@demo.com", "specialization": "General Medicine", "hospital": "Government Hospital, Madurai", "exp": 12},
    {"name": "Dr. Sujatha R", "email": "dr.sujatha@demo.com", "specialization": "Pediatrics", "hospital": "District Hospital, Madurai", "exp": 8},
    {"name": "Dr. Rajesh Menon", "email": "dr.rajesh@demo.com", "specialization": "Cardiology", "hospital": "Meenakshi Medical Center", "exp": 15},
    {"name": "Dr. Kavitha N", "email": "dr.kavitha@demo.com", "specialization": "General Practice", "hospital": "Primary Health Centre, Alanganallur", "exp": 6},
    {"name": "Dr. Mohan S", "email": "dr.mohan@demo.com", "specialization": "Emergency Medicine", "hospital": "Government Hospital, Madurai", "exp": 10},
]

FACILITIES = [
    {"name": "Government Rajaji Hospital", "type": "hospital", "lat": 9.9252, "lon": 78.1198, "address": "Medical College Road, Madurai", "village": "Madurai", "district": "Madurai", "services": ["general", "emergency", "surgery", "cardiology", "orthopedics", "diagnostics"], "emergency": True, "hours": "24/7", "contact": "0452-2301384"},
    {"name": "Madurai Medical College Hospital", "type": "hospital", "lat": 9.9300, "lon": 78.1200, "address": "Alagar Kovil Road, Madurai", "village": "Madurai", "district": "Madurai", "services": ["general", "emergency", "surgery", "diagnostics", "maternity"], "emergency": True, "hours": "24/7", "contact": "0452-2300056"},
    {"name": "Meenakshi Mission Hospital", "type": "hospital", "lat": 9.9400, "lon": 78.1350, "address": "Lake Area, Madurai", "village": "Madurai", "district": "Madurai", "services": ["general", "cardiology", "diagnostics", "surgery"], "emergency": True, "hours": "24/7", "contact": "0452-2580800"},
    {"name": "PHC Kannanur", "type": "phc", "lat": 10.0200, "lon": 78.2050, "address": "Kannanur Main Road", "village": "Kannanur", "district": "Madurai", "services": ["general", "maternal_health", "immunization"], "emergency": False, "hours": "9 AM - 4 PM", "contact": "0452-1234567"},
    {"name": "PHC Alanganallur", "type": "phc", "lat": 9.9650, "lon": 78.0900, "address": "Alanganallur Town", "village": "Alanganallur", "district": "Madurai", "services": ["general", "maternal_health", "basic_diagnostics"], "emergency": False, "hours": "9 AM - 4 PM", "contact": "0452-2345678"},
    {"name": "PHC Melur", "type": "phc", "lat": 10.0350, "lon": 78.3400, "address": "Melur Town Centre", "village": "Melur", "district": "Madurai", "services": ["general", "maternal_health"], "emergency": False, "hours": "9 AM - 4 PM", "contact": "0452-3456789"},
    {"name": "CHC Usilampatti", "type": "chc", "lat": 9.9780, "lon": 77.8400, "address": "Usilampatti Main Road", "village": "Usilampatti", "district": "Madurai", "services": ["general", "diagnostics", "maternal_health", "surgery"], "emergency": True, "hours": "8 AM - 6 PM", "contact": "0452-4567890"},
    {"name": "CHC Tirunelveli", "type": "chc", "lat": 8.7139, "lon": 77.7567, "address": "Tirunelveli Town", "village": "Tirunelveli", "district": "Tirunelveli", "services": ["general", "diagnostics", "maternal_health", "surgery"], "emergency": True, "hours": "8 AM - 6 PM", "contact": "0462-5678901"},
    {"name": "Apollo Clinic Madurai", "type": "clinic", "lat": 9.9350, "lon": 78.1250, "address": "KK Nagar, Madurai", "village": "Madurai", "district": "Madurai", "services": ["general", "diagnostics", "cardiology"], "emergency": False, "hours": "8 AM - 8 PM", "contact": "0452-6789012"},
    {"name": "Lakshmi Pharmacy", "type": "pharmacy", "lat": 9.9270, "lon": 78.1150, "address": "Near Market, Madurai", "village": "Madurai", "district": "Madurai", "services": ["medicines", "basic_health_products"], "emergency": False, "hours": "8 AM - 10 PM", "contact": "0452-7890123"},
    {"name": "SRL Diagnostics Madurai", "type": "diagnostic", "lat": 9.9320, "lon": 78.1180, "address": "Anna Nagar, Madurai", "village": "Madurai", "district": "Madurai", "services": ["blood_test", "xray", "ultrasound", "ecg"], "emergency": False, "hours": "7 AM - 9 PM", "contact": "0452-8901234"},
    {"name": "Emergency Response Centre", "type": "emergency", "lat": 9.9200, "lon": 78.1200, "address": "Collectorate Road, Madurai", "village": "Madurai", "district": "Madurai", "services": ["emergency_triage", "ambulance_dispatch", "first_aid"], "emergency": True, "hours": "24/7", "contact": "108"},
    {"name": "PHC Sedapatti", "type": "phc", "lat": 9.9520, "lon": 77.9020, "address": "Sedapatti Village", "village": "Sedapatti", "district": "Madurai", "services": ["general", "maternal_health"], "emergency": False, "hours": "9 AM - 4 PM", "contact": "0452-9012345"},
    {"name": "Clinic Thalakavur", "type": "clinic", "lat": 10.0120, "lon": 78.1520, "address": "Thalakavur Road", "village": "Thalakavur", "district": "Madurai", "services": ["general", "basic_diagnostics"], "emergency": False, "hours": "9 AM - 5 PM", "contact": "0452-0123456"},
    {"name": "PHC Palamedu", "type": "phc", "lat": 9.9720, "lon": 78.1320, "address": "Palamedu Main Road", "village": "Palamedu", "district": "Madurai", "services": ["general", "maternal_health", "immunization"], "emergency": False, "hours": "9 AM - 4 PM", "contact": "0452-1234568"},
]

COMMUNITIES = [
    {"name": "Kannanur Village", "village": "Kannanur", "district": "Madurai", "lat": 10.0168, "lon": 78.2001, "pop": 3500, "dist": 18.0, "phc": True, "chc": False, "hospital": False, "pharmacy": False, "elderly": 12, "children": 22, "pregnant": 15, "access": 0.3},
    {"name": "Thiruparankundram", "village": "Thiruparankundram", "district": "Madurai", "lat": 9.9853, "lon": 78.1200, "pop": 15000, "dist": 5.0, "phc": True, "chc": False, "hospital": False, "pharmacy": True, "elderly": 8, "children": 20, "pregnant": 30, "access": 0.7},
    {"name": "Alanganallur", "village": "Alanganallur", "district": "Madurai", "lat": 9.9635, "lon": 78.0886, "pop": 8000, "dist": 12.0, "phc": True, "chc": False, "hospital": False, "pharmacy": False, "elderly": 14, "children": 24, "pregnant": 20, "access": 0.4},
    {"name": "Melur Region", "village": "Melur", "district": "Madurai", "lat": 10.0315, "lon": 78.3384, "pop": 12000, "dist": 20.0, "phc": True, "chc": False, "hospital": False, "pharmacy": False, "elderly": 15, "children": 25, "pregnant": 25, "access": 0.3},
    {"name": "Usilampatti Area", "village": "Usilampatti", "district": "Madurai", "lat": 9.9763, "lon": 77.8375, "pop": 10000, "dist": 15.0, "phc": True, "chc": True, "hospital": False, "pharmacy": True, "elderly": 11, "children": 21, "pregnant": 18, "access": 0.5},
    {"name": "Sedapatti", "village": "Sedapatti", "district": "Madurai", "lat": 9.9500, "lon": 77.9000, "pop": 4500, "dist": 22.0, "phc": True, "chc": False, "hospital": False, "pharmacy": False, "elderly": 16, "children": 26, "pregnant": 12, "access": 0.25},
    {"name": "Thalakavur", "village": "Thalakavur", "district": "Madurai", "lat": 10.0100, "lon": 78.1500, "pop": 5000, "dist": 10.0, "phc": False, "chc": False, "hospital": False, "pharmacy": False, "elderly": 13, "children": 23, "pregnant": 10, "access": 0.35},
    {"name": "Vasudevanallur", "village": "Vasudevanallur", "district": "Tirunelveli", "lat": 9.6843, "lon": 77.6333, "pop": 7000, "dist": 25.0, "phc": False, "chc": True, "hospital": False, "pharmacy": False, "elderly": 17, "children": 27, "pregnant": 14, "access": 0.2},
    {"name": "Ramanathapuram", "village": "Ramanathapuram", "district": "Madurai", "lat": 9.9250, "lon": 78.0800, "pop": 6000, "dist": 8.0, "phc": False, "chc": False, "hospital": False, "pharmacy": False, "elderly": 10, "children": 22, "pregnant": 16, "access": 0.45},
    {"name": "Palamedu", "village": "Palamedu", "district": "Madurai", "lat": 9.9700, "lon": 78.1300, "pop": 4000, "dist": 6.0, "phc": True, "chc": False, "hospital": False, "pharmacy": False, "elderly": 14, "children": 24, "pregnant": 8, "access": 0.5},
]

SYMPTOM_SCENARIOS = [
    # Routine / mild
    {"symptoms": {"headache": True, "feeling_today": "okay"}, "severity": "low", "text": "Mild headache, feeling okay otherwise"},
    {"symptoms": {"cough": True, "feeling_today": "okay"}, "severity": "low", "text": "Dry cough for 2 days"},
    {"symptoms": {"sleep_quality": 2, "stress_level": 4, "feeling_today": "okay"}, "severity": "low", "text": "Poor sleep, feeling stressed"},
    
    # Moderate
    {"symptoms": {"fever": True, "fever_temperature": 101.5, "headache": True, "weakness": True, "feeling_today": "bad"}, "severity": "moderate", "text": "Fever with headache and weakness"},
    {"symptoms": {"cough": True, "fever": True, "fever_temperature": 100.5, "fatigue": True, "feeling_today": "bad"}, "severity": "moderate", "text": "Cough with mild fever"},
    {"symptoms": {"pain": True, "pain_location": "abdomen", "pain_severity": 6, "vomiting": True, "feeling_today": "bad"}, "severity": "moderate", "text": "Abdominal pain with vomiting"},
    
    # High
    {"symptoms": {"breathing_difficulty": True, "fever": True, "fever_temperature": 103.5, "weakness": True, "feeling_today": "terrible"}, "severity": "high", "text": "High fever with breathing difficulty"},
    {"symptoms": {"chest_discomfort": True, "breathing_difficulty": True, "dizziness": True, "feeling_today": "terrible"}, "severity": "high", "text": "Chest pain with breathing difficulty and dizziness"},
    
    # Emergency (red-flag triggers)
    {"symptoms": {"chest_discomfort": True, "breathing_difficulty": True, "pain_severity": 9, "sweating": True, "feeling_today": "terrible"}, "severity": "emergency", "text": "Severe chest pain with breathing difficulty"},
    {"symptoms": {"breathing_difficulty": True, "fever": True, "fever_temperature": 104, "severe_weakness": True, "feeling_today": "terrible"}, "severity": "emergency", "text": "Very high fever with severe breathing difficulty"},
]

PRESCRIPTIONS_DATA = [
    {
        "diagnosis": "Upper respiratory tract infection",
        "items": [
            {"name": "Amoxicillin 500mg", "dosage": "500mg", "frequency": "Three times daily", "duration": "5 days", "instructions": "Take after food"},
            {"name": "Paracetamol 650mg", "dosage": "650mg", "frequency": "As needed for fever", "duration": "5 days", "instructions": "Max 3g/day"},
            {"name": "Cetirizine 10mg", "dosage": "10mg", "frequency": "Once daily", "duration": "5 days", "instructions": "At bedtime"},
        ],
    },
    {
        "diagnosis": "Type 2 Diabetes management",
        "items": [
            {"name": "Metformin 500mg", "dosage": "500mg", "frequency": "Twice daily", "duration": "30 days", "instructions": "Take with meals"},
            {"name": "Glimepiride 2mg", "dosage": "2mg", "frequency": "Once daily", "duration": "30 days", "instructions": "Before breakfast"},
        ],
    },
    {
        "diagnosis": "Hypertension management",
        "items": [
            {"name": "Amlodipine 5mg", "dosage": "5mg", "frequency": "Once daily", "duration": "30 days", "instructions": "Morning"},
            {"name": "Telmisartan 40mg", "dosage": "40mg", "frequency": "Once daily", "duration": "30 days", "instructions": "With or without food"},
        ],
    },
]


def seed():
    """Seed the database with demo data."""
    print("🏥 CareRoute AI - Seeding Database...")
    init_db()
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(User).count()
        if existing > 0:
            print(f"⚠️  Database already has {existing} users. Skipping seed.")
            print("   To re-seed, clear the database first.")
            return
        
        # 1. Create Admin
        admin = User(
            email="admin@careroute.demo",
            password_hash=hash_password("admin123"),
            full_name="System Admin",
            role="admin",
            is_active=True,
            is_verified=True,
            community_analytics_participation=True,
        )
        db.add(admin)
        db.flush()
        print("  ✅ Admin user created")
        
        # 2. Create Doctors
        doctor_users = []
        for d in DOCTORS:
            user = User(
                email=d["email"],
                password_hash=hash_password("doctor123"),
                full_name=d["name"],
                role="doctor",
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            db.flush()
            doctor_users.append(user)
            
            profile = DoctorProfile(
                user_id=user.id,
                specialization=d["specialization"],
                hospital_name=d["hospital"],
                experience_years=d["exp"],
            )
            db.add(profile)
        print("  ✅ 5 doctors created")
        
        # 3. Create Patients
        patient_profiles = []
        for p in PATIENTS:
            user = User(
                email=p["email"],
                password_hash=hash_password("patient123"),
                full_name=p["name"],
                role="patient",
                is_active=True,
                is_verified=True,
                phone=f"+91{random.randint(6000000000, 9999999999)}",
            )
            db.add(user)
            db.flush()
            
            dob_parts = p["dob"].split("-")
            profile = PatientProfile(
                user_id=user.id,
                date_of_birth=date(int(dob_parts[0]), int(dob_parts[1]), int(dob_parts[2])),
                gender=p["gender"],
                blood_group=p["blood"],
                village=p["village"],
                district=p["district"],
                state=p["state"],
                latitude=p["lat"],
                longitude=p["lon"],
                allergies=p["allergies"] if p["allergies"] != "None" else None,
                chronic_conditions=p["conditions"] if p["conditions"] != "None" else None,
                preferred_language="en",
            )
            db.add(profile)
            db.flush()
            patient_profiles.append(profile)
            
            # Add emergency contact
            contact = EmergencyContact(
                patient_id=profile.id,
                name=f"Contact for {p['name'].split()[0]}",
                relationship_type="Family",
                phone=f"+91{random.randint(6000000000, 9999999999)}",
                is_primary=True,
            )
            db.add(contact)
        print("  ✅ 10 patients with emergency contacts created")
        
        # 4. Create Healthcare Facilities
        for f in FACILITIES:
            facility = HealthcareFacility(
                name=f["name"],
                facility_type=f["type"],
                latitude=f["lat"],
                longitude=f["lon"],
                address=f["address"],
                village=f["village"],
                district=f["district"],
                state="Tamil Nadu",
                services=f["services"],
                emergency_available=f["emergency"],
                opening_hours=f["hours"],
                contact_number=f["contact"],
            )
            db.add(facility)
        print("  ✅ 15 healthcare facilities created")
        
        # 5. Create Health Check-ins and Assessments
        for i, profile in enumerate(patient_profiles):
            # 2-3 check-ins per patient
            for j in range(random.randint(2, 3)):
                scenario = random.choice(SYMPTOM_SCENARIOS)
                # The symptoms JSON is a display list, so only real symptom names
                # (not scalar config keys like feeling_today/pain_severity).
                display_symptoms = [
                    k for k in scenario["symptoms"]
                    if k in {"fever", "cough", "breathing_difficulty", "chest_discomfort",
                             "headache", "dizziness", "weakness", "pain", "vomiting",
                             "diarrhea", "fatigue"}
                ]
                checkin = HealthCheckin(
                    patient_id=profile.id,
                    symptoms=display_symptoms,
                    symptom_details=scenario["symptoms"],
                    feeling_today=scenario["symptoms"].get("feeling_today", "okay"),
                    fever=scenario["symptoms"].get("fever", False),
                    fever_temperature=scenario["symptoms"].get("fever_temperature"),
                    cough=scenario["symptoms"].get("cough", False),
                    breathing_difficulty=scenario["symptoms"].get("breathing_difficulty", False),
                    chest_discomfort=scenario["symptoms"].get("chest_discomfort", False),
                    headache=scenario["symptoms"].get("headache", False),
                    dizziness=scenario["symptoms"].get("dizziness", False),
                    weakness=scenario["symptoms"].get("weakness", False),
                    pain=scenario["symptoms"].get("pain", False),
                    pain_location=scenario["symptoms"].get("pain_location"),
                    pain_severity=scenario["symptoms"].get("pain_severity"),
                    vomiting=scenario["symptoms"].get("vomiting", False),
                    medication_taken=True,
                    ai_risk_level=scenario["severity"],
                    red_flags_detected=(scenario["severity"] == "emergency"),
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
                )
                db.add(checkin)
                db.flush()
                
                # Create assessment
                assessment = HealthAssessment(
                    checkin_id=checkin.id,
                    patient_id=profile.id,
                    urgency_level=scenario["severity"],
                    possible_concerns=[{"concern": "Preliminary screening based on symptoms", "relevance": scenario["severity"]}],
                    recommended_action="Consult a healthcare professional" if scenario["severity"] != "low" else "Monitor symptoms",
                    warning_signs=["Seek medical attention if symptoms worsen"] if scenario["severity"] in ["high", "emergency"] else [],
                    created_at=checkin.created_at,
                )
                db.add(assessment)
        
        print("  ✅ Health check-ins and assessments created")
        
        # 6. Create Prescriptions and Care Plans
        for i, profile in enumerate(patient_profiles[:5]):
            presc_data = PRESCRIPTIONS_DATA[i % len(PRESCRIPTIONS_DATA)]
            prescription = Prescription(
                patient_id=profile.id,
                doctor_id=doctor_users[0].id,
                diagnosis=presc_data["diagnosis"],
                is_confirmed=True,
            )
            db.add(prescription)
            db.flush()
            
            for item in presc_data["items"]:
                pi = PrescriptionItem(
                    prescription_id=prescription.id,
                    medicine_name=item["name"],
                    dosage=item["dosage"],
                    frequency=item["frequency"],
                    duration=item["duration"],
                    instructions=item["instructions"],
                )
                db.add(pi)
            
            # Create care plan
            care_plan = CarePlan(
                patient_id=profile.id,
                doctor_id=doctor_users[0].id,
                title=f"Care Plan: {presc_data['diagnosis']}",
                description=f"Management plan for {presc_data['diagnosis']}",
                medications=[{"name": it["name"], "dosage": it["dosage"], "frequency": it["frequency"]} for it in presc_data["items"]],
                doctor_instructions="Follow the prescribed medication schedule. Return for follow-up in 2 weeks.",
                lifestyle_instructions="Maintain a healthy diet. Stay hydrated. Get adequate rest.",
                is_active=True,
            )
            db.add(care_plan)
            db.flush()
            
            # Create medication reminders
            for it in presc_data["items"]:
                reminder = MedicationReminder(
                    patient_id=profile.id,
                    care_plan_id=care_plan.id,
                    medicine_name=it["name"],
                    dosage=it["dosage"],
                    frequency=it["frequency"],
                    time_of_day="morning",
                )
                db.add(reminder)
        
        print("  ✅ Prescriptions, care plans, and medication reminders created")
        
        # 7. Create Communities
        community_objects = []
        for c in COMMUNITIES:
            community = Community(
                name=c["name"],
                village=c["village"],
                district=c["district"],
                latitude=c["lat"],
                longitude=c["lon"],
                population=c["pop"],
                distance_to_nearest_facility_km=c["dist"],
                has_phc=c["phc"],
                has_chc=c["chc"],
                has_hospital=c["hospital"],
                has_pharmacy=c["pharmacy"],
                elderly_population_pct=c["elderly"],
                children_population_pct=c["children"],
                pregnant_women_count=c["pregnant"],
                accessibility_score=c["access"],
            )
            db.add(community)
            db.flush()
            community_objects.append(community)
        
        print("  ✅ 10 communities created")
        
        # 8. Create Community Health Signals
        signal_types = ["respiratory", "gastrointestinal", "fever_cluster", "pain_reports", "maternal_health"]
        for community in community_objects:
            for _ in range(random.randint(1, 3)):
                signal = CommunityHealthSignal(
                    community_id=community.id,
                    signal_type="symptom_cluster",
                    symptom_category=random.choice(signal_types),
                    report_count=random.randint(3, 15),
                    severity_indicator=round(random.uniform(0.2, 0.8), 2),
                )
                db.add(signal)
        
        print("  ✅ Community health signals created")
        
        # 9. Create Appointments
        appt_reasons = [
            "General consultation",
            "Follow-up consultation",
            "Review lab test results",
            "Blood pressure check",
            "Medication review",
            "Post-treatment follow-up",
        ]
        for i, profile in enumerate(patient_profiles[:5]):
            doctor_user = doctor_users[i % len(doctor_users)]
            for j in range(2):
                appointment = Appointment(
                    patient_id=profile.id,
                    doctor_id=doctor_user.id,
                    appointment_date=datetime.now(timezone.utc) + timedelta(days=random.randint(-10, 14)),
                    reason=random.choice(appt_reasons),
                    status=random.choice(["scheduled", "completed"]),
                    is_follow_up=(j > 0),
                )
                db.add(appointment)
        
        print("  ✅ Appointments created")
        
        db.commit()
        
        # 10. Calculate community priority scores
        from app.services.community_service import calculate_all_priority_scores, generate_camp_recommendation
        import asyncio
        
        print("\n📊 Calculating community priority scores...")
        scores = asyncio.run(calculate_all_priority_scores(db))
        print(f"  ✅ Priority scores calculated for {len(scores)} communities")
        
        # 11. Generate camp recommendations
        print("\n🏕️  Generating medical camp recommendations...")
        recs = asyncio.run(generate_camp_recommendation(db))
        print(f"  ✅ {len(recs)} camp recommendations generated")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("🎉 Database seeded successfully!")
        print("=" * 60)
        print("\n📋 Demo Accounts:")
        print("  Admin:      admin@careroute.demo / admin123")
        print("  Doctor:     dr.arun@demo.com / doctor123")
        print("  Patient:    fowmiya@demo.com / patient123")
        print("  Patient:    ravi@demo.com / patient123")
        print("  Patient:    lakshmi@demo.com / patient123")
        print("\n🔐 All passwords are demo-only. Change in production!")
        print("\n💡 Start the backend: uvicorn backend.app.main:app --reload --port 8000")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
