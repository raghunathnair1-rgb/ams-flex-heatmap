# AMS Flex-Date Flight Finder

A conversational "flex-date heatmap" flight search agent for Amsterdam Schiphol
(AMS). Ask it about a destination and roughly when you can travel; it maps out
a calendar heatmap of day-by-day prices and points out the cheapest day.

## Architecture

```
React UI (frontend/)  ->  FastAPI (api/index.py)  ->  Agent loop (api/agent.py, max 5 turns)  ->  Tool (api/flights.py: search_flights)
```

See [`AGENTS.md`](AGENTS.md) for how this maps onto harness / loop / skills /
graph engineering, and [`skills/search_flights.skill.md`](skills/search_flights.skill.md)
for the skill spec itself.

- **Agent loop** (`api/agent.py`): calls Azure AI Foundry (Azure OpenAI-compatible
  chat completions) with function/tool calling. Guardrails:
  - loop cap: 5 model turns per request
  - tool-call limit: 3 tool calls per request
  - retry policy: a failing tool call retries up to 3 times
  - one short system role, nothing else
- **Skill / tool** (`api/flights.py`): exactly one skill is registered —
  `search_flights(destination, start_date, end_date)`. That is the entire
  tool surface; no code execution, file access, or web-browsing tool exists
  anywhere in this app. Runs on a deterministic mock generator (seeded by
  destination + date, with weekday/season effects) by default, clearly
  labeled as such in every response's `"source"` field — never presented as
  real data. `api/amadeus_client.py` is a real-data integration attempt kept
  as reference wiring: Amadeus for Developers Self-Service (the free tier
  this was built against) was **permanently shut down in July 2026** — portal
  decommissioned, API keys disabled, `test.api.amadeus.com` no longer
  resolves. Swapping in a live provider (Kiwi.com Tequila, Duffel, etc.) means
  replacing that one file; `flights.py`, the agent loop, and the frontend
  don't need to change.
- **Frontend** (`frontend/`): React + Vite. Chat panel on the left, calendar
  heatmap (sequential color scale, legend, tooltip, "best day" badge) on the
  right.

## Scope guardrails (`api/guardrails.py`)

This agent does one job — flexible-date flight search out of AMS — and
nothing else. Enforced in code, not just prompt wording, so it holds even if
the model is jailbroken:

- **Input filter**: off-topic asks (coding help, "search the web for…",
  essay/image generation, prompt-injection phrases like "ignore previous
  instructions") are refused *before* any model call is made — zero tokens
  spent, zero chance of the model complying.
- **Tool allowlist**: only `search_flights` may ever be executed. A
  hallucinated or injected call to any other tool name is rejected in code.
- **History sanitization**: client-supplied chat history is capped at 6 turns,
  truncated per message, and only `user`/`assistant` roles are accepted — a
  crafted payload can't smuggle in a fake `system` role.
- **Output sanitization**: replies are stripped of code fences as a
  belt-and-braces check.
- **Rate limiting**: 20 requests / 5 minutes per client IP on `/api/chat`
  (best-effort per warm serverless instance).
- **No API surface beyond the three routes below**: `/docs`, `/redoc`, and the
  OpenAPI schema are disabled in production (`docs_url=None` etc. in
  `api/index.py`), so there's nothing to introspect or probe.

The only live endpoints are `GET /api/health`, `GET /api/heatmap`, and
`POST /api/chat` — there is no web-search, code-execution, or general-purpose
endpoint anywhere in the app.

## Sandbox

A `Dockerfile` + `docker-compose.yml` run the backend hardened and isolated:

- non-root user (`app`)
- **read-only root filesystem** (`read_only: true`), with only `/tmp` writable
- **all Linux capabilities dropped** (`cap_drop: ALL`)
- `no-new-privileges` security option
- resource caps: 256 MB memory, 0.5 vCPU, 64 PIDs

```bash
docker compose up --build
```

(On Vercel, `api/index.py` already runs as an isolated Fluid Compute function
— a separate microVM per invocation — so the container sandbox above is for
local/self-hosted runs, or if you later move the backend off Vercel.)

## Environment variables

Copy `.env.example` to `.env` and fill in your Azure AI Foundry project details:

```
AZURE_AI_FOUNDRY_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_AI_FOUNDRY_API_KEY=<your-key>
AZURE_AI_FOUNDRY_MODEL=<your-deployment-name>
AZURE_AI_FOUNDRY_API_VERSION=2024-10-21
```

These are loaded via `python-dotenv` locally, and must be set as Environment
Variables in the Vercel project dashboard for the deployed app (`.env` is
gitignored and never committed).

## Run locally

Backend (FastAPI):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your Azure AI Foundry values
uvicorn api.index:app --reload --port 8000
```

Frontend (React/Vite), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (default `http://localhost:5173`). The Vite dev
server proxies `/api/*` to `http://localhost:8000` (see `frontend/vite.config.js`).

## Deploy to Vercel

```bash
npm i -g vercel   # if not already installed
vercel login
vercel link       # first time: creates/links the Vercel project
vercel env add AZURE_AI_FOUNDRY_ENDPOINT
vercel env add AZURE_AI_FOUNDRY_API_KEY
vercel env add AZURE_AI_FOUNDRY_MODEL
vercel env add AZURE_AI_FOUNDRY_API_VERSION
vercel --prod
```

Vercel builds the frontend as static assets (`frontend/dist`) and deploys
`api/index.py` as a single Python (FastAPI) serverless function, per
`vercel.json`.

## Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: AMS flex-date flight finder"
gh repo create ams-flex-heatmap --public --source=. --remote=origin --push
```
