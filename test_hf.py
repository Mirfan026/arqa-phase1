"""
ARQA Phase 1 — Day 2
Hello-HuggingFace script: first AI call from the project.

Goal: prove that we can talk to a HuggingFace-hosted model
using our token, and print its response in the terminal.

Author: Muhammad Irfan
"""

import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient


# Load HF_TOKEN from .env into the environment
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Safety check: refuse to continue if the token is missing
if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN not found in .env. "
        "Make sure your .env file exists in D:\\arqa-phase1\\ "
        "and contains a line like: HF_TOKEN=hf_..."
    )

print("✓ Token loaded successfully (length:", len(HF_TOKEN), "chars)")


# Create the HuggingFace Inference client
# This is the gateway through which all our model calls flow
client = InferenceClient(token=HF_TOKEN)

print("✓ InferenceClient created")


# Our test prompt — a question relevant to ARQA's domain
prompt = "List 3 rooms a Saudi villa typically has that a US house does not. Be brief."

print("\n--- Prompt ---")
print(prompt)
print("\n--- AI Response ---")

# Call a HuggingFace model
# Phase 1 uses Qwen2.5-7B-Instruct — small, free, multilingual
response = client.chat_completion(
    messages=[{"role": "user", "content": prompt}],
    model="Qwen/Qwen2.5-7B-Instruct",
    max_tokens=200,
)

# Extract the actual text from the response object
answer = response.choices[0].message.content
print(answer)

print("\n✓ Day 2 first AI call: success")