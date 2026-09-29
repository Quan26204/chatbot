import os
import chromadb


# ============================================================
# ChromaDB path
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

CHROMA_PATH = os.path.join(
    BASE_DIR,
    "chroma_db"
)

print(f"ChromaDB path: {CHROMA_PATH}")


client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


collection = client.get_or_create_collection(
    name="documents"
)


# ============================================================
# Add documents
# ============================================================

def add_documents(
    chunks,
    embeddings,
    source_name=None
):
    """
    Store document chunks and embeddings in ChromaDB.

    Each chunk stores:
        - source
        - page
    """

    if not chunks:
        print("No chunks to add.")
        return

    if source_name:
        # ----------------------------------------------------
        # Remove old chunks from this source
        # ----------------------------------------------------

        existing = collection.get(
            where={
                "source": source_name
            }
        )

        existing_ids = existing.get(
            "ids",
            []
        )

        if existing_ids:

            print(
                f"Removing {len(existing_ids)} "
                f"old chunks from {source_name}..."
            )

            collection.delete(
                ids=existing_ids
            )

    # --------------------------------------------------------
    # Create unique IDs
    # --------------------------------------------------------

    existing_count = collection.count()

    ids = [
        f"chunk_{existing_count + i}"
        for i in range(len(chunks))
    ]

    # --------------------------------------------------------
    # Create metadata
    # --------------------------------------------------------

    metadatas = []

    for chunk in chunks:

        if isinstance(chunk, dict):

            page = chunk.get(
                "page"
            )

        else:

            page = None

        metadatas.append({
            "source": source_name or "unknown",
            "page": page if page is not None else -1
        })

    # --------------------------------------------------------
    # Extract text
    # --------------------------------------------------------

    documents = []

    for chunk in chunks:

        if isinstance(chunk, dict):

            documents.append(
                chunk.get(
                    "text",
                    ""
                )
            )

        else:

            documents.append(
                chunk
            )

    # --------------------------------------------------------
    # Add to ChromaDB
    # --------------------------------------------------------

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

    print(
        f"Added {len(documents)} new chunks "
        f"from {source_name}."
    )


# ============================================================
# Search
# ============================================================

def search(
    query_embedding,
    n_results=3
):
    """
    Search for the most relevant chunks.
    """

    results = collection.query(
        query_embeddings=[
            query_embedding.tolist()
        ],
        n_results=n_results
    )

    return results