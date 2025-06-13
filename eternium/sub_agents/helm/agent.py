"""Tools for interacting with Helm to manage application releases."""
import subprocess
import json
from google.adk.agents import Agent
from . import prompt

def _run_helm_command(command: list[str]) -> dict:
  """A helper function to run a helm command and return parsed JSON."""
  try:
    # We add '-o json' to the command to get structured output
    full_command = command + ["-o", "json"]
    print(f"--- HELM COMMAND: {' '.join(full_command)} ---")

    result = subprocess.run(
      full_command,
      capture_output=True,
      text=True,
      check=True  # This will raise an exception for non-zero exit codes
    )
    return json.loads(result.stdout)
  except subprocess.CalledProcessError as e:
    # The command failed, return the error from stderr
    return {"error": "Helm command failed", "details": e.stderr}
  except json.JSONDecodeError as e:
    # Helm might have returned non-JSON output on error
    return {"error": "Failed to parse Helm output as JSON", "details": str(e)}
  except Exception as e:
    return {"error": "An unexpected error occurred", "details": str(e)}

# --- Tool Functions ---

def list_helm_releases(namespace: str, **kwargs) -> list:
  """
  Lists all Helm releases in a specific Kubernetes namespace.
  """
  print(f"--- TOOL: Called list_helm_releases for namespace: {namespace} ---")
  command = ["helm", "list", "-n", namespace]
  return _run_helm_command(command)

def get_helm_release_status(release_name: str, namespace: str, **kwargs) -> dict:
  """
  Gets the detailed status of a specific Helm release in a namespace.
  """
  print(f"--- TOOL: Called get_helm_release_status for {release_name} ---")
  command = ["helm", "status", release_name, "-n", namespace]
  return _run_helm_command(command)

def get_helm_release_history(release_name: str, namespace: str, **kwargs) -> list:
  """
  Gets the revision history for a specific Helm release in a namespace.
  """
  print(f"--- TOOL: Called get_helm_release_history for {release_name} ---")
  command = ["helm", "history", release_name, "-n", namespace]
  return _run_helm_command(command)

def upgrade_helm_release(release_name: str, namespace: str, chart: str, version: str, **kwargs) -> dict:
  """
  Upgrades a Helm release to a specific chart version. This is an ACTION.
  It uses '--install' to install the release if it doesn't exist, and '--atomic'
  to ensure the upgrade is rolled back on failure.
  Args:
    release_name: The name of the release to upgrade (e.g., 'prowlarr').
    namespace: The namespace of the release.
    chart: The name of the chart in the repository (e.g., 'prowlarr/prowlarr').
    version: The target version for the chart (e.g., '1.16.2').
  """
  print(f"--- ACTION TOOL: Upgrading Helm release {release_name} to version {version} ---")
  command = [
    "helm", "upgrade", "--install", release_name, chart,
    "--namespace", namespace,
    "--version", version,
    "--atomic" # Important: roll back on failure
  ]
  # The upgrade command doesn't produce useful JSON, so we run it differently
  try:
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return {"status": "success", "message": "Helm upgrade process initiated successfully.", "output": result.stdout}
  except subprocess.CalledProcessError as e:
    return {"status": "error", "message": "Helm upgrade failed.", "details": e.stderr}

def create_helm_agent(llm) -> Agent:
  """Factory function to create the Helm Operator agent."""

  return Agent(
    name="helm_operator",
    model=llm,
    instruction=prompt.HELM_OPERATOR_INSTRUCTIONS,
    tools = [
      list_helm_releases,
      get_helm_release_status,
      get_helm_release_history,
      upgrade_helm_release
    ]
  )