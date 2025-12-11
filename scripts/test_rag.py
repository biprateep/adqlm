from adqlm.client import AdqlmAssistant
import os

def test_rag():
    print("Initializing Assistant...")
    # Mock LLM key if not present, just for RAG testing we don't need real LLM
    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = "fake_key"
        
    assistant = AdqlmAssistant()
    assistant.ingest_docs()
    
    query = "Find objects within radius of 1 degree using radial query"
    print(f"\nQuerying: {query}")
    
    docs = assistant.rag.retrieve(query, top_k=5)
    
    found_q3c = False
    print("\nRetrieved Documents:")
    for doc in docs:
        print(f"- Source: {doc['source']}")
        print(f"  Text snippet: {doc['text'][:100]}...")
        if "q3c" in doc['text'].lower() or "q3c" in doc['source'].lower():
            found_q3c = True
            
    if found_q3c:
        print("\nSUCCESS: Q3C documentation was retrieved!")
    else:
        print("\nFAILURE: Q3C documentation was NOT retrieved.")

if __name__ == "__main__":
    test_rag()
