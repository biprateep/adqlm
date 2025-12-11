import os
import json
from web.app import app

def test_workflow():
    client = app.test_client()
    
    # 1. Test Generate
    print("Testing /generate...")
    query = "Get TOP 5 stars from Gaia source table"
    response = client.post('/generate', json={'message': query})
    data = response.get_json()
    
    if 'error' in data:
        print(f"Generate Failed: {data['error']}")
        return
        
    sql = data.get('sql')
    print(f"Generated SQL: {sql}")
    
    if not sql:
        print("No SQL returned.")
        return
        
    # Verify no double limit if we add one manually to test logic
    # The prompt asked for TOP 5, so let's see what the LLM gave.
    
    # 2. Test Execute
    print("\nTesting /execute...")
    # Let's pass the SQL back
    response_exec = client.post('/execute', json={'sql': sql})
    data_exec = response_exec.get_json()
    
    if 'error' in data_exec:
        print(f"Execute Failed: {data_exec['error']}")
        return
        
    print("Execute Success!")
    print(f"Rows: {data_exec.get('rows')}")
    print(f"CSV URL: {data_exec.get('csv_url')}")
    
    # Verify file creation
    if data_exec.get('csv_url'):
        local_path = f"web{data_exec['csv_url']}"
        if os.path.exists(local_path):
             print(f"CSV file found at {local_path}")
        else:
             print(f"CSV file MISSING at {local_path}")

if __name__ == "__main__":
    # Ensure keys are set for helper
    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        print("Set API Keys first")
    else:
        test_workflow()
