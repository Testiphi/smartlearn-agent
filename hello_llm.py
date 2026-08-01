# hello_llm.py
import os
from dotenv import load_dotenv
import openai

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise SystemExit("OPENROUTER_API_KEY is missing. Add it to .env and try again.")

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

response = client.chat.completions.create(
    model="qwen/qwen3.5-flash-02-23",
    messages=[
        {"role": "system", "content": "You are a pirate. Answer everything in pirate speak."},
        {"role": "user", "content": "What is Python in 2 sentences?"}
    ],
)

print(response.choices[0].message.content)

# Inspect response details and token usage
print("\n--- Details ---")
print(f"Model: {response.model}")
print(f"Prompt tokens:     {response.usage.prompt_tokens}")
print(f"Completion tokens: {response.usage.completion_tokens}")
print(f"Total tokens:      {response.usage.total_tokens}")
