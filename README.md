# ADQLM - Astronomy Data Query Language Model

A natural language interface for astronomical data services, powered by Gemini and RAG.
Currently supports NOIRLab Astro Data Lab, with architecture designed to easily add more services like Astroquery.

## Features
- **Natural Language to Queries**: Translates English questions into complex queries (e.g. ADQL).
- **RAG Powered**: Uses retrieval-augmented generation with documentation context.
- **Dynamic Routing**: Uses LLMs to intelligently route queries to the appropriate astronomical data service.
- **Interactive UI**: Chat interface with syntax highlighting and data export.
- **Lightweight Deployment**: Ready for platforms like Render.

## Testing & Deployment

### Local Development (Testing on your laptop)

1.  **Clone and Install**:
    ```bash
    git clone <repo_url>
    cd adqlm
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Environment Setup**:
    Set the required environment variables in your terminal before running the app:
    ```bash
    export GOOGLE_API_KEY="your_gemini_key"
    export GLOBAL_PASSWORD="your_beta_password" # Set this to test the login screen
    export SECRET_KEY="a_random_secret_string"

    # Optional: For Data Lab authenticated access (public user is default if not set)
    # export DATALAB_TOKEN="your_token" 
    ```
    *(Note: If `GLOBAL_PASSWORD` is not set locally, the app will bypass the login screen for testing convenience, but will print a warning).*

3.  **Run the App**:
    ```bash
    python3 web/app.py
    ```
    Visit `http://localhost:5000` in your web browser.

### Deployment on Render (For beta testing)

This project includes a `render.yaml` file to make deployment seamless. Render's free tier is sufficient for beta testing.

1.  **Push to GitHub**: Ensure your latest code is pushed to your GitHub repository.
2.  **Connect to Render**:
    *   Go to [Render.com](https://render.com/) and sign in.
    *   Click "New" -> "Blueprint" (or "Web Service" if doing it manually).
3.  **Deploy using Blueprint**:
    *   Connect your GitHub account and select your `adqlm` repository.
    *   Render will automatically detect the `render.yaml` file and configure the service (`adqlm-service`) with the correct build command (`pip install -r requirements.txt`) and start command (`gunicorn web.app:app`).
4.  **Configure Environment Variables**:
    *   During the setup, Render will prompt you to provide values for the environment variables defined in `render.yaml`.
    *   Fill in your `GOOGLE_API_KEY`.
    *   Set a secure `GLOBAL_PASSWORD` to lock the app for beta testers.
    *   (Optional) Provide your `DATALAB_TOKEN`.
    *   Render will auto-generate the `SECRET_KEY`.
5.  **Launch**: Click "Apply" or "Create". Render will build the image and deploy the web service. Once live, you will get a `.onrender.com` URL to share with your beta testers!

## Authentication

*   The app is protected by a global password (`GLOBAL_PASSWORD` env variable) to restrict access during beta testing.
*   Users must enter this password on the landing page before they can interact with the chat interface.
