"""Shared test fixtures for Jupiter Voice."""

import pytest

from jupiter_voice.config import JupiterConfig


@pytest.fixture
def default_config():
    """Return a default JupiterConfig."""
    return JupiterConfig()
