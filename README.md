# Eternium Agency Crew – Homelab Agents

This directory contains the source code and configuration for the **Eternium Agency Crew**: a modular, multi-agent system designed to automate, monitor, and manage your homelab infrastructure.

## Overview

The agents in this project are Python-based and orchestrated via the `eternium` coordinator. Each agent is responsible for interacting with a specific service or platform in your homelab, such as Kubernetes, Docker, Helm, Prometheus, Harbor, MySQL, and more.

## Features

- **Modular agent architecture**: Easily enable or disable agents for different services.
- **Central coordinator**: The `eternium` agent delegates tasks to sub-agents based on your configuration.
- **Service integrations**: Out-of-the-box support for Kubernetes, Docker, Helm, Prometheus, Harbor, MySQL, and memory/embedding services.
- **Configurable via `.env`**: All service endpoints and credentials are managed through environment variables.
- **Containerized**: Deployable via Docker using the provided `Dockerfile`.

## Directory Structure

- `main.py` – Application entrypoint (FastAPI/Uvicorn server)
- `charts` - Helm chart to deploy the app into a kubernetes cluster
- `config.py` – Loads and parses environment configuration
- `eternium/` – Core agent logic and sub-agent modules
  - `agent.py` – Coordinator agent logic
  - `prompt.py` – Prompt templates for LLM-based agents
  - `sub_agents/` – Service-specific agents (docker, harbor, helm, kubernetes, memory, mysql, prometheus, etc)
- `.env` – Environment configuration for all agents and services
- `requirements.txt` – Python dependencies
- `Dockerfile` – Container build instructions

## Usage

1. **Configure**: Copy `.env.example` to `.env` and update with your service endpoints and credentials
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run locally**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080
   ```
4. **Or build and run with Docker**:
   ```bash
   docker build -t mogwai-agency .
   docker run --env-file .env -p 8080:8080 mogwai-agency
   ```

## Enabling/Disabling Agents

Control which agents are active by setting the corresponding `APP_ENABLED_*` variables in your `.env` file.

## Supported Integrations

- **Kubernetes**
- **Docker**
- **Helm**
- **Prometheus**
- **Harbor**
- **MySQL**
- **Memory/Embedding (Milvus, Ollama, etc.)**

## Security

- Store sensitive credentials in your `.env` file and keep it secure
- The application runs as a non-root user (`eternium`) in the container

## Contributing

Feel free to open issues or submit pull requests for new agents or improvements!
