from loader import load_pdf


pdf_path = "../documents/attention.pdf"

text = load_pdf(pdf_path)

print("=" * 60)
print("PDF LOADED SUCCESSFULLY")
print("=" * 60)

print(f"Characters: {len(text)}")

print("\nFirst 2000 characters:\n")

print(text[:2000])