from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.agent import get_agent
from backend.agent.tools.actions import execute_action
from backend.auth.mock_auth import get_all_users, get_user
from backend.data.loader import DEFAULT_DOCS_FOLDER, ingest_documents
from backend.data.structured import StructuredData
from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    ConfirmActionRequest,
    ConfirmActionResponse,
    IngestResponse,
    InsightsResponse,
    UsersResponse,
)

app = FastAPI(title="ParcelPilot Support API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = get_agent()
structured_data = StructuredData()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not get_user(request.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return ChatResponse(**agent.chat(request.message, request.user_id, request.session_id))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent request failed: {exc}") from exc


@app.post("/confirm_action", response_model=ConfirmActionResponse)
def confirm_action(request: ConfirmActionRequest) -> ConfirmActionResponse:
    if not request.confirmed:
        return ConfirmActionResponse(success=False, message="Action cancelled.")
    return ConfirmActionResponse(**execute_action(request.action_id, request.user_id))


@app.get("/users", response_model=UsersResponse)
def users() -> UsersResponse:
    return UsersResponse(users=list(get_all_users().values()))


@app.post("/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    chunks = ingest_documents(DEFAULT_DOCS_FOLDER, reset=True)
    return IngestResponse(chunks_ingested=chunks, message="Documents ingested successfully.")


@app.get("/insights", response_model=InsightsResponse)
def insights() -> InsightsResponse:
    payload = (
        structured_data.get_sla_risk_insights()
        + structured_data.get_repeated_issue_insights()
        + structured_data.get_recent_spike_insights()
    )
    return InsightsResponse(insights=payload)
