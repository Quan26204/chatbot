from loader import load_pdf
from chunker import chunk_text
from embeddings import create_embeddings


pdf_path = "../documents/attention.pdf"


# Load PDF
text = load_pdf(pdf_path)

print(f"Loaded {len(text)} characters.")


# Create chunks
chunks = chunk_text(
    text,
    chunk_size=1000,
    overlap=200
)

print(f"Created {len(chunks)} chunks.")


# Create embeddings
embeddings = create_embeddings(chunks)


print("\n")
print("=" * 60)
print("EMBEDDING TEST")
print("=" * 60)

print(f"Number of embeddings: {len(embeddings)}")
print(f"Embedding dimensions: {len(embeddings[0])}")

print("\nFirst embedding:")
print(embeddings[0][:10])