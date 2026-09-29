from loader import load_pdf
from chunker import chunk_text


pdf_path = "../documents/attention.pdf"

text = load_pdf(pdf_path)

chunks = chunk_text(
    text,
    chunk_size=1000,
    overlap=200
)


print("=" * 60)
print("CHUNKING TEST")
print("=" * 60)

print(f"Total characters: {len(text)}")
print(f"Total chunks: {len(chunks)}")


for i, chunk in enumerate(chunks[:3]):

    print("\n")
    print("-" * 60)
    print(f"CHUNK {i + 1}")
    print("-" * 60)

    print(chunk[:1000])