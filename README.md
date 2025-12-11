# ADQLM - Astronomical Data Query Assistant

A natural language interface for the NOIRLab Astro Data Lab, powered by Gemini and RAG.

## Features
- **Natural Language to ADQL**: Translates English questions into complex SQL queries.
- **RAG Powered**: Uses retrieval-augmented generation with Q3C and table schema documentation.
- **Dual Access Modes**:
    - **Public Mode**: Access restricted to open-source **Gemma 27B**.
    - **Dev Mode**: Full access to **Gemini 2.5 Flash/Pro**.
- **Interactive UI**: Chat interface with syntax highlighting and CSV export.

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
    export DEV_PASSWORD="admin_password"
    export PUBLIC_PASSWORD="guest_password"
    # Optional: For Data Lab access (public user is default if not set)
    # export DATALAB_TOKEN="your_token" 
    ```

3.  **Run the App**:
    ```bash
    python3 web/app.py
    ```
    Visit `http://localhost:5000` and log in.

## Deployment on Vercel

This project is configured for deployment on Vercel using the Flask runtime.

> **Warning**: The project dependencies (esp. `sentence-transformers` and `torch`) are large. You may hit Vercel's 250MB serverless function limit. If so, consider container-based hosting like Render or Railway.

### Steps

1.  **Install Vercel CLI**:
    ```bash
    npm i -g vercel
    ```

2.  **Deploy**:
    Run the following command from the project root:
    ```bash
    vercel
    ```
    Follow the prompts to link the project.

3.  **Configure Environment Variables**:
    Go to your Vercel Project Settings > Environment Variables and add:
    *   `GOOGLE_API_KEY`
    *   `DEV_PASSWORD`
    *   `PUBLIC_PASSWORD`
    *   `SECRET_KEY` (Generate a random string for sessions)
    *   `DATALAB_TOKEN` (Optional, but recommended for avoiding rate limits)

4.  **Redeploy**:
    ```bash
    vercel --prod
    ```

## Authentication Roles

*   **Dev Role**: Log in with `DEV_PASSWORD`. Can verify experimental models.
*   **Public Role**: Log in with `PUBLIC_PASSWORD`. Can only use Gemma 3 27B.
