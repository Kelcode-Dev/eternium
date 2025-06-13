"""Tools for adding to and querying a persistent Milvus vectorstore."""

from langchain_ollama import OllamaEmbeddings
from langchain_milvus import Milvus
from google.adk import Agent
from config import settings
from . import prompt
from typing import Optional

# Initialise the components for the memory system
QUERY_MEMORY_THRESHOLD = settings.memory.threshold
embeddings = OllamaEmbeddings(
    model=settings.memory.embedding_model,
    base_url=settings.memory.embedding_url
)

vector_store = Milvus(
    embedding_function=embeddings,
    collection_name="eternium_homelab_memory",
    connection_args={"uri": settings.milvus.url},
    auto_id=settings.memory.auto_id,
    drop_old=settings.memory.drop_old
)

def add_to_memory(fact: str, **kwargs) -> dict:
  """
  Adds a new piece of text (a fact or note) to the agent's long-term memory.
  Use this when the user says 'remember', 'take a note', etc.
  """
  print(f"--- MEMORY TOOL: Called add_to_memory ---")
  try:
    vector_store.add_texts([fact])
    return {"status": "success", "message": "The information has been added to long-term memory."}
  except Exception as e:
    return {"status": "error", "message": f"Failed to add fact to memory: {e}"}

def query_memory(query: str, include_metadata: Optional[bool] = False, **kwargs) -> list:
  """
  Searches memory for a query. Can optionally return metadata including unique IDs.
  Args:
      query: The search query string (should be concise keywords).
      include_metadata: If True, returns a list of dictionaries with full metadata (for deletion).
                        If False, returns a simple list of strings (for context).
  """
  print(f"--- MEMORY TOOL: Called query_memory (Metadata: {include_metadata}) ---")
  try:
    # If we need metadata, we must use the method that provides scores to filter.
    if include_metadata:
      results_with_scores = vector_store.similarity_search_with_score(query, k=3)
      if not results_with_scores: return [{"error": "No matching facts found."}]

      filtered_results = [
        {"id": doc.metadata.get("pk"), "content": doc.page_content, "score": round(score, 4)}
        for doc, score in results_with_scores if score < QUERY_MEMORY_THRESHOLD
      ]
      if not filtered_results: return [{"error": "Potential matches found but none met the relevance threshold."}]
      return filtered_results

    # Otherwise, we can use the simpler search method for speed.
    else:
      results = vector_store.similarity_search(query, k=1)
      if not results: return []
      return [doc.page_content for doc in results]

  except Exception as e:
      return [{"error": f"Error querying memory: {e}"}]

def delete_memory_by_id(doc_id: str, **kwargs) -> dict:
    """
    Deletes a specific fact from long-term memory using its unique ID.
    Use this as the second step after finding the correct ID with search_memory_for_deletion.
    """
    print(f"--- MEMORY TOOL: Called delete_memory_by_id for ID: {doc_id} ---")
    try:
        # LangChain's Milvus wrapper has a 'delete' method that takes a list of IDs
        result = vector_store.delete([doc_id])
        if result:
            return {"status": "success", "message": f"Successfully deleted memory with ID {doc_id}."}
        else:
            return {"status": "error", "message": "Deletion failed or ID not found."}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting memory by ID: {e}"}

def create_memory_agent(llm):
  """Factory function that builds and returns the Memory agent."""
  return Agent(
    name="memory_agent",
    model=llm,
    instruction=prompt.MEMORY_AGENT_INSTRUCTIONS,
    output_key="memory_output",
    tools=[add_to_memory, query_memory, delete_memory_by_id]
  )
