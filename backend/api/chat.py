"""
Chat API Router
Project: Demand-Decision-Intelligence
Location: backend/api/chat.py

Endpoints:
  POST /api/chat/message   - Submit user query, retrieve grounded DB facts, return response + citations
  GET  /api/chat/history   - Retrieve message thread history for a session
  GET  /api/chat/sessions  - List active chat sessions
  DELETE /api/chat/session/{session_id} - Clear/delete chat session
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.session import get_db
from backend.models.chat import ChatSession, ChatMessage
from backend.services.chat_service import chat_service

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    session_id: int
    role: str
    message: str
    intent: str
    citations: List[Dict[str, Any]]
    created_at: Optional[str] = None


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    summary="Submit query to AI Decision Assistant",
    description="Processes query through database-grounded RAG engine and returns synthesized response with data citations."
)
def send_message(payload: ChatMessageRequest, db: Session = Depends(get_db)):
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        result = chat_service.process_chat_message(
            db=db,
            user_query=payload.message.strip(),
            session_id=payload.session_id,
            user_id=None
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating assistant response: {str(e)}"
        )


@router.get("/history", summary="Get Chat Session History")
def get_chat_history(
    session_id: int = Query(..., description="Chat session ID"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    history = chat_service.get_history(db=db, session_id=session_id, limit=limit)
    return {
        "session_id": session_id,
        "title": session.title,
        "total_messages": len(history),
        "messages": history
    }


@router.get("/sessions", summary="List All Chat Sessions")
def list_chat_sessions(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    sessions = db.query(ChatSession).order_by(desc(ChatSession.updated_at)).limit(limit).all()
    return {
        "total": len(sessions),
        "sessions": [
            {
                "id": s.id,
                "title": s.title,
                "created_at": str(s.created_at),
                "updated_at": str(s.updated_at),
            }
            for s in sessions
        ]
    }


@router.delete("/session/{session_id}", summary="Delete Chat Session")
def delete_chat_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    db.delete(session)
    db.commit()
    return {
        "status": "success",
        "message": f"Chat session {session_id} deleted."
    }
