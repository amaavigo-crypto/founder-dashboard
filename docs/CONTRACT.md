# Metrics contract v1

Every product that feeds Founders Dashboard exposes **one** `GET` endpoint that returns this JSON. The dashboard calls it nightly with `Authorization: Bearer <API key>` and stores the result as that day's snapshot.

Rules:
- All fields are optional except what you want to see. Missing parts just show as empty.
- **Money is for one day, in INR**: payments received that day and costs incurred that day. The dashboard sums days into 7/30/90-day ranges and monthly bars. If your product does not track money, omit `money` and enter it through `POST /api/manual-money`. Do not do both for the same day, or it is counted twice.
- `customers.total` means one customer in your product's own sense (a company, a tenant). Name it in `labels.customers`.
- Keep the response small and fast (under 2 seconds). Never include personal data about end users.

```json
{
  "contract_version": 1,
  "generated_at": "2026-11-25T00:30:00Z",
  "labels": { "customers": "Companies", "size": "Employees", "trend": "Daily active users" },
  "customers": { "total": 18, "new": 1, "churned": 0 },
  "users": { "active_daily": 640, "active_weekly": 1650, "active_monthly": 3100 },
  "trend_value": 640,
  "money": { "revenue": 9800, "cost": { "ai": 210, "hosting": 800, "messaging": 0, "other": 650 } },
  "health": { "uptime_pct": 99.9, "errors": 3, "failed_jobs": 0 },
  "attention": [{ "level": "critical", "title": "2 nightly jobs failed" }],
  "headline": [
    { "label": "Companies", "value": "18" },
    { "label": "Employees managed", "value": "3,420" },
    { "label": "Revenue", "value": "₹2.9L" },
    { "label": "AI cost", "value": "₹6.1K" }
  ],
  "panel": {
    "title": "Companies using each module",
    "rows": [{ "label": "Payroll", "value": "11 of 18", "pct": 61 }]
  },
  "customers_list": [
    { "name": "Company A", "plan": "Growth", "size": "640", "last_active": "Today", "revenue": "₹48K", "status": "active" }
  ],
  "ai_cost_by_customer": [{ "name": "Company A", "cost": 2400 }]
}
```

| Field | Used for |
|---|---|
| `labels` | Wording on the project page (what a customer is called, the table's size column, the trend chart title) |
| `customers`, `users` | Overview tiles and project tiles |
| `trend_value` | The 30-day bar chart. Falls back to `users.active_daily` |
| `money` | Revenue, cost, profit, margin, monthly chart |
| `health` | Uptime tile |
| `attention` | "Needs attention" list and the project's status pill (`critical`, `warn`, `info`) |
| `headline` | The four numbers on the project's Overview card (max 4) |
| `panel` | The project-specific panel (max 8 rows, `pct` 0 to 100) |
| `customers_list` | The table on the project page (max 50 rows; `status` is `active`, `quiet` or `at_risk`) |
| `ai_cost_by_customer` | Money page, last 30 days |

## Adding the endpoint to a product

**Next.js route handler** (HR portal, Lead-Gen), `app/api/founder/metrics/route.ts`:

```ts
import { NextResponse } from "next/server";
import crypto from "crypto";

export async function GET(req: Request) {
  const given = (req.headers.get("authorization") ?? "").replace("Bearer ", "");
  const key = process.env.FOUNDER_METRICS_KEY ?? "";
  const ok = key.length >= 24 && given.length === key.length &&
    crypto.timingSafeEqual(Buffer.from(given), Buffer.from(key));
  if (!ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  // Replace with real queries. Count only; no personal data.
  return NextResponse.json({
    contract_version: 1,
    labels: { customers: "Companies", size: "Employees", trend: "Daily active users" },
    customers: { total: 0 },
    users: { active_daily: 0, active_weekly: 0, active_monthly: 0 },
    attention: [],
  });
}
```

Then in the dashboard: **Add a project**, paste the full URL of that endpoint and the same key.

## Daily sync

Point cronjob.org at `POST https://<dashboard-host>/internal/pull` with header `X-Pull-Secret: <PULL_SECRET>`, once a day (for example 06:00 IST). A founder can also trigger a single project from the API: `POST /api/projects/{id}/pull`.
