from backend.rag.embeddings import create_embeddings
from backend.rag.vector_store import search


def retrieve_context(
    question: str,
    n_results: int = 3,
    distance_threshold: float = 1.15
):
    """
    Retrieve relevant document chunks together with metadata.

    Only documents whose Chroma distance is <= distance_threshold
    are returned.
    """

    if not question or not question.strip():
        return []

    query_embedding = create_embeddings(
        [question]
    )[0]

    results = search(
        query_embedding,
        n_results=n_results
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    retrieved = []

    for i, document in enumerate(documents):

        if not document:
            continue

        metadata = (
            metadatas[i]
            if i < len(metadatas)
            and metadatas[i] is not None
            else {}
        )

        distance = (
            distances[i]
            if i < len(distances)
            else None
        )

        # Do not use results with no distance.
        if distance is None:
            continue

        # Distance threshold prevents unrelated documents
        # from being treated as valid RAG context.
        if distance > distance_threshold:
            continue

        retrieved.append({
            "text": document,
            "source": metadata.get(
                "source",
                "unknown"
            ),
            "page": metadata.get(
                "page",
                None
            ),
            "distance": distance
        })

    return retrieved


def has_relevant_context(
    documents,
    max_distance: float = 1.15
):
    """
    Check whether at least one retrieved document is
    relevant enough to use as RAG context.

    This is useful when retrieve_context is changed or
    called independently.
    """

    if not documents:
        return False

    for document in documents:

        distance = document.get(
            "distance"
        )

        if (
            distance is not None
            and distance <= max_distance
        ):
            return True

    return False


def build_context(documents):
    """
    Combine retrieved documents into a context string
    while preserving source and page information.
    """

    context_parts = []

    for i, document in enumerate(documents):

        source = document.get(
            "source",
            "unknown"
        )

        page = document.get(
            "page"
        )

        text = document.get(
            "text",
            ""
        )

        if page is not None and page != -1:

            source_info = (
                f"Source: {source}, "
                f"Page: {page}"
            )

        else:

            source_info = (
                f"Source: {source}"
            )

        context_parts.append(
            f"[Source {i + 1}]\n"
            f"{source_info}\n"
            f"{text}"
        )

    return "\n\n".join(
        context_parts
    )


def create_rag_prompt(
    question: str,
    context: str
):
    """
    Create a document-grounded prompt for Qwen.
    """

    return f"""
You are a helpful AI assistant.

Answer the user's question using ONLY the provided document context.

Rules:
- Use the document context when answering.
- Do not use outside knowledge for document-based questions.
- Do not invent information.
- If the answer cannot be found in the provided context, say:
  "The information is not available in the provided documents."
- Explain the answer clearly and include the important details supported by the context.
- Keep the answer relevant to the user's question.

Document context:

{context}

Question:

{question}

Answer:
""".strip()
