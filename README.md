# ADQLM - Astronomy Data Query Language Model

A natural language interface for astronomical data services, powered by Gemini and RAG.
Currently supports NOIRLab Astro Data Lab, with architecture designed to easily add more services like Astroquery.

## Features
- **Natural Language to Queries**: Translates English questions into complex queries (e.g. ADQL).
- **RAG Powered**: Uses retrieval-augmented generation with documentation context.
- **Dynamic Routing**: Uses LLMs to intelligently route queries to the appropriate astronomical data service.
- **Interactive UI**: Chat interface with syntax highlighting and data export.
- **Lightweight Deployment**: Ready for platforms like Render.

## Local Development

1.  **Clone and Install**:
    ```bash
    git clone <repo_url>
    cd adqlm
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Environment Setup**:
    Create a `.env` file (or set variables in your shell):
    ```bash
    export GOOGLE_API_KEY="your_gemini_key"
    export GLOBAL_PASSWORD="your_beta_password"
    # Optional: For Data Lab access (public user is default if not set)
    # export DATALAB_TOKEN="your_token" 
    ```

3.  **Run the App**:
    ```bash
    python3 web/app.py
    ```
    Visit `http://localhost:5000` and log in.

## Deployment on Render

This project is configured for deployment on Render.

1.  Connect your GitHub repository to Render.
2.  Create a new "Web Service".
3.  Set the Build Command to `pip install -r requirements.txt`.
4.  Set the Start Command to `gunicorn web.app:app`.
5.  Add the following Environment Variables in the Render dashboard:
    *   `GOOGLE_API_KEY`: Your Gemini API key.
    *   `GLOBAL_PASSWORD`: Password for beta testing access.
    *   `SECRET_KEY`: A random string for Flask sessions.
    *   `DATALAB_TOKEN` (Optional): For NOIRLab Data Lab authenticated access.

## Authentication

*   The app is protected by a global password (`GLOBAL_PASSWORD` env variable) to restrict access during beta testing.
