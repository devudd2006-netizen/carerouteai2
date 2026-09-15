# CareRoute AI — Deployment Guide

Deployment instructions for the frontend, backend, and PostgreSQL database.

> **Rule of thumb:** never hardcode `localhost` URLs in deployment. All API URLs
> come from environment variables (see `.env.example`).

---

## 1. Environment Variables

| Variable | Where | Required | Description |
|---|---|---|---|
| `DATABASE_URL` | Backend | Yes | `postgresql://user:pass@host:5432/careroute` |
| `JWT_SECRET` | Backend | Yes | Long random string (`openssl rand -hex 32`) |
| `GEMINI_API_KEY` | Backend | No | Enables Gemini AI; rule-based fallback used without it |
| `FRONTEND_URL` | Backend | Yes | Public frontend origin (CORS) |
| `APP_URL` | Backend | No | Public backend origin |
| `DEBUG` | Backend | No | Set `false` in production (disables SQL echo logging) |
| `VITE_API_URL` | Frontend | Yes | Public backend API base URL, e.g. `https://api.yourdomain.com` |
| `VITE_MAP_TILE_URL` | Frontend | No | Custom tile server; OpenStreetMap used by default |

> **Local development note:** if PostgreSQL is not available, the backend
> automatically falls back to a local SQLite file (`backend/careroute.db`) so you
> can run the app without installing a database server.

---

## 2. Database (PostgreSQL)

Use any managed Postgres: Supabase, Neon, Railway, Render Postgres, RDS.

```bash
# Apply schema via Alembic
cd backend
alembic upgrade head

# Load clearly-labeled demo data (optional, for demos only)
python seed_database.py
```

Connection string format:

```
postgresql://USER:PASSWORD@HOST:PORT/DBNAME
```

Most managed providers require SSL. If so, append:

```
?sslmode=require
```

---

## 3. Backend (FastAPI)

### Option A: Render

1. New Web Service → connect your GitHub repo
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from the table above

### Option B: Railway

```bash
railway init
railway add --plugin postgresql
railway variables set JWT_SECRET=<your-secret>
railway up
```

### Option C: Fly.io

```bash
fly launch        # uses backend/Dockerfile
fly postgres create
fly postgres attach <app-postgres>
fly secrets set JWT_SECRET=<your-secret> GEMINI_API_KEY=<key>
fly deploy
```

### Option D: Docker (any VPS)

```bash
docker-compose up -d --build
```

The included `docker-compose.yml` runs PostgreSQL + backend with a shared
uploads volume.

---

## 4. Frontend (Vercel / Netlify)

```bash
cd frontend
npm install
npm run build
```

Deploy the `dist/` folder.

**Vercel dashboard settings:**

- Framework preset: Vite
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_URL=https://<your-backend-url>`

**Important:** add your deployed frontend URL to the backend's `FRONTEND_URL`
environment variable, or API calls will be blocked by CORS.

---

## 5. Production Hardening Checklist

- [ ] `DEBUG=false` (stops SQL query echo logging)
- [ ] Strong `JWT_SECRET` (32+ random bytes)
- [ ] `DATABASE_URL` uses a managed Postgres with SSL
- [ ] Password hashing upgraded from SHA-256 to bcrypt/argon2 (see `backend/app/core/auth.py`)
- [ ] HTTPS enforced at the load balancer / platform level
- [ ] Upload storage moved to S3-compatible storage with signed URLs
- [ ] Rate limiting enabled at the proxy (the backend exposes `RATE_LIMIT_PER_MINUTE`)
- [ ] Log aggregation configured; verify no PHI or tokens appear in logs
- [ ] Regular database backups scheduled
- [ ] Demo accounts removed or disabled (`is_active=false`)

---

## 6. Post-Deployment Smoke Test

```bash
curl https://<backend-url>/api/health
# → {"status":"healthy","service":"CareRoute AI Backend"}

curl -X POST https://<backend-url>/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"...","password":"..."}'
# → {"access_token":"...","token_type":"bearer","user":{...}}
```

Then open `https://<frontend-url>` and log in. Swagger UI remains available at
`https://<backend-url>/docs` (consider disabling in production via
`docs_url=None` in `backend/app/main.py` if the API should be private).
