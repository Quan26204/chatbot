from loader import load_pdf
from chunker import chunk_text
from embeddings import create_embeddings
from vector_store import add_documents, search


# =====================================
# 1. Load PDF
# =====================================

pdf_path = "../documents/attention.pdf"

text = load_pdf(pdf_path)

print(f"Loaded {len(text)} characters.")


# =====================================
# 2. Chunk
# =====================================

chunks = chunk_text(
    text,
    chunk_size=1000,
    overlap=200
)

print(f"Created {len(chunks)} chunks.")


# =====================================
# 3. Create embeddings
# =====================================

embeddings = create_embeddings(chunks)

print("Embeddings created.")


# =====================================
# 4. Store in ChromaDB
# =====================================

add_documents(
    chunks,
    embeddings
)

print("Documents stored in ChromaDB.")


# =====================================
# 5. Test semantic search
# =====================================

query = "What is self-attention?"

print("\n")
print("=" * 60)
print("SEARCH")
print("=" * 60)

print(f"Query: {query}")


query_embedding = create_embeddings(
    [query]
)[0]


results = search(
    query_embedding,
    n_results=3
)


# =====================================
# 6. Display results
# =====================================

print("\nTop results:")

for i, document in enumerate(
    results["documents"][0]
):

    print("\n")
    print("-" * 60)
    print(f"RESULT {i + 1}")
    print("-" * 60)

    print(document)