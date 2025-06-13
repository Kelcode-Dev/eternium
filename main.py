import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from config import settings

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Call the function to get the FastAPI app instance
app: FastAPI = get_fast_api_app(
  agents_dir=AGENT_DIR,
  session_service_uri=settings.app.session_db,
  allow_origins=settings.app.allowed_origins,
  web=settings.app.serve_web_ui,
)

# Simple health check endpoint for Kubernetes liveness/readiness probes.
@app.get('/healthz', status_code=200, tags=["Health"])
def health():
  return {"status": "ok"}

if __name__ == "__main__":
  uvicorn.run(app, host=settings.app.host, port=settings.app.port)
