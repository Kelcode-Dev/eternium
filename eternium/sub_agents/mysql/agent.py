"""Tools for interacting with a MySQL database as a DBA using SQLAlchemy."""
import os
import subprocess
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from google.adk import Agent
from config import settings
from . import prompt

# Setup the SQLAlchemy engine (global)
DATABASE_URL = f"mysql+mysqlconnector://{settings.mysql.username}:{settings.mysql.password}@{settings.mysql.host}:{settings.mysql.port}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# --- Tool Functions ---

def create_database(db_name: str, **kwargs) -> dict:
  """Creates a new database (schema) in MySQL."""
  print(f"--- TOOL: Called create_database for '{db_name}' ---")
  try:
    with engine.connect() as conn:
      conn.execute(text(f"CREATE DATABASE `{db_name}`"))
    return {"status": "success", "message": f"Database '{db_name}' created successfully."}
  except SQLAlchemyError as e:
    return {"status": "error", "message": str(e.__cause__ or e)}

def manage_user(username: str, action: str, password: str, **kwargs) -> dict:
  """Creates or drops a user in MySQL. Action must be 'create' or 'drop'."""
  print(f"--- TOOL: Called manage_user for '{username}' with action '{action}' ---")
  if action.lower() not in ['create', 'drop']:
    return {"status": "error", "message": "Invalid action. Must be 'create' or 'drop'."}

  try:
    with engine.connect() as conn:
      if action.lower() == 'create':
        if not password:
          return {"status": "error", "message": "Password is required to create a user."}
        conn.execute(text(f"CREATE USER '{username}'@'%' IDENTIFIED BY :pwd"), {"pwd": password})
        message = f"User '{username}' created successfully."
      else:
        conn.execute(text(f"DROP USER '{username}'@'%'"))
        message = f"User '{username}' dropped successfully."
      conn.execute(text("FLUSH PRIVILEGES"))
    return {"status": "success", "message": message}
  except SQLAlchemyError as e:
      return {"status": "error", "message": str(e.__cause__ or e)}

def grant_privileges(username: str, db_name: str, privileges: str, **kwargs) -> dict:
  """Grants specific privileges to a user on a database."""
  print(f"--- TOOL: Granting '{privileges}' on '{db_name}' to '{username}' ---")
  try:
    with engine.connect() as conn:
      conn.execute(text(f"GRANT {privileges} ON `{db_name}`.* TO '{username}'@'%'"))
      conn.execute(text("FLUSH PRIVILEGES"))
    return {"status": "success", "message": f"Privileges granted successfully."}
  except SQLAlchemyError as e:
    return {"status": "error", "message": str(e.__cause__ or e)}

def backup_database(db_name: str, **kwargs) -> dict:
  """
  Creates a backup of a specific database using mysqldump.
  The backup is stored on a persistent volume at '/backups'.
  """
  print(f"--- ACTION TOOL: Called backup_database for '{db_name}' ---")
  backup_dir = "/backups"
  if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  backup_file = f"{backup_dir}/{db_name}_{timestamp}.sql"

  command = [
    "mysqldump",
    "-h", settings.mysql.host,
    "-P", str(settings.mysql.port),
    "-u", settings.mysql.username,
    f"--password={settings.mysql.password}",
    db_name
  ]

  try:
    with open(backup_file, "w") as f:
      subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True, check=True)
    return {"status": "success", "message": f"Backup completed successfully. File saved to {backup_file}."}
  except subprocess.CalledProcessError as e:
    return {"status": "error", "message": "mysqldump failed.", "details": e.stderr}
  except Exception as e:
    return {"status": "error", "message": str(e)}

def run_sql_query(query: str, db_name: str, **kwargs) -> list[dict]:
  """
  Executes a raw SQL query against a specific database and returns the result.
  Handles both data retrieval (SELECT) and data modification (INSERT, UPDATE) queries.
  """
  print(f"--- TOOL: Running SQL query on database '{db_name}': '{query[:100]}...' ---")
  try:
    db_url = f"{DATABASE_URL}/{db_name}"
    db_engine = create_engine(db_url, pool_pre_ping=True)

    with db_engine.connect() as conn:
      result = conn.execute(text(query))
      if result.returns_rows:
        return [dict(row) for row in result.mappings().all()] or []
      else:
        return [{"status": "success", "rows_affected": result.rowcount}]
  except SQLAlchemyError as e:
    return [{"error": str(e.__cause__ or e)}]

def create_mysql_agent(llm) -> Agent:
  """Factory function to create the MySQL DBA Agent."""
  return Agent(
    name="mysql_dba",
    model=llm,
    instruction=prompt.MYSQL_DBA_INSTRUCTIONS,
    tools=[
      create_database,
      manage_user,
      grant_privileges,
      backup_database,
      run_sql_query
    ],
  )
