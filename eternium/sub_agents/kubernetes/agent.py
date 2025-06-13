"""kubernetes_expert_agent: for intereacting with a kubernetes cluster"""

import json
from kubernetes import client, config
from google.adk import Agent
from . import prompt

# Configuration
try:
    print("--- Loading in-cluster Kubernetes config ---")
    config.load_incluster_config()
except config.ConfigException:
    print("--- In-cluster config failed, loading local kubeconfig ---")
    config.load_kube_config()

CORE_V1_API = client.CoreV1Api()
APPS_V1_API = client.AppsV1Api()
NETWORKING_V1_API = client.NetworkingV1Api()

# Tool Functions

def get_pods(namespace: str, **kwargs) -> list[dict]:
  """
  Retrieves the name, status, and restart count of all pods in a given Kubernetes namespace.
  """
  print(f"--- TOOL: Called get_pods for namespace: {namespace} ---")
  try:
    pod_list = CORE_V1_API.list_namespaced_pod(namespace=namespace)
    if not pod_list.items:
      return []  # Return an empty list if no pods are found

    pods_info = []
    for pod in pod_list.items:
      restart_count = pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0
      pods_info.append({
        "name": pod.metadata.name,
        "status": pod.status.phase,
        "restarts": restart_count
      })
    return pods_info
  except Exception as e:
    return [{"error": f"Error listing pods: {e}"}]

def get_deployments(namespace: str, **kwargs) -> list[dict]:
  """
  Retrieves the name and replica status of all deployments in a given Kubernetes namespace.
  """
  print(f"--- TOOL: Called get_deployments for namespace: {namespace} ---")
  try:
    dep_list = APPS_V1_API.list_namespaced_deployment(namespace=namespace)
    if not dep_list.items:
      return []

    deployments_info = []
    for dep in dep_list.items:
      deployments_info.append({
        "name": dep.metadata.name,
        "ready_replicas": dep.status.available_replicas or 0,
        "desired_replicas": dep.spec.replicas
      })
    return deployments_info
  except Exception as e:
    return [{"error": f"Error listing deployments: {e}"}]

def get_statefulsets(namespace: str, **kwargs) -> list[dict]:
  """
  Retrieves the name and replica status of all stateful sets in a given Kubernetes namespace.
  """
  print(f"--- TOOL: Called get_statefulsets for namespace: {namespace} ---")
  try:
    sts_list = APPS_V1_API.list_namespaced_stateful_set(namespace=namespace)
    if not sts_list.items:
      return []

    statefulsets_info = []
    for sts in sts_list.items:
      statefulsets_info.append({
        "name": sts.metadata.name,
        "ready_replicas": sts.status.ready_replicas or 0,
        "desired_replicas": sts.spec.replicas
      })
    return statefulsets_info
  except Exception as e:
    return [{"error": f"Error listing statefulsets: {e}"}]

def get_daemonsets(namespace: str, **kwargs) -> list[dict]:
  """
  Retrieves the name and scheduling status of all daemon sets in a given Kubernetes namespace.
  """
  print(f"--- TOOL: Called get_daemonsets for namespace: {namespace} ---")
  try:
    ds_list = APPS_V1_API.list_namespaced_daemon_set(namespace=namespace)
    if not ds_list.items:
      return []

    daemonsets_info = []
    for ds in ds_list.items:
      daemonsets_info.append({
        "name": ds.metadata.name,
        "desired_scheduled": ds.status.desired_number_scheduled,
        "ready": ds.status.number_ready
      })
    return daemonsets_info
  except Exception as e:
      return [{"error": f"Error listing daemonsets: {e}"}]

def get_namespaces(**kwargs) -> list[str]:
  """
  Retrieves a list of all namespaces within the cluster.
  """
  print(f"--- TOOL: Called get_namespaces ---")
  try:
    ns_list = CORE_V1_API.list_namespace()
    if not ns_list.items:
      return []

    namespace_names = [ns.metadata.name for ns in ns_list.items]
    return namespace_names
  except Exception as e:
    return [f"Error listing namespaces: {e}"]

def get_ingresses(namespace: str, **kwargs) -> list[dict]:
  """
  Retrieves a list of all Ingress resources in a given Kubernetes namespace.
  Use this to find out how services are exposed to the outside world (URLs, hostnames).
  """
  print(f"--- TOOL: Called get_ingresses for namespace: {namespace} ---")
  try:
    ingress_list = NETWORKING_V1_API.list_namespaced_ingress(namespace=namespace)
    if not ingress_list.items:
        return []

    ingresses_info = []
    for ingress in ingress_list.items:
      rules_info = []
      if ingress.spec.rules:
        for rule in ingress.spec.rules:
          if rule.http and rule.http.paths:
            paths = [
              f"{path.path} -> {path.backend.service.name}:{path.backend.service.port.number}"
              for path in rule.http.paths
            ]
            rules_info.append({"host": rule.host, "paths": paths})

      ingresses_info.append({
        "name": ingress.metadata.name,
        "rules": rules_info
      })
    return ingresses_info
  except Exception as e:
    return [{"error": f"Error listing ingresses: {e}"}]

def get_services(namespace: str, **kwargs) -> list[dict]:
  """
  Retrieves a list of all Service resources in a given Kubernetes namespace.
  Use this to find out ingresses are connected to pods and which svc's expose which pods
  """
  print(f"--- TOOL: Called get_services for namespace: {namespace} ---")
  try:
    svc_list = CORE_V1_API.list_namespaced_service(namespace=namespace)
    result = []
    for svc in svc_list.items:
      result.append({
        "name": svc.metadata.name,
        "type": svc.spec.type,
        "cluster_ip": svc.spec.cluster_ip,
        "ports": [
          {
            "port": p.port,
            "target_port": p.target_port,
            "protocol": p.protocol,
            "name": p.name
          }
          for p in svc.spec.ports
        ],
        "selector": svc.spec.selector or {},
        "creation_timestamp": svc.metadata.creation_timestamp.isoformat() if svc.metadata.creation_timestamp else None
      })

    return result
  except Exception as e:
    return [{"error": f"Error listing services: {e}"}]

def scale_deployment(deployment_name: str, namespace: str, replicas: int, **kwargs) -> dict:
  """
  Scales a specific deployment to a desired number of replicas.
  """
  print(f"--- TOOL: Called scale_deployment for {deployment_name} to {replicas} replicas ---")
  try:
    APPS_V1_API.patch_namespaced_deployment_scale(
      name=deployment_name, namespace=namespace, body={"spec": {"replicas": replicas}}
    )
    return {"status": "success", "message": f"Scale command issued for {deployment_name}."}
  except Exception as e:
    return {"status": "error", "message": f"Error scaling deployment: {e}"}

def delete_pod(namespace: str, pod_name: str, **kwargs) -> dict:
  """
  Deletes a specific pod from a given namespace.
  """
  print(f"--- TOOL: Called delete_pod for '{pod_name}' in namespace '{namespace}'. ---")
  try:
    CORE_V1_API.delete_namespaced_pod(pod_name, namespace)
    return {"status": "success", "message": f"Delete command issued for pod '{pod_name}'."}
  except Exception as e:
    return {"status": "error", "message": f"Error deleting pod: {e}"}

def describe_resource(name: str, namespace: str, kind: str, **kwargs) -> dict:
  """
  Provides a detailed description and recent events for various Kubernetes resources.
  Use this as the primary tool for diagnosing 'why' a resource is failing.
  The 'kind' can be 'pod', 'deployment', 'statefulset', 'daemonset', 'service', or 'ingress'.
  """
  print(f"--- TOOL: Called describe_resource for {kind}/{name} in {namespace} ---")
  try:
    resource_info = {}
    events_list = []
    resource_kind_for_events = kind.capitalize()

    # --- Get resource-specific details ---
    kind_lower = kind.lower()
    if kind_lower == 'pod':
      resource = CORE_V1_API.read_namespaced_pod(name=name, namespace=namespace)
      resource_info = {"status": resource.status.phase, "ip": resource.status.pod_ip, "node": resource.spec.node_name}

    elif kind_lower == 'service' or kind_lower == 'svc':
      resource = CORE_V1_API.read_namespaced_service(name=name, namespace=namespace)
      ports = [f"{p.port}/{p.protocol}" for p in resource.spec.ports] if resource.spec.ports else []
      resource_info = {"type": resource.spec.type, "cluster_ip": resource.spec.cluster_ip, "ports": ports}
      resource_kind_for_events = "Service"

    elif kind_lower == 'deployment':
      resource = APPS_V1_API.read_namespaced_deployment(name=name, namespace=namespace)
      resource_info = {"replicas": f"{resource.status.available_replicas or 0}/{resource.spec.replicas}", "strategy": resource.spec.strategy.type}
      resource_kind_for_events = "Deployment"

    elif kind_lower == 'statefulset':
      resource = APPS_V1_API.read_namespaced_stateful_set(name=name, namespace=namespace)
      resource_info = {"replicas": f"{resource.status.ready_replicas or 0}/{resource.spec.replicas}"}
      resource_kind_for_events = "StatefulSet"

    elif kind_lower == 'daemonset':
      resource = APPS_V1_API.read_namespaced_daemon_set(name=name, namespace=namespace)
      resource_info = {"desired": resource.status.desired_number_scheduled, "ready": resource.status.number_ready}
      resource_kind_for_events = "DaemonSet"

    elif kind_lower == 'ingress':
      resource = NETWORKING_V1_API.read_namespaced_ingress(name=name, namespace=namespace)
      hosts = [rule.host for rule in resource.spec.rules] if resource.spec.rules else []
      resource_info = {"class": resource.spec.ingress_class_name, "hosts": hosts}
      resource_kind_for_events = "Ingress"

    else:
      return {"error": f"Describing resources of kind '{kind}' is not supported yet."}

    # --- Fetch and add associated events ---
    field_selector = f"involvedObject.name={name},involvedObject.namespace={namespace},involvedObject.kind={resource_kind_for_events}"
    events = CORE_V1_API.list_namespaced_event(namespace=namespace, field_selector=field_selector)

    for event in events.items:
      events_list.append({
        "timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None,
        "type": event.type,
        "reason": event.reason,
        "message": event.message
      })

    # Sort events by time, most recent last
    events_list.sort(key=lambda e: e['timestamp'] or '', reverse=True)

    return {"resource_info": resource_info, "events": events_list[:10]} # Return the 10 most recent events
  except Exception as e:
    return {"error": f"Error describing {kind}/{name}: {e}"}

def get_logs(name: str, namespace: str, kind: str, tail_lines: int, previous: bool, **kwargs) -> dict:
  """
  Retrieves logs for a given Kubernetes resource. If the kind is a controller
  (deployment, statefulset, daemonset), it finds a pod managed by it and gets its logs.
  The 'previous' flag only applies when the kind is 'pod'.
  """
  print(f"--- TOOL: Called get_logs for {kind}/{name} in {namespace} ---")

  try:
    pod_name_to_log = ""
    is_controller = False

    # --- Step 1: Determine the actual pod to get logs from ---
    kind_lower = kind.lower()

    if kind_lower == 'pod':
      pod_name_to_log = name

    elif kind_lower in ['deployment', 'statefulset', 'daemonset']:
      is_controller = True
      label_selector_str = ""

      # Get the correct controller object to find its label selector
      if kind_lower == 'deployment':
        controller = APPS_V1_API.read_namespaced_deployment(name=name, namespace=namespace)
        label_selector_str = ",".join([f"{k}={v}" for k, v in controller.spec.selector.match_labels.items()])
      elif kind_lower == 'statefulset':
        controller = APPS_V1_API.read_namespaced_stateful_set(name=name, namespace=namespace)
        label_selector_str = ",".join([f"{k}={v}" for k, v in controller.spec.selector.match_labels.items()])
      elif kind_lower == 'daemonset':
        controller = APPS_V1_API.read_namespaced_daemon_set(name=name, namespace=namespace)
        label_selector_str = ",".join([f"{k}={v}" for k, v in controller.spec.selector.match_labels.items()])

      # Find pods that match the controller's label selector
      pods = CORE_V1_API.list_namespaced_pod(namespace=namespace, label_selector=label_selector_str)
      if not pods.items:
        return {"error": f"No pods found for {kind}/{name}."}

      # Select the first pod found
      pod_name_to_log = pods.items[0].metadata.name

    else:
      return {"error": f"Getting logs for kind '{kind}' is not supported."}

    # --- Step 2: Retrieve the logs from the target pod ---
    if not pod_name_to_log:
      return {"error": "Could not determine a pod to get logs from."}

    # The 'previous' flag is only meaningful for direct pod queries, not controllers
    use_previous_flag = previous if not is_controller else False

    logs = CORE_V1_API.read_namespaced_pod_log(
      name=pod_name_to_log,
      namespace=namespace,
      tail_lines=tail_lines,
      previous=use_previous_flag
    )

    log_source = f"{kind}/{name}"
    if is_controller:
      log_source += f" (via pod '{pod_name_to_log}')"

    return {"source": log_source, "log_content": logs or "No logs found."}
  except Exception as e:
      return {"error": f"Error getting logs for {kind}/{name}: {e}"}

def create_kubernetes_agent(llm):
  """Factory function that builds and returns the Kubernetes agent."""
  return Agent(
    name="kubernetes_expert_agent",
    model=llm,
    instruction=prompt.KUBERNETES_EXPERT_INSTRUCTIONS,
    output_key="kubernetes_expert_output",
    tools=[
      get_pods,
      get_deployments,
      get_statefulsets,
      get_daemonsets,
      get_namespaces,
      get_ingresses,
      get_services,
      get_logs,
      scale_deployment,
      delete_pod,
      describe_resource
    ],
  )
