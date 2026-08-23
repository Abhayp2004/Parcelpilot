# ParcelPilot Support

ParcelPilot Support is an internal AI support agent for authorised ParcelPilot staff. It combines policy and contract search, structured logistics data lookups, and confirmation-gated ticket actions in a single interface.

## Stack

- Backend: Python 3.11 + FastAPI
- Agent: LangChain tool-calling agent with Anthropic `claude-sonnet-4-6`
- Vector store: local ChromaDB
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Document parsing: `pdfplumber` with `pypdf` fallback
- Structured data: pandas + openpyxl
- Frontend: React + Vite + TypeScript + Tailwind CSS

## Features

- Policy, SOP, guide, and agreement search with source-priority ordering
- Structured lookups for accounts, orders, tickets, cancellation eligibility, and failed-pickup credits
- Explicit conflict handling when customer agreements override general policy
- Mock role-based auth enforced in the tool layer
- Pending-confirmation action flow for escalations and ticket updates
- Insights panel for SLA risk, repeated open-ticket accounts, and recent ticket spikes

## Project layout

```text
parcelpilot/
├── backend/
├── data/
├── frontend/
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Setup

1. Export your Anthropic key:

```bash
export ANTHROPIC_API_KEY=your_key
```

2. Install backend dependencies:

```bash
cd parcelpilot
pip install -r backend/requirements.txt
```

3. Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

4. Ingest the supplied PDFs into Chroma:

```bash
python -m backend.data.loader
```

5. Start the backend:

```bash
uvicorn backend.main:app --reload
```

6. Start the frontend in another terminal:

```bash
cd frontend
npm run dev
```

7. Open `http://localhost:5173`.

## API endpoints

- `POST /chat`
- `POST /confirm_action`
- `GET /users`
- `POST /ingest`
- `GET /insights`
- `GET /health`

## Architecture notes

The backend uses a tool-calling LangChain agent with three tools:

- `search_documents` queries Chroma and returns policy snippets grouped by source priority.
- `lookup_data` reads the Excel snapshot and derives SLA, cancellation, and service-credit context using the dataset snapshot time as the reference clock.
- `prepare_action` returns a pending action object that must be confirmed through `/confirm_action`.

Source trust is handled in three places:

- Document ingestion tags each chunk with priority metadata.
- `search_documents` surfaces deprecated-source warnings and agreement-versus-policy conflicts.
- The system prompt instructs the agent to cite sources, surface uncertainty, and prefer customer agreements over general policy.

Access control is enforced in the tool layer through `backend/auth/mock_auth.py`, not just in prompt text.

ChromaDB was chosen because it keeps the retrieval layer local, persistent, and zero-infrastructure for the assessment dataset size.

## Product note

This build explicitly addresses the trust and reliability problem through source precedence, conflict warnings, deprecated-document handling, and an insights panel for proactive operational risk.

Intentionally left out:

- Real authentication and persistence beyond in-memory sessions/actions
- Production ticketing integrations
- Streaming responses and advanced retry handling

Suggested success metric:

- `% of support questions resolved without human escalation within 60 seconds`

## Docker

Build and run both services:

```bash
docker-compose up --build
```

The backend will be available at `http://localhost:8000` and the frontend at `http://localhost:5173`.
