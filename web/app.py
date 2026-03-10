from flask import Flask
from adqlm.client import ADQLMAssistant
import os

from .api_routes import api_bp
from .frontend_routes import frontend_bp

# Initialize the assistant globally
assistant = None

def get_assistant():
    global assistant
    if assistant is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        datalab_token = os.environ.get("DATALAB_TOKEN")
        
        if not api_key:
            print("Warning: GOOGLE_API_KEY not set.")
        
        assistant = ADQLMAssistant(google_api_key=api_key, datalab_token=datalab_token)
        # Ingest docs once on startup
        assistant.ingest_docs()
    return assistant

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "super_secret_dev_key")

    # Ensure assistant is initialized before handling requests
    @app.before_request
    def initialize_assistant():
        """Initializes the ADQLMAssistant singleton if not already created."""
        get_assistant()

    # Register Blueprints
    # Note: frontend_bp uses login_required which checks session
    # API endpoints might also need protection in production
    app.register_blueprint(frontend_bp)
    
    # We apply a basic before_request check for API routes to enforce login
    @api_bp.before_request
    def require_login_for_api():
        from flask import session, jsonify
        if not session.get('authenticated'):
            # Only enforce if a global password is set
            if os.environ.get('GLOBAL_PASSWORD'):
                return jsonify({"error": "Unauthorized"}), 401

    app.register_blueprint(api_bp)

    return app

# Expose app for Gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
