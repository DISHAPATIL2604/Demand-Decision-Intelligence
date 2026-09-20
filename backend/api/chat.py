"""
Chat API Router
Endpoints:
  POST /api/chat/message    – Process a user message and return AI decision response
  GET  /api/chat/suggestions – Return suggested starter questions
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.core.deps import get_current_user
from backend.models.user import User
from backend.services.chat_assistant import ChatAssistantService

router = APIRouter()
chat_service = ChatAssistantService()


# ── Request / Response schemas ──────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    message: str
    history: List[Dict[str, Any]] = []


class EvidenceItem(BaseModel):
    field: str
    value: Any


class ChatMessageResponse(BaseModel):
    reply: str
    citations: List[str]
    intent: Optional[str] = None
    evidence: List[Dict[str, Any]] = []


class ChatSuggestionsResponse(BaseModel):
    suggestions: List[str]


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/message", response_model=ChatMessageResponse)
def send_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process a natural-language question using the RAG decision assistant."""
    try:
        result = chat_service.process_message(request.message, request.history, db)
        return ChatMessageResponse(
            reply=result["reply"],
            citations=result.get("citations", []),
            intent=result.get("intent"),
            evidence=result.get("evidence", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.get("/suggestions", response_model=ChatSuggestionsResponse)
def get_suggestions(current_user: User = Depends(get_current_user)):
    """Return curated starter questions for the assistant."""
    return ChatSuggestionsResponse(suggestions=chat_service.get_suggestions())
