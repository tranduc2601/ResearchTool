"""Configuration models and loader."""
from pathlib import Path
import sys
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource
from pydantic import BaseModel, Field, model_validator

class OrchestratorSettings(BaseModel):
    max_revisits: int = 3
    action_timeout_seconds: float = 15.0
    yield_window_minutes: int = 20
    low_yield_threshold: int = 2
    saturation_evidence_threshold: int = 5
    max_consecutive_scrolls: int = 3
    checkpoint_interval_actions: int = 10

class ProviderSettings(BaseModel):
    vision_backend: str = "qwen2-vl"
    vision_model_path: str = "Qwen/Qwen2-VL-2B-Instruct"
    ocr_backend: str = "paddle"
    tesseract_cmd: str | None = None
    controller_backend: str = "windows"
    hf_token: str | None = None
    openai_api_key: str | None = None

class AndroidSettings(BaseModel):
    device_serial: str | None = None
    use_scrcpy: bool = False
    scrcpy_path: str = "scrcpy"
    scrcpy_max_fps: int = 5
    scrcpy_bitrate: str = "2M"
    adb_path: str = "adb"

class DedupSettings(BaseModel):
    levenshtein_same_threshold: float = 0.95
    levenshtein_prob_same_threshold: float = 0.80
    image_hash_distance_threshold: int = 5



def get_app_root() -> Path:
    """Return the absolute path to the application root directory."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        return Path(sys.executable).parent.resolve()
    else:
        # Running from source (src/research_tool/config/settings.py -> root)
        return Path(__file__).parent.parent.parent.parent.resolve()

class AppSettings(BaseSettings):
    """
    Main settings. Reads from defaults.yaml first, then overridden
    by environment variables (e.g. RT_ORCHESTRATOR__MAX_REVISITS=5).
    """
    model_config = SettingsConfigDict(
        env_prefix="RT_",
        env_nested_delimiter="__",
        env_file=str(get_app_root() / ".env"),
        extra="ignore"
    )

    data_dir: Path = Field(default_factory=lambda: get_app_root() / "data")
    orchestrator: OrchestratorSettings = OrchestratorSettings()
    providers: ProviderSettings = ProviderSettings()
    android: AndroidSettings = AndroidSettings()
    dedup: DedupSettings = DedupSettings()

    @model_validator(mode="after")
    def resolve_paths(self) -> "AppSettings":
        """Ensure paths are absolute relative to app root."""
        if not self.data_dir.is_absolute():
            self.data_dir = get_app_root() / self.data_dir
        return self

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
    import logging
    
    base_kwargs = {}
    default_path = Path(__file__).parent / "defaults.yaml"
    
    path_to_load = Path(config_file) if config_file else default_path
    
    if path_to_load.exists():
        with open(path_to_load, "r", encoding="utf-8") as f:
            base_kwargs = yaml.safe_load(f) or {}

    settings = AppSettings(**base_kwargs)
    
    # Startup self-check
    logging.info(f"App Root: {get_app_root()}")
    logging.info(f"Resolved Data Dir: {settings.data_dir}")
    logging.info(f"Env file path: {get_app_root() / '.env'}")
    
    return settings
