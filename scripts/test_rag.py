from adqlm.client import ADQLMAssistant
from adqlm.rag import DocumentEmbedder
import os
import json

def run_test():
    test_file = 'test_schema_docs.json'
    dummy_schema = [
        {"text": "Table: desi_dr1.quasars\nDescription: Quasar catalog\nColumns:\n- z (real): Redshift\n- ra (double): Right ascension\n- dec (double): Declination", "source": "tap_schema: desi_dr1.quasars"}
    ]
    with open(test_file, 'w') as f:
        json.dump(dummy_schema, f)
        
    embedder = DocumentEmbedder()
    
    # Mock the actual _embed call so it doesn't need an API key
    import numpy as np
    def mock_embed(texts):
        # Return random embeddings
        return np.random.rand(len(texts), 768)

    embedder._embed = mock_embed

    embedder.load_json_docs(test_file)

    assert len(embedder.documents) == 1, "Should have loaded 1 document"
    assert embedder.documents[0].startswith("Table: desi_dr1.quasars")
    print("RAG local ingestion check passed.")
    
    results = embedder.retrieve("highest redshift quasars in DESI DR1", top_k=1)
    assert len(results) == 1, "Should retrieve 1 result"
    assert results[0]['source'] == "tap_schema: desi_dr1.quasars"
    print("RAG retrieval check passed.")
    
    # Clean up test file so it doesn't leave artifacts
    if os.path.exists(test_file):
        os.remove(test_file)

run_test()
