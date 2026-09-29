from rag_pipeline import (
    retrieve_context,
    build_context,
    create_rag_prompt
)

from llm import generate_answer


question = "What is self-attention?"


print("=" * 60)
print("RAG + QWEN TEST")
print("=" * 60)

print(f"\nQuestion:")
print(question)


# =====================================
# 1. Retrieve relevant documents
# =====================================

print("\nRetrieving relevant documents...")

documents = retrieve_context(
    question,
    n_results=3
)


# =====================================
# 2. Build context
# =====================================

context = build_context(
    documents
)


# =====================================
# 3. Create RAG prompt
# =====================================

prompt = create_rag_prompt(
    question,
    context
)


# =====================================
# 4. Send to Qwen
# =====================================

print("\nSending prompt to Qwen3...")


answer = generate_answer(
    prompt
)


# =====================================
# 5. Display answer
# =====================================

print("\n")
print("=" * 60)
print("FINAL ANSWER")
print("=" * 60)

print(answer)