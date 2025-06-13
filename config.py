# config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

# Load environment variables from the .env file at the project root.
from dotenv import load_dotenv
load_dotenv()

# Configuration Models for Each Service/Agent
# Each class corresponds to a prefix in the top-level .env file.

class AppSettings(BaseSettings):
  """General application settings, loaded from APP_* variables."""
  name: str = "Eternium Agency"
  session_db: str = "sqlite:///./sessions.db"
  allowed_origins_str: str = "http://localhost,http://localhost:8080,*"
  serve_web_ui: bool = True
  host: str = "0.0.0.0"
  port: int = 8080

  # Agent enablement flags
  enabled_docker: bool = True
  enabled_harbor: bool = True
  enabled_helm: bool = True
  enabled_kubernetes: bool = True
  enabled_memory: bool = True
  enabled_mysql: bool = True
  enabled_prometheus: bool = True

  model_config = SettingsConfigDict(env_prefix='APP_')

  @property
  def allowed_origins(self) -> List[str]:
    """Parses the comma-separated string into a proper list."""
    return [origin.strip() for origin in self.allowed_origins_str.split(',')]

class LLMSettings(BaseSettings):
  """Configuration for the primary LLM, loaded from LLM_* variables."""
  url: Optional[str] = None
  token: Optional[str] = None
  model: Optional[str] = None
  model_config = SettingsConfigDict(env_prefix='LLM_')

class PrometheusSettings(BaseSettings):
  """Configuration for the Prometheus service."""
  url: str = "http://localhost:9090"
  username: Optional[str] = None
  password: Optional[str] = None
  model_config = SettingsConfigDict(env_prefix='PROMETHEUS_')

class HarborSettings(BaseSettings):
  """Configuration and credentials for the Harbor service."""
  url: str
  username: str
  token: str
  ssl_verify: bool = True
  model_config = SettingsConfigDict(env_prefix='HARBOR_')

class MilvusSettings(BaseSettings):
  """Configuration for the Milvus vector database service."""
  url: str = "http://localhost:19530"
  username: Optional[str] = None
  password: Optional[str] = None
  model_config = SettingsConfigDict(env_prefix='MILVUS_')

class MemorySettings(BaseSettings):
  """Configuration for the Memory Agent's embedding model."""
  embedding_url: str
  embedding_model: str = "mxbai-embed-large:latest"
  auto_id: bool = True
  drop_old: bool = False
  threshold: float = 0.7
  model_config = SettingsConfigDict(env_prefix='MEMORY_')

class MysqlSettings(BaseSettings):
  """Configuration for the MySQL Agent"""
  host: str
  username: Optional[str] = None
  password: Optional[str] = None
  port: int = 3306
  model_config = SettingsConfigDict(env_prefix='MYSQL_')

class DockerSettings(BaseSettings):
  """Configuration for the Docker agent."""
  # This agent doesn't need env vars, but we have a class for consistency.
  client: Optional[str] = None
  model_config = SettingsConfigDict(env_prefix='DOCKER_')

class HelmSettings(BaseSettings):
  """Configuration for the Docker agent."""
  # This agent doesn't need env vars, but we have a class for consistency.
  pass

# --- The Master Settings Class ---
class Settings(BaseSettings):
  """The main, globally accessible settings object, organized by component."""
  app: AppSettings = AppSettings()
  llm: LLMSettings = LLMSettings()
  prometheus: PrometheusSettings = PrometheusSettings()
  harbor: HarborSettings = HarborSettings()
  milvus: MilvusSettings = MilvusSettings()
  memory: MemorySettings = MemorySettings()
  docker: DockerSettings = DockerSettings()
  helm: HelmSettings = HelmSettings()
  mysql: MysqlSettings = MysqlSettings()

# --- Global Singleton ---
settings = Settings()
