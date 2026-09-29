from backend.rag.rag_pipeline import (
    retrieve_context,
    build_context,
    create_rag_prompt
)


question = "What is self-attention?"


print("=" * 60)
print("FULL RAG PIPELINE TEST")
print("=" * 60)

print(f"\nQuestion:\n{question}")


# ============================================================
# 1. Retrieve relevant chunks
# ============================================================

documents = retrieve_context(
    question,
    n_results=3
)


print("\nRetrieved documents:")

for i, document in enumerate(documents):

    print("\n")
    print("-" * 60)
    print(f"SOURCE {i + 1}")
    print("-" * 60)

    print(
        f"Source: {document.get('source', 'unknown')}"
    )

    print(
        f"Page: {document.get('page', 'unknown')}"
    )

    print(
        f"Distance: {document.get('distance', 'unknown')}"
    )

    print("\nContent:")
    print(
        document.get("text", "")
    )


# ============================================================
# 2. Build context
# ============================================================

context = build_context(
    documents
)


print("\n")
print("=" * 60)
print("CONTEXT")
print("=" * 60)

print(context)


# ============================================================
# 3. Create RAG prompt
# ============================================================

prompt = create_rag_prompt(
    question,
    context
)


print("\n")
print("=" * 60)
print("RAG PROMPT")
print("=" * 60)

print(prompt)