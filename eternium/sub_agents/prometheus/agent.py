"""prometheus_query_agent: for getting metrics and data from prometheus"""

import json
from prometheus_api_client import PrometheusConnect
from google.adk import Agent
from config import settings
from . import prompt

# Configuration
PROMETHEUS_URL = settings.prometheus.url

# Tool Functions

def run_promql_query(query: str, **kwargs) -> list:
  """
  Executes a PromQL query against the homelab Prometheus instance and returns the raw, structured result.
  Use this to answer any questions about system metrics like CPU usage, memory usage,
  or network traffic. For example, to find average CPU usage, you could
  formulate a query like 'avg(rate(container_cpu_usage_seconds_total[5m]))'.
  """
  print(f"--- TOOL: Running PromQL query: {query} ---")

  if not PROMETHEUS_URL:
    return [{"error": "PROMETHEUS_URL environment variable is not set."}]

  try:
    pc = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)
    result = pc.custom_query(query=query)

    # If the query returns no data, return an empty list.
    if not result:
      return []

    # Return the raw, structured list of dictionaries from the client.
    return result

  except Exception as e:
    # Return the error in the same structured format (a list with a dict).
    return [{"error": f"Error running Prometheus query: {e}"}]

def create_prometheus_agent(llm):
  """Factory function that builds and returns the Harbor agent."""
  return Agent(
    name="prometheus_analyser_agent",
    model=llm,
    instruction=prompt.PROMETHEUS_ANALYST_INSTRUCTIONS,
    output_key="prometheus_analyser_output",
    tools=[run_promql_query]
  )
