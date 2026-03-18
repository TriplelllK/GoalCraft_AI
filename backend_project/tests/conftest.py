"""
Pytest configuration: force in-memory backends before any app import.
This ensures tests run without PostgreSQL, Qdrant, or OpenAI.
"""
import os

# Must be set BEFORE any app module is imported (module-level singletons read env at import time)
os.environ["STORAGE_BACKEND"] = "memory"
os.environ["VECTOR_BACKEND"] = "memory"
os.environ.pop("POSTGRES_HOST", None)
os.environ.pop("QDRANT_URL", None)
os.environ.pop("OPENAI_API_KEY", None)  # no LLM in CI — rule-based only
