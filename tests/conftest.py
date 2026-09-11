

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest
from main import create_app
from services.config import Settings


def build_client(**overrides: object) -> TestClient:
    """A TestClient wired to the MOCK provider regardless of .env.

    Constructor kwargs beat the environment in pydantic-settings, so
    tests force the mock and shrink limits (max_upload_bytes=8 etc.)
    without touching files or spawning 25 MiB blobs.
    """
    settings = Settings(provider="mock", **overrides)  # type: ignore[arg-type]
    return TestClient(create_app(settings))


@pytest.fixture
def client() -> TestClient:
    return build_client()