from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    BackgroundTasks
)

from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

import requests
import json
import os
import shutil
import re

from backend.database import SessionLocal
from backend.models import Conversation, Message

# RAG
from backend.rag.rag_pipeline import (
    retrieve_context,
    build_context,
    create_rag_prompt,
    has_relevant_context
)

# Document ingestion
from backend.rag.ingest import ingest_document


app = FastAPI(
    title="Local AI Chatbot"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"


# ============================================================
# Paths
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DOCUMENTS_DIR = os.path.join(
    BASE_DIR,
    "documents"
)

os.makedirs(
    DOCUMENTS_DIR,
    exist_ok=True
)


# ============================================================
# Configuration
# ============================================================

RAG_DISTANCE_THRESHOLD = 1.15


# ============================================================
# Database dependency
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# Request models
# ============================================================

class ConversationRequest(BaseModel):

    title: str | None = None


class ChatRequest(BaseModel):

    conversation_id: int
    message: str


# ============================================================
# Conversation helpers
# ============================================================

def build_conversation_history(
    messages,
    current_message_id=None
):
    """
    Build previous conversation history.

    The current user message is excluded because it is already
    provided separately as the current question.
    """

    history_parts = []

    for message in messages:

        if (
            current_message_id is not None
            and message.id == current_message_id
        ):
            continue

        if message.role == "user":

            history_parts.append(
                f"User: {message.content}"
            )

        elif message.role == "assistant":

            history_parts.append(
                f"Assistant: {message.content}"
            )

    return "\n".join(
        history_parts
    )


def is_conversation_question(
    message: str
):
    """
    Detect questions that mainly depend on previous
    conversation context.

    This is intentionally limited to generic follow-up/
    conversation requests. Specific topics such as
    'shorter version of self-attention' still go through RAG.
    """

    text = message.lower().strip()

    patterns = [

        # Asking about previous conversation
        r"\bwhat did i just ask\b",
        r"\bwhat did i ask\b",
        r"\bwhat was my last question\b",
        r"\bwhat was my previous question\b",
        r"\bwhat did i say\b",
        r"\bwhat did we talk about\b",
        r"\bwhat are we talking about\b",

        # Generic follow-up
        r"\bexplain that again\b",
        r"\bexplain it again\b",
        r"\btell me more about that\b",
        r"\btell me more about it\b",
        r"\bgive me a shorter version\b",
        r"\bmake it shorter\b",
        r"\bsummarize that\b",
        r"\bsummarize it\b",
        r"\bshorten that\b",
        r"\bshorten it\b",
    ]

    return any(
        re.search(
            pattern,
            text
        )
        for pattern in patterns
    )


def is_last_question_request(
    message: str
):
    """
    Detect requests asking specifically for the last
    user question.
    """

    text = message.lower().strip()

    patterns = [
        r"^what did i just ask\??$",
        r"^what did i ask\??$",
        r"^what was my last question\??$",
        r"^what was my previous question\??$",
    ]

    return any(
        re.match(
            pattern,
            text
        )
        for pattern in patterns
    )


def get_last_user_question(
    messages,
    current_message_id
):
    """
    Find the previous user question, excluding the
    current message.
    """

    for message in reversed(messages):

        if message.id == current_message_id:
            continue

        if message.role == "user":

            return message.content

    return None


def save_assistant_message(
    db,
    conversation_id,
    content
):
    """
    Save an assistant response to the database.
    """

    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=content
    )

    db.add(
        assistant_message
    )

    db.commit()


def immediate_response(
    db,
    conversation_id,
    content
):
    """
    Return a non-streamed response while also saving it.
    """

    save_assistant_message(
        db,
        conversation_id,
        content
    )

    return StreamingResponse(
        iter([content]),
        media_type="text/plain"
    )


# ============================================================
# Basic endpoints
# ============================================================

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


# ============================================================
# Document upload
# ============================================================

def run_ingestion(
    file_path: str
):
    """
    Run document ingestion in the background.
    """

    try:

        print(
            f"\nStarting background ingestion: "
            f"{file_path}"
        )

        ingest_document(
            file_path
        )

        print(
            f"\nBackground ingestion completed: "
            f"{file_path}"
        )

    except Exception as e:

        print(
            f"\nBackground ingestion failed: "
            f"{file_path}"
        )

        print(
            f"Error: {e}"
        )


@app.post("/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )


    # --------------------------------------------------------
    # Only allow PDF for now
    # --------------------------------------------------------

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )


    # --------------------------------------------------------
    # Save uploaded file
    # --------------------------------------------------------

    filename = os.path.basename(
        file.filename
    )

    file_path = os.path.join(
        DOCUMENTS_DIR,
        filename
    )

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )


    # --------------------------------------------------------
    # Start background ingestion
    # --------------------------------------------------------

    background_tasks.add_task(
        run_ingestion,
        file_path
    )


    # --------------------------------------------------------
    # Return immediately
    # --------------------------------------------------------

    return {
        "message": "Document uploaded successfully",
        "filename": filename,
        "status": "processing"
    }


# ============================================================
# Create conversation
# ============================================================

@app.post("/conversations")
def create_conversation(
    request: ConversationRequest,
    db: Session = Depends(get_db)
):

    conversation = Conversation(
        title=request.title or "New conversation"
    )

    db.add(
        conversation
    )

    db.commit()

    db.refresh(
        conversation
    )

    return {
        "id": conversation.id,
        "title": conversation.title
    }

# ============================================================
# Get all conversations
# ============================================================

@app.get("/conversations")
def get_conversations(
    db: Session = Depends(get_db)
):

    conversations = db.query(
        Conversation
    ).order_by(
        Conversation.id.desc()
    ).all()

    return [
        {
            "id": conversation.id,
            "title": conversation.title
        }
        for conversation in conversations
    ]
    
# ============================================================
# Get conversation
# ============================================================

@app.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    conversation = db.query(
        Conversation
    ).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )


    messages = db.query(
        Message
    ).filter(
        Message.conversation_id == conversation.id
    ).order_by(
        Message.id
    ).all()


    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [

            {
                "id": message.id,
                "role": message.role,
                "content": message.content
            }

            for message in messages
        ]
    }


# ============================================================
# Delete conversation
# ============================================================

@app.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    conversation = db.query(
        Conversation
    ).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )


    # Delete messages belonging to conversation

    db.query(
        Message
    ).filter(
        Message.conversation_id == conversation.id
    ).delete(
        synchronize_session=False
    )


    # Delete conversation

    db.delete(
        conversation
    )

    db.commit()


    return {
        "message": "Conversation deleted successfully",
        "conversation_id": conversation_id
    }


# ============================================================
# Chat
# ============================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Find conversation
    # --------------------------------------------------------

    conversation = db.query(
        Conversation
    ).filter(
        Conversation.id == request.conversation_id
    ).first()

    if not conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )


    # --------------------------------------------------------
    # 2. Save user message
    # --------------------------------------------------------

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )

    db.add(
        user_message
    )

    db.commit()


    # --------------------------------------------------------
    # 3. Load conversation history
    # --------------------------------------------------------

    messages = db.query(
        Message
    ).filter(
        Message.conversation_id == conversation.id
    ).order_by(
        Message.id
    ).all()


    conversation_history = build_conversation_history(
        messages,
        current_message_id=user_message.id
    )


    # --------------------------------------------------------
    # 4. Handle direct conversation-memory questions
    # --------------------------------------------------------

    if is_last_question_request(
        request.message
    ):

        last_question = get_last_user_question(
            messages,
            current_message_id=user_message.id
        )

        if last_question:

            answer = (
                f'You just asked: "{last_question}"'
            )

        else:

            answer = (
                "There is no previous question "
                "in this conversation."
            )

        return immediate_response(
            db,
            conversation.id,
            answer
        )


    # --------------------------------------------------------
    # 5. Determine whether this is a conversation follow-up
    # --------------------------------------------------------

    conversation_question = is_conversation_question(
        request.message
    )


    # --------------------------------------------------------
    # 6. Retrieve relevant documents
    # --------------------------------------------------------

    documents = []
    context = ""

    if not conversation_question:

        try:

            documents = retrieve_context(
                request.message,
                n_results=3,
                distance_threshold=RAG_DISTANCE_THRESHOLD
            )

            if has_relevant_context(
                documents,
                max_distance=RAG_DISTANCE_THRESHOLD
            ):

                context = build_context(
                    documents
                )

            else:

                documents = []
                context = ""

        except Exception as e:

            print(
                f"RAG retrieval error: {e}"
            )

            documents = []
            context = ""


        # ----------------------------------------------------
        # IMPORTANT:
        # Do not allow Qwen to answer factual questions
        # from its own knowledge when no relevant document
        # was retrieved.
        # ----------------------------------------------------

        if not context:

            return immediate_response(
                db,
                conversation.id,
                "The information is not available "
                "in the provided documents."
            )


    # --------------------------------------------------------
    # 7. Build prompt
    # --------------------------------------------------------

    if conversation_question:

        prompt = f"""
You are a helpful AI assistant.

This is a conversation follow-up question.

Use the previous conversation to understand what
the user is referring to.

Rules:
- Use the previous conversation when answering.
- Resolve references such as "that", "it", "again",
  and "shorter version" using the conversation history.
- Do not invent previous questions or answers.
- Answer naturally and directly.

Previous conversation:

{conversation_history}

Current user question:

{request.message}

Answer:
""".strip()

    else:

        prompt = create_rag_prompt(
            request.message,
            context
        )


    # --------------------------------------------------------
    # 8. Prepare sources
    # --------------------------------------------------------

    sources = []

    for document in documents:

        source = document.get(
            "source"
        )

        page = document.get(
            "page"
        )

        if (
            not source
            or source == "unknown"
        ):
            continue

        source_item = {
            "source": source
        }

        if (
            page is not None
            and page != -1
        ):

            source_item["page"] = page

        sources.append(
            source_item
        )


    # --------------------------------------------------------
    # Remove duplicate sources
    # --------------------------------------------------------

    unique_sources = []

    seen = set()

    for source in sources:

        key = (
            source.get("source"),
            source.get("page")
        )

        if key not in seen:

            seen.add(
                key
            )

            unique_sources.append(
                source
            )


    sources = unique_sources


    # --------------------------------------------------------
    # 9. Generate response
    # --------------------------------------------------------

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
                stream=True,
                timeout=300
            )

            response.raise_for_status()


            # ------------------------------------------------
            # Stream Qwen response
            # ------------------------------------------------

            for line in response.iter_lines():

                if not line:
                    continue

                data = json.loads(
                    line
                )

                token = data.get(
                    "response",
                    ""
                )

                if token:

                    full_response += token

                    yield token


                if data.get(
                    "done"
                ):

                    break


            # ------------------------------------------------
            # Save assistant response
            # ------------------------------------------------

            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response
            )

            db.add(
                assistant_message
            )

            db.commit()


            # ------------------------------------------------
            # Send sources at the end
            # ------------------------------------------------

            if sources:

                yield "\n\n[SOURCES]\n"

                for source in sources:

                    source_name = source.get(
                        "source",
                        "unknown"
                    )

                    page = source.get(
                        "page"
                    )

                    if page is not None:

                        yield (
                            f"- {source_name} "
                            f"(Page {page})\n"
                        )

                    else:

                        yield (
                            f"- {source_name}\n"
                        )


        except Exception as e:

            db.rollback()

            yield (
                f"\n[Error: {str(e)}]"
            )


    # --------------------------------------------------------
    # Return streaming response
    # --------------------------------------------------------

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )
