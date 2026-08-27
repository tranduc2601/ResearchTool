import os
from pathlib import Path

from research_tool.config.settings import load_settings

def test_load_settings_defaults():
    settings = load_settings()
    assert settings.data_dir == Path("data")
    assert settings.orchestrator.max_revisits == 3
    assert settings.orchestrator.action_timeout_seconds == 15.0
    assert settings.providers.vision_backend == "stub"

def test_load_settings_env_override(monkeypatch):
    monkeypatch.setenv("RT_ORCHESTRATOR__MAX_REVISITS", "10")
    monkeypatch.setenv("RT_PROVIDERS__VISION_BACKEND", "openai")
    monkeypatch.setenv("RT_DATA_DIR", "/tmp/test_data")
    
    settings = load_settings()
    
    assert settings.orchestrator.max_revisits == 10
    assert settings.providers.vision_backend == "openai"
    assert settings.data_dir == Path("/tmp/test_data")
    # Verify defaults are kept for other fields
    assert settings.orchestrator.action_timeout_seconds == 15.0

def test_load_settings_missing_file():
    settings = load_settings("nonexistent_file.yaml")
    # Should fall back to Pydantic field defaults
    assert settings.orchestrator.max_revisits == 3
    assert settings.providers.vision_backend == "stub"
