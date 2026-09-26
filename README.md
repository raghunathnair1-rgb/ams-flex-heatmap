# AMS Flex-Date Flight Finder

A conversational "flex-date heatmap" flight search agent for Amsterdam Schiphol
(AMS). Ask it about a destination and roughly when you can travel; it maps out
a calendar heatmap of day-by-day prices and points out the cheapest day.

## Architecture

```
React UI (frontend/)  ->  FastAPI (api/index.py)  ->  Agent loop (api/agent.py, max 5 turns)  ->  Tool (api/flights.py: search_flights)
```

- **Agent loop** (`api/agent.py`): calls Azure AI Foundry (Azure OpenAI-compatible
  chat completions) with function/tool calling. Guardrails:
  - loop cap: 5 model turns per request
  - tool-call limit: 3 tool calls per request
  - retry policy: a failing tool call retries up to 3 times
  - one short system role, nothing else
- **Tool** (`api/flights.py`): `search_flights(destination, start_date, end_date)`.
  No live flight API key is wired up, so prices are generated deterministically
  (seeded by destination + date, with weekday/season effects) — swap this
  function for a real provider (Amadeus, Duffel, Kiwi Tequila, …) without
  touching the agent loop or frontend.
- **Frontend** (`frontend/`): React + Vite. Chat panel on the left, calendar
  heatmap (sequential color scale, legend, tooltip, "best day" badge) on the
  right.

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
