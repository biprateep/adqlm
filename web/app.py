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
    """Initializes the AdqlmAssistant singleton if not already created."""
    global assistant
    if assistant is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            # For demo purposes, we might just warn or let it fail later
            print("Warning: GOOGLE_API_KEY not set.")
        
        # Ingest docs once on startup
        assistant = AdqlmAssistant(google_api_key=api_key)
        assistant.ingest_docs()

@app.route('/')
def index():
    """Renders the main chat interface."""
    return render_template('index.html')

@app.route('/models')
def get_models():
    """Returns a list of supported Gemini/Gemma models."""
    models = [
        {"id": "models/gemma-3-27b-it", "name": "Gemma 3 27B"},
        {"id": "models/gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
        {"id": "models/gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
        {"id": "models/gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
    ]
    return jsonify(models)

@app.route('/generate', methods=['POST'])
def generate():
    """
    Endpoint to generate SQL from natural language.
    Expects JSON: { "message": "query text", "model": "optional_model_name" }
    Returns JSON: { "sql": "SELECT ...", "error": "..." }
    """
    user_input = request.json.get('message')
    model_name = request.json.get('model')
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    result = assistant.generate_query(user_input, model_name=model_name)
    return jsonify(result)

@app.route('/execute', methods=['POST'])
def execute():
    """
    Endpoint to execute SQL and retrieve results.
    Expects JSON: { "sql": "SELECT ..." }
    Returns JSON: { "success": true, "preview": [...], "csv_url": "..." }
    """
    sql_query = request.json.get('sql')
    if not sql_query:
        return jsonify({"error": "No SQL provided"}), 400
        
    result = assistant.execute_and_save(sql_query)
    return jsonify(result)

# Keeping /query for older tests but deprecated
@app.route('/query', methods=['POST'])
def query():
    """Deprecated: Legacy endpoint combining generation and execution."""
    user_input = request.json.get('message')
    if not user_input:
         return jsonify({"error": "No message provided"}), 400
    
    # Use legacy method
    result = assistant.process_query(user_input)
    
    # Process data legacy way too
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
