"""Configuration models and loader."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource
from pydantic import BaseModel
import yaml

class OrchestratorSettings(BaseModel):
    max_revisits: int = 3
    action_timeout_seconds: float = 15.0
    yield_window_minutes: int = 20
    low_yield_threshold: int = 2
    saturation_evidence_threshold: int = 5

class ProviderSettings(BaseModel):
    vision_backend: str = "stub"
    ocr_backend: str = "stub"
    controller_backend: str = "stub"

class AppSettings(BaseSettings):
    """
    Main settings. Reads from defaults.yaml first, then overridden
    by environment variables (e.g. RT_ORCHESTRATOR__MAX_REVISITS=5).
    """
    model_config = SettingsConfigDict(
        env_prefix="RT_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore"
    )

    data_dir: Path = Path("data")
    orchestrator: OrchestratorSettings = OrchestratorSettings()
    providers: ProviderSettings = ProviderSettings()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            env_settings,
            init_settings,
            dotenv_settings,
            file_secret_settings,
        )

def load_settings(config_file: Path | str | None = None) -> AppSettings:
    """Load settings from defaults.yaml and env vars."""
    base_kwargs = {}
    default_path = Path(__file__).parent / "defaults.yaml"
    
    path_to_load = Path(config_file) if config_file else default_path
    
    if path_to_load.exists():
        with open(path_to_load, "r", encoding="utf-8") as f:
            base_kwargs = yaml.safe_load(f) or {}

    return AppSettings(**base_kwargs)
