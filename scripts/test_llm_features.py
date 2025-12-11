from adqlm.llm import LLMClient
import os

def test_features():
    print("Testing LLM Features...")
    # Mock behavior if no key (though we expect key in environment)
    # But for a real test we need the key.
    if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ:
         print("Skipping LLM tests due to missing key.")
         return

    client = LLMClient()
    
    # 1. Test Refinement
    bad_query = "count starrs in gaia_dr2"
    print(f"\nOriginal: {bad_query}")
    refined = client.refine_query(bad_query)
    print(f"Refined: {refined}")
    
    # 2. Test Anti-Hallucination (Mock Context)
    print("\nTesting Hallucination Check...")
    # Provide no context and ask for obscure table
    res = client.generate_query("Select info from super_secret_table", [])
    print(f"Result (Should be Error): {res}")

if __name__ == "__main__":
    test_features()
