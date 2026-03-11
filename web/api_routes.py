import os
import pandas as pd
from flask import Blueprint, request, jsonify, Response, session
from adqlm.client import ADQLMAssistant

api_bp = Blueprint('api', __name__)

def get_assistant():
    """Returns the globally initialized assistant (from app.py)"""
    from web.app import get_assistant as _get_assistant
    return _get_assistant()

@api_bp.route('/models')
def get_models():
    """Returns a list of supported models."""
    gemma_models = [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
        {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite"}
    ]
    return jsonify(gemma_models)

@api_bp.route('/generate', methods=['POST'])
def generate():
    """
    Endpoint to generate a query from natural language.
    Expects JSON: { "message": "query text", "model": "optional_model_name" }
    """
    user_input = request.json.get('message')
    model_name = request.json.get('model')

    if not model_name:
            model_name = "gemini-2.5-flash"

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    assistant = get_assistant()
    result = assistant.generate_query(user_input, model_name=model_name)
    return jsonify(result)

@api_bp.route('/execute', methods=['POST'])
def execute():
    """
    Endpoint to execute a query and retrieve results.
    Expects JSON: { "sql": "SELECT ...", "service": "noirlab" }
    """
    query = request.json.get('sql')
    service_key = request.json.get('service', 'noirlab')

    if not query:
        return jsonify({"error": "No query provided"}), 400

    assistant = get_assistant()
    result = assistant.execute_and_preview(query, service_key=service_key)
    return jsonify(result)

@api_bp.route('/download_csv', methods=['POST'])
def download_csv():
    """
    Endpoint to stream CSV download of a query result.
    Expects JSON: { "sql": "SELECT ...", "service": "noirlab" }
    """
    query = request.json.get('sql')
    service_key = request.json.get('service', 'noirlab')

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        assistant = get_assistant()

        if service_key not in assistant.services:
            return jsonify({"error": f"Unknown service: {service_key}"}), 400

        service = assistant.services[service_key]
        print(f"Executing for download on {service.get_name()}: {query}")
        df = service.execute_query(query)

        if df is None:
             return jsonify({"error": "No data returned"}), 404

        # Stream CSV
        csv_data = df.to_csv(index=False)

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=results.csv"}
        )
    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500
