import os
from google import genai

def list_models():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY or GEMINI_API_KEY not set.")
        return

    client = genai.Client(api_key=api_key)
    try:
        models = client.models.list()
        print("Available Models:")
        for m in models:
            print(f"- {m.name}")
            # print(dir(m)) # Uncomment to debug if needed
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
