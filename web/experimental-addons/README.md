# CREDIUM — Experimental Addons

## Multi-Role Dashboard (Hackathon Demo UI)

**Status:** 🧪 Experimental / Not production-ready

This directory contains an experimental multi-role frontend for the CREDIUM demo, replacing the original single-page `web/index.html` with role-specific dashboards.

### Dashboards

| Role | File | Purpose |
|------|------|---------|
| 🏠 Landing | `index.html` | Role selection with live API status |
| 📋 NGO Worker | `ngo-worker.html` | Bill creation, vendor management, quick actions |
| 🛡️ NGO Manager | `ngo-manager.html` | Command center, fraud detection, chain health |
| 🏪 Vendor | `vendor.html` | Invoice tracking, payment history, earnings |
| 💝 Donor | `donor.html` | Impact visualization, fund flow, transparency |

### How to Run

```bash
# From repo root
python api/main.py  # serves at http://127.0.0.1:8000

# Or with uvicorn
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

The landing page at `/` lets you choose which dashboard to access.

### API Endpoints

All dashboards pull from these backend endpoints:
- `GET /api/state` — System state, chain health, meter summary
- `GET /api/bills` — List of all bills with verdicts
- `POST /api/release` — Submit a bill release
- `POST /api/watcher/scan` — Run equivocation detection
- `POST /api/attack/forge30` — Trigger forge-30 attack demo
- `POST /api/attack/double-claim` — Trigger double-claim demo
- `GET /api/eval` — Attack detection evaluation metrics
- `GET /api/reset` — Reset simulation to clean state
- `GET /api/health` — Chain health check

### Tech Stack

- **Pure HTML/CSS/JS** — No framework, no build step
- **Dark theme** — Consistent across all dashboards
- **Auto-refresh** — 5-10s polling for live data
- **Responsive** — Works on desktop and mobile

### Known Issues

- No authentication / authorization
- No CSP headers
- Error states not fully handled (graceful degradation needed)
- No unit or E2E tests
- Not suitable for production deployment

### Branch

This lives on the `ui-redesign` branch and is **not yet merged to main**.
