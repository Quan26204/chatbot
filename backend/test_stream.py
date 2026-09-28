import requests

url = "http://127.0.0.1:8000/chat"

data = {
    "conversation_id": 1,
    "message": "Explain what a neural network is in simple terms."
}

with requests.post(url, json=data, stream=True) as response:

    response.raise_for_status()

    for chunk in response.iter_content(
        chunk_size=None,
        decode_unicode=True
    ):

        if chunk:
            print(chunk, end="", flush=True)