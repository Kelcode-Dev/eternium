# Eternium Agent Helm Chart

This Helm chart deploys a versatile Eternium Assistant Agent into a Kubernetes cluster. The agent enables LLM-assisted automation for inspecting and managing Kubernetes, Prometheus, Harbor, and more.

## Prerequisites and Assumptions

To make full use of all agents you will need installations of the following services:

| Feature              | Dependency / Assumption                      | Notes                                                                 |
| -------------------- | -------------------------------------------- | --------------------------------------------------------------------- |
| LLM                  | Hosted LLM API (e.g. OpenAI, Gemini, Ollama) | Must be reachable and authenticated                                   |
| Memory Agent         | Embedding API endpoint                       | May be separate or part of LLM provider                               |
| Docker Agent         | Docker daemon (TCP or socket)                | Optional; may need volume mount for `/var/run/docker.sock`            |
| Helm Agent           | `helm` CLI installed                         | Must be available inside the container                                |
| Kubernetes Agent     | Kube API + RBAC                              | Assumes agent runs in-cluster with suitable permissions               |
| Harbor Agent         | Harbor registry with token access            | Assumes Harbor-compatible API                                         |
| Prometheus Agent     | Prometheus with Node Exporter                | Should be accessible from the agent                                   |
| MySQL Agent          | MySQL/MariaDB instance                       | Username and password must be provided                                |
| Memory DB (Fallback) | SQLite write access                          | Local path must be writeable, should work with postgres or mysql too  |
| TLS via Ingress      | cert-manager + issuer                        | `ClusterIssuer` or `Issuer` must exist                                |

The chart includes a default ClusterRole, ClusterRoleBinding, and ServiceAccount with sufficient permissions to interact with standard Kubernetes resources. These are enabled via the `rbac.enabled` and `serviceAccount.enabled` values.

## Security Considerations

- Ensure that `LLM_TOKEN`, `HARBOR_TOKEN`, and `MYSQL_PASSWORD` are stored securely and rotated as needed
- Avoid using `APP_ALLOWED_ORIGINS: "*"` in production environments
- Mounting the Docker socket (`/var/run/docker.sock`) grants container-level host control — use with caution, recommendation is a docker enabled image
- If exposing the web UI, secure it behind authentication or IP whitelisting

## Installation

Check out the repo and run the following:

```bash
cd chart
helm upgrade --install eternium-agent . -f values.yaml --namespace=eternium-agent --create-namespace
```

## Configuration

Agents can be turned on and off by switching the relevant `config.data.APP_ENABLED_{AGENT}` value to `true|false`, for more details on the agents, what they do and what configuraiton they require check out the parent readme.

The following table lists the configurable parameters of the `eternium-agent` Helm chart and their default values.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `image.repository` | string | `"myregistry/myproject/myagent"` | Docker image repository to use |
| `image.pullPolicy` | string | `"IfNotPresent"` | Image pull policy |
| `image.tag` | string | `"latest"` | Image tag override |
| `image.imagePullSecrets` | string | `"my-image-pull-secret"` | Name of image pull secret for private registries |
| `replicaCount` | int | `1` | Number of agent replicas |
| `config.name` | string | `"my-agent-configs"` | Name of the ConfigMap |
| `config.data.APP_NAME` | string | `"Eternium Assistant Agent"` | Application name |
| `config.data.APP_ALLOWED_ORIGINS` | string | `"*"` | Allowed CORS origins |
| `config.data.APP_SERVE_WEB_UI` | bool | `true` | Enable or disable serving the web UI |
| `config.data.APP_HOST` | string | `"0.0.0.0"` | Host IP for the service to bind |
| `config.data.APP_PORT` | int | `8080` | Port number the app will run on |
| `config.data.APP_ENABLED_KUBERNETES` | bool | `true` | Enable Kubernetes tools |
| `config.data.APP_ENABLED_HARBOR` | bool | `true` | Enable Harbor registry tools |
| `config.data.APP_ENABLED_PROMETHEUS` | bool | `true` | Enable Prometheus metrics tools |
| `config.data.APP_ENABLED_DOCKER` | bool | `true` | Enable Docker API tools |
| `config.data.APP_ENABLED_HELM` | bool | `true` | Enable Helm integration |
| `config.data.APP_ENABLED_MEMORY` | bool | `true` | Enable memory/embedding capabilities |
| `config.data.APP_ENABLED_MYSQL` | bool | `true` | Enable mysql management capabilities |
| `config.data.LLM_URL` | string | `https://api.example-llm.com/v1` | LLM API base URL |
| `config.data.LLM_MODEL` | string | `"gpt-4.1"` | LLM model to use |
| `config.data.PROMETHEUS_URL` | string | `http://prometheus.monitoring.svc:9090` | Prometheus instance URL |
| `config.data.PROMETHEUS_USERNAME` | string | `""` | Prometheus username |
| `config.data.PROMETHEUS_PASSWORD` | string | `""` | Prometheus password |
| `config.data.HARBOR_URL` | string | `"https://harbor.registry.local"` | Harbor registry URL |
| `config.data.HARBOR_USERNAME` | string | `"robot$agent_bot"` | Harbor robot account username |
| `config.data.MILVUS_URL` | string | `"http://milvus.vector-db.svc:19530"` | Milvus vector DB URL |
| `config.data.MILVUS_USERNAME` | string | `""` | Milvus username |
| `config.data.MILVUS_PASSWORD` | string | `""` | Milvus password |
| `config.data.MEMORY_EMBEDDING_URL` | string | `"https://api.example-llm.com/v1/embeddings"` | URL for embedding model |
| `config.data.MEMORY_EMBEDDING_MODEL` | string | `"text-embedding-3-small"` | Embedding model identifier |
| `config.data.MEMORY_AUTO_ID` | bool | `true` | Auto-generate IDs for memory |
| `config.data.MEMORY_DROP_OLD` | bool | `false` | Drop old memory chunks |
| `config.data.MEMORY_THRESHOLD` | float | `0.8` | Similarity threshold for memory recall |
| `config.data.DOCKER_CLIENT` | string | `""` | Docker client host or socket |
| `config.data.MYSQL_HOST` | string | `"localhost"` | Hostname of the MySQL server |
| `config.data.MYSQL_USERNAME` | string | `"agent_user"` | MySQL username |
| `config.data.MYSQL_PORT` | int | `3306` | MySQL port |
| `config.data.MYSQL_SSL_VERIFY` | bool | `true` | Verify SSL cert for MySQL connection |
| `secrets.name` | string | `"my-agent-secrets"` | Kubernetes Secret name |
| `secrets.data.APP_SESSION_DB` | string | `"sqlite:///./sessions.db"` | SQLAlchemy DB URI for session store |
| `secrets.data.HARBOR_TOKEN` | string | `"changeme"` | Harbor robot account token |
| `secrets.data.LLM_TOKEN` | string | `"changeme"` | Token for LLM access |
| `secrets.data.MYSQL_PASSWORD` | string | `"changeme"` | MySQL database password |
| `service.name` | string | `"my-agent-service"` | Kubernetes service name |
| `service.type` | string | `"ClusterIP"` | Kubernetes service type |
| `service.port` | int | `8080` | Service port |
| `ingress.enabled` | bool | `true` | Enable ingress controller |
| `ingress.ingressClassName` | string | `"traefik"` | Ingress class name |
| `ingress.annotations` | map | `{}` | Ingress annotations |
| `ingress.host` | string | `"agent.eternium.local"` | Ingress hostname |
| `ingress.tls[0].secretName` | string | `"agent-eternium-tls"` | TLS secret name |
| `ingress.tls[0].hosts` | list | `["agent.eternium.local"]` | TLS hosts list |
| `serviceAccount.enabled` | bool | `true` | Whether to create a ServiceAccount |
| `serviceAccount.name` | string | `"my-agent-sa"` | Name of the ServiceAccount |
| `serviceAccount.annotations` | map | `{}` | Annotations for the ServiceAccount |
| `rbac.enabled` | bool | `true` | Enable RBAC roles and bindings |
| `postgresql.enabled` | bool | `false` | Enable bundled bitnami/postgresql subchart |

## Uninstall

To uninstall the chart and delete all associated resources:

```bash
helm uninstall eternium-agent
```