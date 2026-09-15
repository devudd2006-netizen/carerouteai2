# CareRoute AI — Demo Accounts & Scenarios

All demo data is **fictional and clearly labeled**. Load it with:

```bash
cd backend
python seed_database.py
```

> The seed script is safe to re-run: it skips if users already exist. Delete
> `backend/careroute.db` (SQLite) or drop the schema (PostgreSQL) to re-seed.

---

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin / Community Authority | admin@careroute.demo | admin123 |
| Doctor | dr.arun@demo.com | doctor123 |
| Doctor | dr.sujatha@demo.com | doctor123 |
| Doctor | dr.rajesh@demo.com | doctor123 |
| Doctor | dr.kavitha@demo.com | doctor123 |
| Doctor | dr.mohan@demo.com | doctor123 |
| Patient | fowmiya@demo.com | patient123 |
| Patient | ravi@demo.com | patient123 |
| Patient | lakshmi@demo.com | patient123 |
| Patient | murugan@demo.com | patient123 |
| Patient | priya@demo.com | patient123 |
| Patient | kumar@demo.com | patient123 |
| Patient | anitha@demo.com | patient123 |
| Patient | senthil@demo.com | patient123 |
| Patient | meena@demo.com | patient123 |
| Patient | venkatesh@demo.com | patient123 |

All demo data (people, villages, facilities, phone numbers) is fictional.

---

## Scenario 1 — Routine Health Check

1. Log in as `fowmiya@demo.com` / `patient123`
2. Click **Check Health** (quick action on the dashboard)
3. Answer the conversational check-in: feeling "bad", tick **Fever** (101.5°F),
   **Cough**, **Headache**, **Weakness**
4. Result: **AI-Assisted Preliminary Screening** shows
   - urgency **MODERATE**
   - possible concerns ("fever may be associated with infection…")
   - recommended care level: **Community Health Centre / clinic**
5. Open **My Health Memory** — the check-in now appears on the health timeline

**What this demonstrates:** conversational check-in → AI screening →
appropriate (not maximum) care recommendation → longitudinal Health Memory.

---

## Scenario 2 — Potential Emergency (Red-Flag Engine)

Use the same patient. In the check-in, select:

- Chest discomfort ✔
- Breathing difficulty ✔
- Dizziness ✔
- Weakness ✔
- Pain, severity 9/10 ✔

Result: the deterministic **Red-Flag Safety Engine** (not the AI) fires
multiple rules and the app switches to the emergency interface:

- "POTENTIAL EMERGENCY DETECTED"
- Emergency guidance per red flag
- Nearest emergency-capable facility with distance and phone number
- **Emergency Health Card** with minimum-necessary information
- Clearly labeled demo emergency workflow (no real ambulance is contacted)

**What this demonstrates:** rule-based safety overrides AI — red flags always
escalate to EMERGENCY regardless of what the AI says.

---

## Scenario 3 — Prescription → Care Plan → Reminders

1. Log in as `dr.arun@demo.com` / `doctor123`
2. Open a patient → add **Doctor Assessment** (notes, diagnosis)
3. Create a **Prescription** with 1–2 medicines and a follow-up
4. Log back in as the patient → **My Medicines**
5. The prescribed medicines appear as Morning/Afternoon/Night reminders
6. Mark doses **Taken** — adherence % updates
7. The care plan shows doctor instructions, follow-up date, and monitoring notes

**What this demonstrates:** only doctor-approved information becomes medical
instructions; medication reminders are generated from confirmed prescriptions;
never from AI output.

---

## Scenario 4 — Community Healthcare Gap (Authority)

1. Log in as `admin@careroute.demo` / `admin123`
2. Open **Community Health Pulse**
3. Cards show: communities monitored, high-priority areas, healthcare gaps,
   recommended camps
4. Open the **Healthcare Gap Map** — each village is shaded by Care Priority
   Score (LOW → CRITICAL)
5. Select **Vasudevanallur** (score ~88, CRITICAL):
   - 25 km from nearest suitable facility
   - no PHC, no hospital, no pharmacy
   - high vulnerable population
   - increased health demand signals
6. Click **Recommend Medical Camp**
7. The optimizer proposes: location, priority score, reason, population,
   suggested services (general consultation, maternal screening, BP/sugar
   screening), suggested duration

**What this demonstrates:** aggregated, de-identified community analytics →
transparent priority scoring → actionable (but advisory) camp recommendation.
Final deployment decisions remain with healthcare authorities.

---

## Notes for Judges / Reviewers

- AI outputs are always labeled **"AI-Assisted Preliminary Screening"**;
  doctor entries are labeled **"Doctor Assessment"** — they are never mixed.
- If no `GEMINI_API_KEY` is configured, screening runs on a conservative
  rule-based engine and the UI shows:
  **"AI service unavailable — basic rule-based screening used."**
- The emergency workflow is a prototype: no real ambulance dispatch, hospital
  API, or ABDM integration is claimed anywhere in the product.
