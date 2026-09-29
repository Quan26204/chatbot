from pathlib import Path

from backend.rag.loader import load_pdf
from backend.rag.chunker import chunk_pages
from backend.rag.embeddings import create_embeddings
from backend.rag.vector_store import add_documents


def ingest_document(pdf_path: str):

    print("=" * 60)
    print("DOCUMENT INGESTION")
    print("=" * 60)

    # ========================================================
    # 1. Load PDF
    # ========================================================

    print("\n[1/4] Loading PDF...")

    pages = load_pdf(
        pdf_path
    )

    print(
        f"Loaded {len(pages)} pages."
    )

    # ========================================================
    # 2. Chunk document
    # ========================================================

    print("\n[2/4] Creating chunks...")

    chunks = chunk_pages(
        pages,
        chunk_size=1000,
        overlap=200
    )

    print(
        f"Created {len(chunks)} chunks."
    )

    # ========================================================
    # 3. Create embeddings
    # ========================================================

    print("\n[3/4] Creating embeddings...")

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = create_embeddings(
        texts
    )

    print(
        "Embeddings created."
    )

    # ========================================================
    # 4. Store in ChromaDB
    # ========================================================

    print("\n[4/4] Storing in ChromaDB...")

    source_name = Path(
        pdf_path
    ).name

    add_documents(
        chunks,
        embeddings,
        source_name=source_name
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "INGESTION COMPLETE"
    )

    print(
        "=" * 60
    )


# ============================================================
# Command line
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "python -m backend.rag.ingest "
            "documents/example.pdf"
        )

        raise SystemExit(1)

    ingest_document(
        sys.argv[1]
    )