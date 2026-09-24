from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import requests
import json

app = FastAPI(title="Local AI Chatbot")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"

conversation_history = []


class ChatRequest(BaseModel):
    message: str


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


@app.post("/chat")
def chat(request: ChatRequest):

    conversation_history.append(
        f"User: {request.message}"
    )

    prompt = "\n".join(conversation_history)
    prompt += "\nAssistant:"

    def generate():

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": True
            },
            stream=True
        )

        response.raise_for_status()

        full_response = ""

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

        conversation_history.append(
            f"Assistant: {full_response}"
        )

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )