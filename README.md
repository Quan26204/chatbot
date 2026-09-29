# Local AI Chatbot

A local AI chatbot built with **React**, **FastAPI**, **Ollama**, and **Qwen3 8B**.

The application supports conversation history, Retrieval-Augmented Generation (RAG), PDF uploads with background ingestion, semantic document search, and source/page citations.

## Features

- Local AI chat using **Qwen3 8B**
- Conversation management
  - Create conversations
  - Load previous conversations
  - Delete conversations
  - Store message history
- RAG-based document question answering
- PDF document upload
- Automatic background document ingestion
- Semantic search with **ChromaDB**
- Text embeddings with **all-MiniLM-L6-v2**
- Source and page references
- Streaming AI responses
- React + Vite frontend
- FastAPI backend

## Architecture

```text
                    React Frontend
                          |
                          | HTTP
                          v
                    FastAPI Backend
                     /          \
                    /            \
                   v              v
             SQLite DB       RAG Pipeline
           Conversations          |
             Messages             v
                            MiniLM Embeddings
                                  |
                                  v
                              ChromaDB
                                  |
                                  v
                         Relevant Documents
                                  |
                                  v
                         Ollama / Qwen3 8B
                                  |
                                  v
                             AI Response
```

## Project Structure

```text
ai-chatbot/
|
+-- backend/
|   +-- main.py
|   +-- database.py
|   +-- models.py
|   |
|   +-- rag/
|       +-- loader.py
|       +-- chunker.py
|       +-- embeddings.py
|       +-- vector_store.py
|       +-- rag_pipeline.py
|       +-- ingest.py
|
+-- frontend/
|   +-- src/
|   |   +-- App.jsx
|   |   +-- App.css
|   |   +-- ...
|   +-- package.json
|
+-- documents/
+-- chroma_db/
+-- chatbot.db
+-- requirements.txt
+-- .gitignore
```

## Requirements

### Backend

- Python 3.12+
- Ollama
- Qwen3 8B
- Git

### Frontend

- Node.js
- npm

## Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd ai-chatbot
```

### 2. Set up the backend

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

If FastAPI reports that multipart form support is missing:

```powershell
pip install python-multipart
```

### 3. Install Qwen3 8B with Ollama

Install Ollama, then run:

```powershell
ollama pull qwen3:8b
```

Check the installed model:

```powershell
ollama list
```

The backend expects Ollama at:

```text
http://localhost:11434
```

### 4. Start the backend

From the project root:

```powershell
python -m uvicorn backend.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

### 5. Start the frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite normally runs at:

```text
http://localhost:5173
```

Open that address in your browser.

## RAG Pipeline

Documents are processed through:

```text
PDF
 |
 v
PDF Loader
 |
 v
Text Chunks
 |
 v
all-MiniLM-L6-v2
 |
 v
Embeddings
 |
 v
ChromaDB
```

When the user asks a question:

```text
User Question
     |
     v
Question Embedding
     |
     v
ChromaDB Similarity Search
     |
     v
Relevant Document Chunks
     |
     v
Context + Conversation History
     |
     v
Qwen3 8B
     |
     v
Answer + Sources
```

## PDF Upload

PDF documents can be uploaded directly from the frontend using the attachment button next to the chat input.

The process is:

```text
Select PDF
    |
    v
POST /documents/upload
    |
    v
Save PDF
    |
    v
Background ingestion
    |
    +-- Load PDF
    +-- Create chunks
    +-- Generate embeddings
    +-- Store in ChromaDB
```

The document can then be used by the RAG system.

## API Endpoints

### Health

```http
GET /
GET /health
```

### Conversations

Create:

```http
POST /conversations
```

List:

```http
GET /conversations
```

Get one:

```http
GET /conversations/{conversation_id}
```

Delete:

```http
DELETE /conversations/{conversation_id}
```

### Chat

```http
POST /chat
```

Example:

```json
{
  "conversation_id": 1,
  "message": "What is self-attention?"
}
```

The response is streamed from the backend.

### Documents

```http
POST /documents/upload
```

Accepts PDF files and starts background ingestion.

## Example

After uploading `attention.pdf`, ask:

```text
What is self-attention?
```

The RAG system searches ChromaDB for relevant chunks and provides them to Qwen3 8B.

A response can include:

```text
[SOURCES]

- attention.pdf (Page 2)
- attention.pdf (Page 3)
```

## Conversation Context

Messages are stored in SQLite, allowing contextual questions such as:

```text
User:
Explain transformers.

Assistant:
...

User:
Give me the shorter version.
```

The chatbot can use the previous conversation to understand the second question.

## Important Files

### `backend/main.py`

Main FastAPI application responsible for:

- API endpoints
- Conversation management
- Chat requests
- Conversation history
- Document upload
- Streaming Qwen responses

### `backend/rag/rag_pipeline.py`

Handles:

- Document retrieval
- Context construction
- RAG prompt creation

### `backend/rag/ingest.py`

Handles:

- PDF loading
- Chunking
- Embedding generation
- ChromaDB storage

### `backend/rag/vector_store.py`

Handles ChromaDB:

- Adding documents
- Removing old chunks for re-uploaded documents
- Similarity search

### `backend/rag/embeddings.py`

Creates embeddings using:

```text
all-MiniLM-L6-v2
```

### `backend/rag/loader.py`

Loads text from PDF documents.

### `backend/rag/chunker.py`

Splits documents into chunks for retrieval.

## Data Storage

### SQLite

Stores:

- Conversations
- Messages

### ChromaDB

Stores:

- Document chunks
- Embeddings
- Source metadata
- Page numbers

## Git / Files to Ignore

Do not commit local/generated data such as:

```text
.venv/
chroma_db/
node_modules/
*.db
documents/
uploads/
.env
```

Add these to `.gitignore`.

## Troubleshooting

### `npm` is not recognized

Install Node.js and restart PowerShell.

Check:

```powershell
node --version
npm --version
```

### `GET /conversations` returns 405

Make sure the backend contains:

```python
@app.get("/conversations")
```

Then restart Uvicorn.

### `python-multipart` error

Run:

```powershell
pip install python-multipart
```

### Ollama connection error

Check:

```powershell
ollama list
```

If necessary:

```powershell
ollama pull qwen3:8b
```

### RAG returns no useful results

Check that:

1. The PDF was uploaded successfully.
2. Background ingestion completed.
3. The document was added to ChromaDB.
4. The embedding model loaded successfully.

## Future Improvements

- Document management UI
- Ingestion progress/status
- Additional document formats
- Improved chunking strategies
- RAG relevance filtering
- Automatic conversation titles
- Authentication
- Multi-user support
- Markdown rendering
- Improved source citation
- Docker deployment
- Production deployment

## License

This project is for educational and development purposes.
