from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from src.utils.config import get_settings
import requests

settings = get_settings()
router = APIRouter(prefix="/chat", tags=["Chatbot"])


settings.N8N_WEBHOOK_URL
JWT_TOKEN = "YOUR_JWT_TOKEN"


class ChatMessage(BaseModel):
    """Request model for chat messages. Example appears in OpenAPI docs."""
    message: str = Field(..., example="hello how are you")

@router.post("/message")
async def send_message_to_n8n(payload: ChatMessage):

    user_message = payload.message
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")

    headers = {
        "Content-Type": "application/json",

    }

    try:
        response = requests.post(settings.N8N_WEBHOOK_URL, json={"message": user_message}, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"n8n error: {response.text}")

        return response.json()  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
