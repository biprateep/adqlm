from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Response
from adqlm.client import AdqlmAssistant
import os
import pandas as pd
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_dev_key")

# Initialize the assistant globally (or lazily)
assistant = None

def get_assistant():
    global assistant
    if assistant is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        # Ensure datalab token is passed if available
        datalab_token = os.environ.get("DATALAB_TOKEN")
        
        if not api_key:
            print("Warning: GOOGLE_API_KEY not set.")
        
        assistant = AdqlmAssistant(google_api_key=api_key, datalab_token=datalab_token)
        # Ingest docs once on startup
        assistant.ingest_docs()
    return assistant

@app.before_request
def initialize_assistant():
    """Initializes the AdqlmAssistant singleton if not already created."""
    get_assistant()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        public_pwd = os.environ.get('PUBLIC_PASSWORD')
        
        if public_pwd and password == public_pwd:
            session['role'] = 'public'
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid Password")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Renders the main chat interface."""
    return render_template('index.html')

@app.route('/models')
@login_required
def get_models():
    """Returns a list of supported Gemma models."""
    
    gemma_models = [
        {"id": "models/gemma-3-27b-it", "name": "Gemma 3 27B"}
    ]
    
    return jsonify(gemma_models)

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    """
    Endpoint to generate SQL from natural language.
    Expects JSON: { "message": "query text", "model": "optional_model_name" }
    """
    user_input = request.json.get('message')
    model_name = request.json.get('model')
    
    # Enforce Gemma usage
    if model_name and "gemma" not in model_name:
            return jsonify({"error": "Access Denied: Only Gemma models are supported."}), 403
    
    if not model_name:
            model_name = "models/gemma-3-27b-it"

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    result = get_assistant().generate_query(user_input, model_name=model_name)
    return jsonify(result)

@app.route('/execute', methods=['POST'])
@login_required
def execute():
    """
    Endpoint to execute SQL and retrieve results.
    Expects JSON: { "sql": "SELECT ..." }
    """
    sql_query = request.json.get('sql')
    if not sql_query:
        return jsonify({"error": "No SQL provided"}), 400
        
    result = get_assistant().execute_and_preview(sql_query)
    return jsonify(result)

@app.route('/download_csv', methods=['POST'])
@login_required
def download_csv():
    """
    Endpoint to stream CSV download of a query result.
    Expects JSON: { "sql": "SELECT ..." }
    """
    sql_query = request.json.get('sql')
    if not sql_query:
        return jsonify({"error": "No SQL provided"}), 400
        
    try:
        # execute using the assistant's datalab client directly or a helper
        # We need to render to CSV string
        assistant = get_assistant()
        print(f"Executing for download: {sql_query}")
        df = assistant.datalab.execute_query(sql_query)
        
        if df is None:
             return jsonify({"error": "No data returned"}), 404
             
        # Stream CSV
        # We can use .to_csv() but return it as a string
        csv_data = df.to_csv(index=False)
        
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=results.csv"}
        )
    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

# Keeping /query for older tests but deprecated
@app.route('/query', methods=['POST'])
@login_required
def query():
    """Deprecated: Legacy endpoint combining generation and execution."""
    user_input = request.json.get('message')
    if not user_input:
         return jsonify({"error": "No message provided"}), 400
    
    # For legacy, default public to Gemma if they hit this endpoint
    # But generate_query default model is None -> uses LLMClient default (gemini-flash)
    # So we might leak Flash usage here if we don't handle it.
    # Legacy endpoint doesn't support model selection.
    # If public, we should force them to use a model safe one, OR reject.
    # Given requirements, public = Gemma only.
    if session.get('role') == 'public':
         return jsonify({"error": "Legacy endpoint not supported for public role. use /generate"}), 403

    # Use legacy method
    result = get_assistant().process_query(user_input)
    
    # Process data legacy way too
    data_response = None
    if result['data'] is not None:
        if isinstance(result['data'], pd.DataFrame):
            # Should not happen with new client, but safety net
            import numpy as np
            result['data'] = result['data'].replace({np.nan: None})
            data_response = result['data'].to_dict(orient='records')
        elif isinstance(result['data'], list):
            data_response = result['data']
        else:
             data_response = str(result['data'])
             
    return jsonify({
        "sql": result['sql'],
        "explanation": result['explanation'],
        "data": data_response
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
