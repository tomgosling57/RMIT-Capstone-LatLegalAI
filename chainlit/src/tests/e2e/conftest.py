"""
Pytest configuration for Chainlit service end-to-end tests.

Provides:
  - Service-availability helpers (port check, container check, HTTP check)
  - Session-scoped URL fixture for the Chainlit service
  - Custom pytest markers for conditional test skipping
"""

import pytest
import requests
import subprocess
import socket

# ---------------------------------------------------------------------------
# Service URLs
# ---------------------------------------------------------------------------
CHAINLIT_URL = "http://localhost:80/chat"  # Chainlit via Nginx

# Container names
CHAINLIT_CONTAINER = "latmatrix-chainlit"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def is_port_open(host: str, port: int, timeout: float = 2) -> bool:
    """Return True if the TCP port is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except socket.error:
        return False


def is_container_running(container_name: str) -> bool:
    """Return True if a Docker container with the given name is running."""
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                f"name={container_name}",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return container_name in result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def is_service_responding(url: str, timeout: float = 5) -> bool:
    """Return True if the service returns a non-5xx response."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code < 500
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


# ---------------------------------------------------------------------------
# URL fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def chainlit_url() -> str:
    """Return the external URL for the Chainlit service (via Nginx)."""
    return CHAINLIT_URL


# ---------------------------------------------------------------------------
# Marker registration
# ---------------------------------------------------------------------------


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "chainlit_required: mark test as requiring the Chainlit service to be running",
    )


# ---------------------------------------------------------------------------
# Auto-skip logic
# ---------------------------------------------------------------------------


def pytest_runtest_setup(item):
    if item.get_closest_marker("chainlit_required"):
        if not is_container_running(CHAINLIT_CONTAINER):
            pytest.skip(
                f"Chainlit container '{CHAINLIT_CONTAINER}' not found. "
                "Start the stack with: docker-compose up -d"
            )
        if not is_port_open("localhost", 80):
            pytest.skip("Nginx (port 80) not accessible.")
        if not is_service_responding(CHAINLIT_URL, timeout=5):
            pytest.skip(f"Chainlit service not responding at {CHAINLIT_URL}")
