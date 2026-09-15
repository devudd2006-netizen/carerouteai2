# 🏥 CareRoute AI

**"Your Digital Home Health Companion"**

AI-assisted digital home healthcare and healthcare accessibility platform for rural and underserved communities.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Database Setup](#database-setup)
- [Environment Variables](#environment-variables)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Seeding Demo Data](#seeding-demo-data)
- [API Documentation](#api-documentation)
- [AI Configuration](#ai-configuration)
- [Maps Configuration](#maps-configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security & Privacy](#security--privacy)
- [ABDM Integration Roadmap](#abdm-integration-roadmap)
- [Known Limitations](#known-limitations)

---

## 🎯 Overview

CareRoute AI creates a continuous digital bridge between patients, doctors, emergency response, and community healthcare systems.

**Two-Way Healthcare Bridge:**

1. **Patient → Healthcare**: "I need care. Help me reach the right care."
2. **Healthcare → Community**: "This community needs healthcare. Help us decide where to send it."

**Important Medical Safety Notice:** CareRoute AI provides preliminary health screening and care navigation support. It does NOT replace professional medical advice, diagnosis, or treatment. All AI outputs are labeled as preliminary screening.

---

## ✨ Features

### Patient Features
- 🔐 Registration & Login (JWT authentication)
- 📋 Health Check-in (conversational symptom entry)
- 🧠 AI-Assisted Preliminary Screening
- ⚠️ Red-Flag Emergency Detection
- 🗺️ Care Route Engine (find appropriate care)
- 🗺️ Interactive Healthcare Facility Map
- 🏥 Emergency Health Card
- 💊 Medication Reminders & Adherence Tracking
- 📄 Medical Document Management
- 📅 Appointments & Follow-ups
- 🧬 Health Memory (longitudinal timeline)
- 👤 Profile Management

### Doctor Features
- 👥 Patient list & detail view
- 📝 Consultation notes & assessment
- 💊 Prescription creation
- 📅 Follow-up scheduling

### Community Health Intelligence
- 📊 Community Health Pulse dashboard
- 🗺️ Healthcare Gap Map with Care Priority Scores
- 🏕️ Medical Camp Recommendations
- 📈 Health demand trend analysis

### Admin Features
- 📊 System-wide dashboard
- 👥 User management overview
- 📈 Analytics

---

## 🏗️ Architecture

```
Patient → Health Monitoring → AI Screening → Risk Assessment → Care Route → Facility → Doctor
                                                                                      ↓
Community Data → Accessibility Analysis → Priority Score → Gap Map → Camp Recommendation
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Router, Recharts, Leaflet |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL |
| AI | Google Gemini API (with rule-based fallback) |
| Maps | Leaflet + OpenStreetMap |
| Auth | JWT (custom implementation, no external dependencies) |

---

## 📁 Project Structure

```
careroute-ai/
├── frontend/                 # React + Vite frontend
│   ├── src/
│   │   ├── components/       # Shared components
│   │   ├── pages/            # Page components
│   │   ├── contexts/         # React contexts (Auth)
│   │   ├── services/         # API service layer
│   │   ├── types/            # TypeScript types
│   │   └── utils/            # Utilities
│   ├── package.json
│   └── ...
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── core/             # Config, auth
│   │   ├── db/               # Database setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routes/           # API routes
│   │   ├── services/         # Business logic
│   │   └── main.py           # App entry point
│   ├── alembic/              # Database migrations
│   ├── seed_database.py      # Seed script
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.10
- **PostgreSQL** ≥ 14 (or use Docker)
- **Git**

### Option 1: Full Docker Stack (Recommended)

```bash
git clone <repository-url>
cd careroute-ai
cp .env.example .env

docker-compose up -d --build
# Postgres + backend + frontend (nginx, http://localhost:5173)

# Seed demo data (first time only)
docker exec -it careroute-backend python seed_database.py
```

### Option 2: Local Development

```bash
git clone <repository-url>
cd careroute-ai
cp .env.example .env

# --- Backend ---
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# No PostgreSQL installed? The backend falls back to SQLite automatically.
alembic upgrade head            # or: python -c "from app.db.database import init_db; init_db()"
python seed_database.py
uvicorn app.main:app --reload --port 8000

# --- Frontend (new terminal) ---
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

Demo accounts are listed on the login screen and in `docs/demo-scenarios.md`.

### Option 2: Local PostgreSQL

```bash
# Create database
createdb careroute

# Copy environment file
cp .env.example .env
# Edit DATABASE_URL in .env

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed_database.py
uvicorn app.main:app --reload --port 8000

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

---

## 🗄️ Database Setup

### Initialize Database

```bash
cd backend

# Option 1: Direct init
python -c "from app.db.database import init_db; init_db()"

# Option 2: With Alembic
alembic upgrade head
```

### Seed Demo Data

```bash
python seed_database.py
```

This creates:
- 1 Admin, 5 Doctors, 10 Patients
- 15 Healthcare Facilities
- 10 Communities/Villages
- Health check-ins, assessments, prescriptions
- Community health signals & priority scores
- Medical camp recommendations

---

## 🔧 Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/careroute

# Authentication
JWT_SECRET=change-this-to-a-strong-random-secret

# AI (optional - falls back to rule-based screening)
GEMINI_API_KEY=your-gemini-api-key

# CORS
FRONTEND_URL=http://localhost:5173
APP_URL=http://localhost:8000
```

---

## 🖥️ Frontend Setup

```bash
cd frontend
npm install
npm run dev    # Development server on port 5173
npm run build  # Production build
```

---

## 🔌 API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Patient | fowmiya@demo.com | patient123 |
| Patient | ravi@demo.com | patient123 |
| Doctor | dr.arun@demo.com | doctor123 |
| Admin | admin@careroute.demo | admin123 |

---

## 🤖 AI Configuration

### Google Gemini (Optional)

1. Get API key from https://aistudio.google.com/apikey
2. Add to `.env`: `GEMINI_API_KEY=your-key`
3. The system will use Gemini for enhanced health screening

### Fallback Mode

If no Gemini API key is provided, the system uses a **rule-based screening engine** that provides safe, conservative health assessments. This is clearly labeled in the UI.

### Red-Flag Safety Engine

A **deterministic rule-based engine** always runs regardless of AI service. It detects potentially life-threatening symptom combinations and overrides AI screening when emergency flags are detected.

---

## 🗺️ Maps Configuration

### Default: OpenStreetMap + Leaflet

No API key required. Uses free OpenStreetMap tiles via Leaflet.

### Custom Tile Server

Set in `.env`:
```env
VITE_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

---

## 🧪 Testing

### Backend Test Suite (33 tests)

```bash
cd backend
pip install -r requirements.txt   # includes pytest + httpx
python -m pytest tests/ -q
```

Covers: red-flag emergency engine (false-positive & true-positive cases),
rule-based screening fallback, care route engine, community priority score,
auth API, check-in → screening flow, emergency escalation, and the emergency
health card (minimum-necessary fields).

### Backend Import Check

```bash
cd backend
python -c "from app.main import app; print('Backend OK')"
```

### Frontend Build Check

```bash
cd frontend
npm install
npm run build
```

### Manual API Testing

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
```

---

## 🚢 Deployment

### Frontend (Vercel)

```bash
cd frontend
npm run build
# Deploy dist/ folder to Vercel
```

### Backend (Render/Railway)

1. Set environment variables in the platform
2. Build command: `cd backend && pip install -r requirements.txt`
3. Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Database

Use a hosted PostgreSQL service (Supabase, Neon, Railway).

Update `DATABASE_URL` in your deployment environment.

---

## 🔒 Security & Privacy

- JWT authentication with configurable expiration
- Password hashing with salted SHA-256
- Role-based access control (Patient, Doctor, Admin, Community Authority)
- CORS configuration for frontend origin
- Input validation via Pydantic
- File upload validation (type + size limits)
- Secure filename generation
- No sensitive data in logs
- Environment variable configuration (no hardcoded secrets)
- Emergency health cards are time-limited (24h expiry)
- Community analytics use aggregated/de-identified data

---

## 🏛️ ABDM Integration Roadmap

The health record layer is designed to support India's ABDM (Ayushman Bharat Digital Mission) ecosystem:

1. **Current**: `LocalHealthRecordProvider` — local database storage
2. **Future**: `ABDMHealthRecordProvider` — ABDM API integration
3. **Abstraction**: `HealthRecordProvider` interface for easy swapping

Actual ABDM integration requires government API credentials and compliance certification.

---

## ⚠️ Known Limitations

- **Demo Data Only**: Healthcare facilities use seed data; real government facility APIs would replace this
- **No Real Emergency Services**: Emergency workflow is a prototype; no real ambulance dispatch
- **AI Limitations**: Rule-based fallback provides conservative assessments; Gemini integration enhances accuracy
- **No Real OCR**: Document extraction relies on AI text parsing; production would use proper OCR
- **Voice Input**: Browser Speech API support varies; not available in all environments
- **Multilingual**: UI supports English; Tamil/Hindi translations are planned

---

## 📄 License

MIT License

---

**CareRoute AI** — From your home to the right care. 🏥💚
