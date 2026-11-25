# Founders Dashboard

One place for the founders to see business health across every project. FastAPI backend + Next.js frontend. Products feed it through a small, standard [metrics endpoint](docs/CONTRACT.md); the dashboard never reads their databases.

```
backend/   FastAPI, SQLAlchemy, JWT auth, nightly puller, aggregation
frontend/  Next.js 15 (App Router): Overview, Project detail, Money, Add project
docs/      CONTRACT.md: what each product must return
```

## Run it locally

```bash
# 1. backend (on Windows Git Bash use: source .venv/Scripts/activate and python -m uvicorn)
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set JWT_SECRET, PULL_SECRET, FOUNDER_EMAIL, FOUNDER_PASSWORD
python -m app.seed              # founder login + 2 sample projects (use --no-sample for real use)
python -m uvicorn app.main:app --port 8000

# 2. frontend (new terminal)
cd frontend
cp .env.example .env.local
npm install
npm run dev                     # http://localhost:3000
```

Sign in with `FOUNDER_EMAIL` / `FOUNDER_PASSWORD`. Tests: `cd backend && pip install -r requirements-dev.txt && python -m pytest`.

## Deploy on Vercel

Two Vercel projects from the same repo, plus a Postgres database.

1. **Database.** In Vercel, Storage > Marketplace > Neon > create a database. Copy its connection string (use the pooled one, the host with `-pooler`).
2. **API project.** New Project > import the repo > **Root Directory: `backend`**. Framework is detected as FastAPI. Add environment variables:
   - `DATABASE_URL` the Neon connection string
   - `JWT_SECRET` 32+ random characters
   - `PULL_SECRET` any random string (only used for manual or external triggers)
   - `CRON_SECRET` 32+ random characters (Vercel Cron sends it automatically)
   - `FOUNDER_EMAIL`, `FOUNDER_PASSWORD` for the first login
   The app refuses to start on Vercel with SQLite or the dev secrets.
3. **Create the tables and the founder login, once, from your computer:**
   ```bash
   cd backend && . .venv/bin/activate          # on Windows Git Bash: source .venv/Scripts/activate
   DATABASE_URL="<the Neon string>" FOUNDER_EMAIL="you@example.com" FOUNDER_PASSWORD="..." python -m app.seed --no-sample
   ```
4. **Web project.** New Project > same repo > **Root Directory: `frontend`**. Add `API_URL` = the API project's URL (for example `https://founders-api.vercel.app`). Deploy, then sign in.
5. **Nightly sync.** `backend/vercel.json` already schedules `GET /api/cron/pull` daily at 00:30 UTC (6:00 am IST). Vercel runs crons on production deployments only. On the free Hobby plan the run can land anywhere in that hour, and once a day is the maximum; Pro allows every minute.
6. Add each product as a project in the dashboard (**Add project**), using its metrics URL and key.

Notes: the browser only talks to the web project; the web project's server calls the API with the founder's session token. The API URL is public, so the JWT secret must stay secret. To rotate `CRON_SECRET`, change it and redeploy (Vercel captures it per deployment).

### Self-hosting instead

Run `uvicorn app.main:app --port 8000` and `npm run build && npm start` under PM2, with Postgres and `API_URL=http://127.0.0.1:8000`. Point cronjob.org at `POST /internal/pull` with the `X-Pull-Secret` header.

## What is not built yet

- Several founders with different permissions (everyone who can sign in sees everything).
- A screen for manual revenue entry (use `POST /api/manual-money` for now).
- Alert notifications (email or Slack). "Needs attention" is shown on screen only.
