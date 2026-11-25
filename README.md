# Founders Dashboard

One place for the founders to see business health across every project. FastAPI backend + Next.js frontend. Products feed it through a small, standard [metrics endpoint](docs/CONTRACT.md); the dashboard never reads their databases.

```
backend/   FastAPI, SQLAlchemy, JWT auth, nightly puller, aggregation
frontend/  Next.js 15 (App Router): Overview, Project detail, Money, Add project
docs/      CONTRACT.md: what each product must return
```

## Run it locally

```bash
# 1. backend
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set JWT_SECRET, PULL_SECRET, FOUNDER_EMAIL, FOUNDER_PASSWORD
python -m app.seed              # founder login + 2 sample projects (use --no-sample for real use)
uvicorn app.main:app --port 8000

# 2. frontend (new terminal)
cd frontend
cp .env.example .env.local
npm install
npm run dev                     # http://localhost:3000
```

Sign in with `FOUNDER_EMAIL` / `FOUNDER_PASSWORD`. Tests: `cd backend && pytest`.

## Going live

- Use Postgres: `DATABASE_URL=postgresql+psycopg://user:pass@host:5432/founders`.
- Backend: `uvicorn app.main:app --port 8000` under PM2. Frontend: `npm run build && npm start` under PM2, with `API_URL=http://127.0.0.1:8000`. Keep the backend off the public internet except `/internal/pull`; the browser only talks to the Next.js server.
- Serve over HTTPS (the session cookie is `secure` in production).
- Change every secret in `.env`. Replace the seeded sample projects with real ones through **Add project**.
- Schedule `POST /internal/pull` once a day on cronjob.org (see the contract doc).

## What is not built yet

- Several founders with different permissions (everyone who can sign in sees everything).
- A screen for manual revenue entry (use `POST /api/manual-money` for now).
- Alert notifications (email or Slack). "Needs attention" is shown on screen only.
