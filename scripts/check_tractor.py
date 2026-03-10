from adqlm.client import AdqlmAssistant

def check_tractor_docs():
    assistant = AdqlmAssistant()
    # We want to see if ls_dr9.tractor is in the schema docs and has the 'type' column description.
    
    # Reload the docs manually to inspect
    import json
    with open('schema_docs.json', 'r') as f:
        docs = json.load(f)
        
    found = False
    for doc in docs:
        if "ls_dr9.tractor" in doc.get('source', ''):
             print(f"Found Tractor Doc: {doc['source']}")
             print(doc['text'][:500] + "...")
             found = True
             break
    
    if not found:
        print("Tractor table NOT found in schema docs.")

if __name__ == "__main__":
    check_tractor_docs()
