import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen3:8b"


def generate_answer(prompt: str):
    """
    Send prompt to the local Qwen model through Ollama.
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "think": False
        },
        timeout=300
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]