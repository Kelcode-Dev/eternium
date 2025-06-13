"""harbor_query_agent: for getting information from the docker registry"""

import json
import requests
from google.adk import Agent
from config import settings
from . import prompt

# Helper for API calls
def _make_harbor_request(method, endpoint):
  """
  A helper to abstract away the request and error handling.
  """
  url = f"{HARBOR_URL}{endpoint}"
  try:
    response = requests.request(
      method,
      settings.harbor.url,
      auth=(
        settings.harbor.username,
        settings.harbor.token
      ),
      verify=settings.harbor.ssl_verify
    )
    response.raise_for_status()
    return response.json()
  except requests.exceptions.HTTPError as e:
    # Return a structured error
    return {"error": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
  except requests.exceptions.RequestException as e:
    return {"error": f"Request failed: {e}"}

# Tool Functions

def list_harbor_projects(**kwargs) -> list:
  """
  Retrieves a list of all project names in the Harbor registry.
  """
  print("--- TOOL: Called list_harbor_projects ---")
  data = _make_harbor_request("GET", "/api/v2.0/projects")

  if "error" in data:
    return [data]  # Return list with an error dict

  if not data:
    return []  # Return an empty list if no projects

  return [project['name'] for project in data]

def list_harbor_repositories(project_name: str, **kwargs) -> list:
  """
  Lists all container image repositories within a specific Harbor project.
  """
  print(f"--- TOOL: Called list_harbor_repositories for project '{project_name}' ---")
  endpoint = f"/api/v2.0/projects/{project_name}/repositories"
  data = _make_harbor_request("GET", endpoint)

  if "error" in data:
    return [data]

  if not data:
    return []

  return [repo['name'].replace(f"{project_name}/", "") for repo in data]

def list_image_tags(project_name: str, repository_name: str, **kwargs) -> list:
  """
  Lists all the tags for a specific image repository in a Harbor project.
  """
  print(f"--- TOOL: Called list_image_tags for {project_name}/{repository_name} ---")
  endpoint = f"/api/v2.0/projects/{project_name}/repositories/{repository_name}/artifacts"
  data = _make_harbor_request("GET", endpoint)

  if "error" in data:
    return [data]

  if not data:
    return []

  return [artifact['tags'][0]['name'] for artifact in data if artifact.get('tags')]

def get_vulnerability_report(project_name: str, repository_name: str, tag: str, **kwargs) -> dict:
  """
  Retrieves the security vulnerability report for a specific container image tag.
  """
  print(f"--- TOOL: Called get_vulnerability_report for {project_name}/{repository_name}:{tag} ---")
  endpoint = f"/api/v2.0/projects/{project_name}/repositories/{repository_name}/artifacts/{tag}?with_scan_overview=true"
  data = _make_harbor_request("GET", endpoint)

  if "error" in data:
    return data

  scan_overview = data.get('scan_overview')
  if not scan_overview:
    return {"status": "Not Scanned", "message": f"No vulnerability scan overview found for {repository_name}:{tag}."}

  summary = scan_overview.get(next(iter(scan_overview)), {}).get('summary', {})
  if not summary or summary.get('total', 0) == 0:
    return {"status": "Clean", "total_vulnerabilities": 0, "message": f"No vulnerabilities found for {repository_name}:{tag}."}

  # Return the summary as a structured dictionary
  return {
    "status": "Vulnerabilities Found",
    "image": f"{project_name}/{repository_name}:{tag}",
    "vulnerability_summary": {
      "total": summary.get('total', 0),
      "critical": summary.get('critical', 0),
      "high": summary.get('high', 0),
      "medium": summary.get('medium', 0),
      "low": summary.get('low', 0),
    }
  }

def scan_image(project_name: str, repository_name: str, tag: str, **kwargs) -> dict:
  """
  Triggers a new vulnerability scan for a specific container image tag in Harbor.
  This is an ACTION that initiates a process. It does not return the results directly.
  Use get_vulnerability_report to check the results after the scan is complete.
  """
  print(f"--- ACTION TOOL: Called scan_image for {project_name}/{repository_name}:{tag} ---")

  # The API endpoint to trigger a scan on an artifact (image tag)
  endpoint = f"/api/v2.0/projects/{project_name}/repositories/{repository_name}/artifacts/{tag}/scan"
  payload = {}
  result = _make_harbor_request("POST", endpoint, payload=payload)

  return result

def create_harbor_agent(llm):
  """Factory function that builds and returns the Harbor agent."""
  return Agent(
    name="harbor_query_agent",
    model=llm,
    instruction=prompt.HARBOR_INSPECTOR_INSTRUCTIONS,
    output_key="harbor_query_output",
    tools=[
      list_harbor_projects,
      list_harbor_repositories,
      list_image_tags,
      get_vulnerability_report,
      scan_image
    ],
  )
