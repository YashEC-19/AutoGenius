# ============================================================
# AutoGenius — Central Configuration Loader
# File: autogenius/config.py
# Used by: agents, vision pipeline, utilities
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Optional

# ── Load .env file ────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
    print(f"✅ [Config] Loaded environment from {ENV_FILE}")
else:
    # Try loading from current working directory
    load_dotenv()
    print("⚠️  [Config] No .env found in project root — reading from system env")


# ── Groq Configuration ────────────────────────────────────────
@dataclass
class GroqConfig:
    api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    researcher_model: str = field(
        default_factory=lambda: os.getenv("GROQ_RESEARCHER_MODEL", "llama-3.3-70b-versatile")
    )
    writer_model: str = field(
        default_factory=lambda: os.getenv("GROQ_WRITER_MODEL", "llama-3.3-70b-versatile")
    )
    vision_model: str = field(
        default_factory=lambda: os.getenv("GROQ_VISION_MODEL", "llama-3.3-70b-versatile")
    )
    researcher_temperature: float = field(
        default_factory=lambda: float(os.getenv("RESEARCHER_TEMPERATURE", "0.2"))
    )
    writer_temperature: float = field(
        default_factory=lambda: float(os.getenv("WRITER_TEMPERATURE", "0.6"))
    )
    vision_temperature: float = field(
        default_factory=lambda: float(os.getenv("VISION_TEMPERATURE", "0.7"))
    )

    def validate(self) -> bool:
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            raise ValueError(
                "❌ GROQ_API_KEY is not set!\n"
                "   1. Go to https://console.groq.com\n"
                "   2. Create a free account\n"
                "   3. Copy your API key\n"
                "   4. Add it to .env as GROQ_API_KEY=your_key_here"
            )
        return True


# ── Agent Configuration ───────────────────────────────────────
@dataclass
class AgentConfig:
    max_iterations: int = field(
        default_factory=lambda: int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
    )
    verbose: bool = field(
        default_factory=lambda: os.getenv("AGENT_VERBOSE", "true").lower() == "true"
    )
    save_states: bool = field(
        default_factory=lambda: os.getenv("SAVE_AGENT_STATES", "true").lower() == "true"
    )


# ── Output Configuration ─────────────────────────────────────
@dataclass
class OutputConfig:
    output_dir: Path = field(
        default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "./outputs"))
    )

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)


# ── Pollinations (Image Gen) Configuration ───────────────────
@dataclass
class ImageConfig:
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "POLLINATIONS_BASE_URL", "https://image.pollinations.ai/prompt"
        )
    )
    width: int = field(
        default_factory=lambda: int(os.getenv("POLLINATIONS_WIDTH", "1280"))
    )
    height: int = field(
        default_factory=lambda: int(os.getenv("POLLINATIONS_HEIGHT", "720"))
    )
    model: str = field(
        default_factory=lambda: os.getenv("POLLINATIONS_MODEL", "flux")
    )


# ── App Configuration ─────────────────────────────────────────
@dataclass
class AppConfig:
    name: str = field(default_factory=lambda: os.getenv("APP_NAME", "AutoGenius"))
    env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    debug: bool = field(
        default_factory=lambda: os.getenv("APP_DEBUG", "true").lower() == "true"
    )


# ── Master Config ─────────────────────────────────────────────
@dataclass
class AutoGeniusConfig:
    """
    Single config object passed throughout the entire application.
    Usage:
        from config import get_config
        cfg = get_config()
        print(cfg.groq.researcher_model)
    """
    groq: GroqConfig = field(default_factory=GroqConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    image: ImageConfig = field(default_factory=ImageConfig)
    app: AppConfig = field(default_factory=AppConfig)


# ── Singleton getter ──────────────────────────────────────────
_config_instance: Optional[AutoGeniusConfig] = None


def get_config() -> AutoGeniusConfig:
    """Returns a singleton AutoGeniusConfig instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AutoGeniusConfig()
    return _config_instance


def print_config_summary():
    """Prints a safe summary of the loaded config (no secrets)."""
    cfg = get_config()
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="⚙️  AutoGenius Config Summary", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="bold white")
    table.add_column("Value", style="green")

    table.add_row("App Name", cfg.app.name)
    table.add_row("Environment", cfg.app.env)
    table.add_row("Debug Mode", str(cfg.app.debug))
    table.add_row("─────────────────", "─────────────────────────────")
    table.add_row("Groq Key Set", "✅ Yes" if cfg.groq.api_key and cfg.groq.api_key != "your_groq_api_key_here" else "❌ No")
    table.add_row("Researcher Model", cfg.groq.researcher_model)
    table.add_row("Writer Model", cfg.groq.writer_model)
    table.add_row("Vision Model", cfg.groq.vision_model)
    table.add_row("─────────────────", "─────────────────────────────")
    table.add_row("Agent Max Iterations", str(cfg.agent.max_iterations))
    table.add_row("Agent Verbose", str(cfg.agent.verbose))
    table.add_row("─────────────────", "─────────────────────────────")
    table.add_row("Output Directory", str(cfg.output.output_dir))
    table.add_row("Image Width", str(cfg.image.width))
    table.add_row("Image Height", str(cfg.image.height))
    table.add_row("Image Model", cfg.image.model)

    console.print(table)


# ── Run config check directly ─────────────────────────────────
if __name__ == "__main__":
    print_config_summary()
    cfg = get_config()
    try:
        cfg.groq.validate()
        print("\n✅ All configuration checks passed!")
    except ValueError as e:
        print(f"\n{e}")
