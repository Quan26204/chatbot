from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import requests
import json

from database import SessionLocal
from models import Conversation, Message


app = FastAPI(title="Local AI Chatbot")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"


# -------------------------
# Database dependency
# -------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# -------------------------
# Request models
# -------------------------

class ConversationRequest(BaseModel):
    title: str | None = None


class ChatRequest(BaseModel):
    conversation_id: int
    message: str


# -------------------------
# Basic endpoints
# -------------------------

@app.get("/")
def root():
    return {
        "message": "Local AI Chatbot API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# -------------------------
# Create conversation
# -------------------------

@app.post("/conversations")
def create_conversation(
    request: ConversationRequest,
    db: Session = Depends(get_db)
):

    conversation = Conversation(
        title=request.title or "New conversation"
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title
    }


# -------------------------
# Chat
# -------------------------

@app.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    conversation = db.query(Conversation).filter(
        Conversation.id == request.conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )

    db.add(user_message)
    db.commit()

    # Load conversation history
    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.id).all()

    prompt_parts = []

    for message in messages:

        if message.role == "user":
            prompt_parts.append(
                f"User: {message.content}"
            )

        elif message.role == "assistant":
            prompt_parts.append(
                f"Assistant: {message.content}"
            )

    prompt = "\n".join(prompt_parts)
    prompt += "\nAssistant:"

    def generate():

        full_response = ""

        try:

            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": True,
                    "think": False
                },
                stream=True
            )

            response.raise_for_status()

            for line in response.iter_lines():

                if not line:
                    continue

                data = json.loads(line)

                token = data.get("response", "")

                if token:
                    full_response += token
                    yield token

                if data.get("done"):
                    break

            # Save complete assistant response
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response
            )

            db.add(assistant_message)
            db.commit()

        except Exception as e:

            db.rollback()

            yield f"\n[Error: {str(e)}]"

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )