def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
):
    """
    Split text into overlapping chunks.

    chunk_size:
        Maximum number of characters per chunk.

    overlap:
        Number of characters shared between consecutive chunks.
    """

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def chunk_pages(
    pages,
    chunk_size: int = 1000,
    overlap: int = 200
):
    """
    Split PDF pages into overlapping chunks
    while preserving the page number.

    pages:
        [
            {
                "text": "...",
                "page": 1
            },
            ...
        ]

    Returns:
        [
            {
                "text": "...",
                "page": 1
            },
            ...
        ]
    """

    chunks = []

    for page_data in pages:

        text = page_data["text"]
        page_number = page_data["page"]

        page_chunks = chunk_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk in page_chunks:

            chunks.append({
                "text": chunk,
                "page": page_number
            })

    return chunks