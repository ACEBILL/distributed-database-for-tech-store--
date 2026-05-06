import pytest
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app import create_app


@pytest.fixture
def app():
    """Create and configure a test app."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's CLI."""
    return app.test_cli_runner()


@pytest.fixture
def valid_token():
    """Return a valid JWT token for testing (from sample user NV001)."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJOVjAwMSIsImhvX3RlbiI6Ik5ndXnDqm4gVmFuIEEiLCJjaHVjX3Z1IjoiYWRtaW4iLCJtYV9waG9uZ19iYW4iOiJQQjAxIiwic2NvcGUiOiJjZW50cmFsIiwiZXhwIjo5OTk5OTk5OTk5fQ.signature"


@pytest.fixture
def invalid_token():
    """Return an invalid JWT token."""
    return "invalid.token.here"
