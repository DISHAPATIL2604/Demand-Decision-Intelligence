from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.api.auth import get_current_user
from backend.services.chat_assistant import ChatAssistantService

router = APIRouter()
chat_service = ChatAssistantService()

class ChatMessageRequest(BaseModel):
    message: str
    history: List[Dict[str, Any]] = []

class ChatMessageResponse(BaseModel):
    reply: str
    citations: List[str]

class ChatSuggestionsResponse(BaseModel):
    suggestions: List[str]

@router.post("/message", response_model=ChatMessageResponse)
def send_message(
    request: ChatMessageRequest, 
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    try:
        result = chat_service.process_message(request.message, request.history, db)
        return ChatMessageResponse(
            reply=result["reply"],
            citations=result["citations"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/suggestions", response_model=ChatSuggestionsResponse)
def get_suggestions(current_user: Any = Depends(get_current_user)):
    return ChatSuggestionsResponse(suggestions=chat_service.get_suggestions())
