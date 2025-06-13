"""
This module contains the factory function for creating the main Coordinator agent.
It dynamically assembles the agency based on the enabled agents.
"""
import importlib
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm
from . import prompt
from config import settings

llm = LiteLlm(
  model=settings.llm.model,
  api_base=settings.llm.url,
  api_key=settings.llm.token
)

AGENT_BLUEPRINTS = {
  'docker':     {'prompt_snippet': prompt.DOCKER_DELEGATION_RULE},
  'harbor':     {'prompt_snippet': prompt.HARBOR_DELEGATION_RULE},
  'helm':       {'prompt_snippet': prompt.HELM_DELEGATION_RULE},
  'kubernetes': {'prompt_snippet': prompt.KUBERNETES_DELEGATION_RULE},
  'memory':     {'prompt_snippet': prompt.MEMORY_DELEGATION_RULE},
  'mysql':      {'prompt_snippet': prompt.MYSQL_DELEGATION_RULE},
  'prometheus': {'prompt_snippet': prompt.PROMETHEUS_DELEGATION_RULE}
}
available_agents = []
enabled_agent_rules = []

print("Assembling agency...")
for agent_name, config in AGENT_BLUEPRINTS.items():
  if getattr(settings.app, f"enabled_{agent_name}", False):
    print(f"  - Enabling specialist: {agent_name}")
    try:
      module_path = f".sub_agents.{agent_name}"
      agent_module = importlib.import_module(module_path, package='eternium')
      factory_function = getattr(agent_module, f"create_{agent_name}_agent")

      # The worker agent is created with the same llm
      agent_instance = factory_function(llm)

      available_agents.append(AgentTool(agent=agent_instance))
      enabled_agent_rules.append(config['prompt_snippet'])
    except (ImportError, AttributeError) as e:
      print(f"  - WARNING: Could not load agent '{agent_name}'. Error: {e}")
  else:
    print(f"No settngs for {agent_name}")

delegation_rules = "\n".join(enabled_agent_rules)
final_prompt = prompt.COORDINATOR_PROMPT_TEMPLATE.format(delegation_rules=delegation_rules)

# The coordinator is also created with the same llm
eternium_coordinator = Agent(
  name="eternium_coordinator",
  model=llm,
  instruction=final_prompt,
  tools=available_agents
)

root_agent = eternium_coordinator
