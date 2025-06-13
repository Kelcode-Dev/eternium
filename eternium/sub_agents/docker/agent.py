"""Tools for pulling, tagging, and pushing container images using the Docker daemon."""
import docker
from google.adk.agents import Agent
from config import settings
from . import prompt

DOCKER_CLIENT = None
try:
  if settings.docker.client:
    DOCKER_CLIENT = settings.docker.client
  else:
    DOCKER_CLIENT = docker.from_env()
except Exception as e:
  print(f"WARNING: Could not connect to Docker daemon. DockerAgent tools will fail. Error: {e}")

def pull_image(image_name_with_tag: str, **kwargs) -> dict:
  """
  Pulls a container image from a public or private registry to the local Docker host.
  Args:
    image_name_with_tag: The full name of the image, including the tag.
    Example: 'ghcr.io/open-webui/open-webui:v0.6.14'
  """
  if not DOCKER_CLIENT: return {"status": "error", "message": "Docker client not available."}
  print(f"--- ACTION TOOL: Called pull_image for {image_name_with_tag} ---")
  try:
    image = DOCKER_CLIENT.images.pull(image_name_with_tag)
    return {"status": "success", "pulled_image_id": image.short_id}
  except Exception as e:
    return {"status": "error", "message": str(e)}

def retag_image(source_image: str, target_image: str, **kwargs) -> dict:
  """
  Applies a new tag to an already pulled image on the local Docker host.
  Args:
    source_image: The original image name that was pulled.
    target_image: The new image name for the target registry.
  """
  if not DOCKER_CLIENT: return {"status": "error", "message": "Docker client not available."}
  print(f"--- ACTION TOOL: Retagging {source_image} to {target_image} ---")
  try:
    image = DOCKER_CLIENT.images.get(source_image)
    if image.tag(target_image):
      return {"status": "success", "new_tag": target_image}
    return {"status": "error", "message": "Failed to apply new tag."}
  except Exception as e:
    return {"status": "error", "message": str(e)}

def push_image(image_name_with_tag: str, **kwargs) -> dict:
  """
  Pushes a tagged image from the local Docker host to a registry.
  Args:
    image_name_with_tag: The full name of the image to push.
  """
  if not DOCKER_CLIENT: return {"status": "error", "message": "Docker client not available."}
  print(f"--- ACTION TOOL: Pushing {image_name_with_tag} ---")
  try:
    result = DOCKER_CLIENT.images.push(image_name_with_tag, stream=False, decode=False)
    if "error" in result:
      return {"status": "error", "message": result}
    return {"status": "success", "message": f"Successfully pushed {image_name_with_tag}."}
  except Exception as e:
    return {"status": "error", "message": str(e)}

def create_docker_agent(llm):
  """Factory function that builds and returns the Docker agent."""
  return Agent(
    name="docker_agent",
    model=llm,
    instruction=prompt.DOCKER_AGENT_INSTRUCTIONS,
    output_key="docker_output",
    tools=[
      pull_image,
      retag_image,
      push_image
    ],
  )
