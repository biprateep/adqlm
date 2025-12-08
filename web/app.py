from flask import Flask, render_template, request, jsonify
from adqlm.client import AdqlmAssistant
import os
import pandas as pd

app = Flask(__name__)

# Initialize the assistant globally (or lazily)
# In a real app, you might want to handle this differently (e.g. factory pattern)
assistant = None

@app.before_request
def initialize_assistant():
    global assistant
    if assistant is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            # For demo purposes, we might just warn or let it fail later
            print("Warning: GOOGLE_API_KEY not set.")
        
        assistant = AdqlmAssistant(google_api_key=api_key)
        # Ingest docs on startup - this might take a moment
        # Ideally this is done asynchronously or pre-built
        assistant.ingest_docs()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    result = assistant.process_query(user_input)
    
    # Process data for JSON serialization if it's a DataFrame
    data_response = None
    if result['data'] is not None:
        if isinstance(result['data'], pd.DataFrame):
            data_response = result['data'].to_dict(orient='records')
        else:
            data_response = str(result['data'])
    
    return jsonify({
        "sql": result['sql'],
        "explanation": result['explanation'],
        "data": data_response
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
