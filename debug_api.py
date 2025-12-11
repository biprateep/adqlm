import os
from google import genai
from adqlm.llm import LLMClient

def test_api():
    # Prefer GEMINI_API_KEY
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY (or GOOGLE_API_KEY) not set")
        return

    print(f"Testing with API Key: {api_key[:5]}...")

    try:
        # Test 1: Direct GenAI usage (New SDK)
        print("Test 1: Direct GenAI usage (New SDK)...")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents="Say 'Hello World'"
        )
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"Test 1 Failed: {e}")

    try:
        # Test 2: RAG + LLM Integration
        print("\nTest 2: RAG + LLM Integration...")
        from adqlm.client import AdqlmAssistant
        
        # Test loading the new schema DB
        assistant = AdqlmAssistant(google_api_key=api_key)
        # Manually trigger ingest which should pick up the file
        assistant.ingest_docs()
        
        # Query about a specific table known to be in the DB
        q = "Show me the top 10 brightest stars from the Buzzard survey main table"
        print(f"Query: {q}")
        result = assistant.process_query(q)
        
        print("\nResult:")
        print(f"SQL: {result['sql']}")
        print(f"Explanation: {result['explanation'][:100]}...") # Truncate for brevity
        
    except Exception as e:
        print(f"Test 2 Failed: {e}")

if __name__ == "__main__":
    test_api()
