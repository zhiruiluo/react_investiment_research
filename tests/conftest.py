"""Pytest configuration - load .env before tests."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parents[1] / ".env"
if env_path.exists():
    load_dotenv(env_path)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test (requires API key)")
