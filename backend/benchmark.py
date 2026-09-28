import requests
import time
import json
import csv
from transformers import AutoTokenizer


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3:8b"

QUESTIONS = [
    "What is machine learning? Explain it simply.",
    "What is a neural network?",
    "Explain the Transformer architecture in simple terms.",
    "What is the difference between AI and machine learning?",
    "What is REST API?",
]

OUTPUT_FILE = "benchmark_results.csv"


print("Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen3-8B"
)

print("Tokenizer loaded.\n")


def run_test(question, thinking):
    payload = {
        "model": MODEL,
        "prompt": question,
        "stream": True,
        "think": thinking
    }

    start_time = time.perf_counter()

    first_token_time = None
    end_time = None
    full_response = ""

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        stream=True,
        timeout=300
    )

    response.raise_for_status()

    for line in response.iter_lines():

        if not line:
            continue

        data = json.loads(line)

        token = data.get("response", "")

        if token:

            if first_token_time is None:
                first_token_time = time.perf_counter()

            full_response += token

        if data.get("done"):
            end_time = time.perf_counter()
            break

    if first_token_time is None:
        raise RuntimeError("No tokens received")

    if end_time is None:
        end_time = time.perf_counter()

    ttft = first_token_time - start_time
    total_latency = end_time - start_time

    token_count = len(
        tokenizer.encode(
            full_response,
            add_special_tokens=False
        )
    )

    generation_time = end_time - first_token_time

    if generation_time > 0:
        tokens_per_second = token_count / generation_time
    else:
        tokens_per_second = 0

    return {
        "ttft": ttft,
        "total_latency": total_latency,
        "tokens": token_count,
        "tokens_per_second": tokens_per_second
    }


results = []


for thinking in [True, False]:

    mode_name = "ON" if thinking else "OFF"

    print("\n")
    print("=" * 60)
    print(f"THINKING {mode_name}")
    print("=" * 60)

    for i, question in enumerate(QUESTIONS, start=1):

        print(f"\nTest {i}/{len(QUESTIONS)}")
        print(f"Question: {question}")

        try:

            metrics = run_test(
                question,
                thinking
            )

            result = {
                "thinking": mode_name,
                "test": i,
                "question": question,
                **metrics
            }

            results.append(result)

            print(
                f"TTFT: {metrics['ttft']:.3f}s | "
                f"Total: {metrics['total_latency']:.3f}s | "
                f"Tokens: {metrics['tokens']} | "
                f"Speed: {metrics['tokens_per_second']:.2f} tok/s"
            )

        except Exception as e:

            print(f"ERROR: {e}")


# =====================================
# Save CSV
# =====================================

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "thinking",
            "test",
            "question",
            "ttft",
            "total_latency",
            "tokens",
            "tokens_per_second"
        ]
    )

    writer.writeheader()
    writer.writerows(results)


# =====================================
# Summary
# =====================================

print("\n")
print("=" * 60)
print("FINAL BENCHMARK")
print("=" * 60)


for mode in ["ON", "OFF"]:

    mode_results = [
        r for r in results
        if r["thinking"] == mode
    ]

    if not mode_results:
        continue

    avg_ttft = sum(
        r["ttft"]
        for r in mode_results
    ) / len(mode_results)

    avg_latency = sum(
        r["total_latency"]
        for r in mode_results
    ) / len(mode_results)

    avg_tokens = sum(
        r["tokens"]
        for r in mode_results
    ) / len(mode_results)

    avg_speed = sum(
        r["tokens_per_second"]
        for r in mode_results
    ) / len(mode_results)

    print(f"\nThinking {mode}")

    print(f"Average TTFT:       {avg_ttft:.3f}s")
    print(f"Average latency:    {avg_latency:.3f}s")
    print(f"Average tokens:     {avg_tokens:.1f}")
    print(f"Average speed:      {avg_speed:.2f} tok/s")


print("\n")
print(f"Results saved to: {OUTPUT_FILE}")