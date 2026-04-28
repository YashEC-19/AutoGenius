#!/usr/bin/env python3
# ============================================================
# AutoGenius — Environment Setup Verification Script
# Run this FIRST to confirm everything is ready before
# running agents or pipelines.
#
# Usage: python setup_check.py
# ============================================================

import sys
import os
import subprocess
from pathlib import Path

# ── Rich for pretty output ────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None


def section(title: str):
    if console:
        console.rule(f"[bold cyan]{title}[/bold cyan]")
    else:
        print(f"\n{'='*50}\n{title}\n{'='*50}")


def ok(msg: str):
    print(f"  ✅  {msg}")


def warn(msg: str):
    print(f"  ⚠️   {msg}")


def fail(msg: str):
    print(f"  ❌  {msg}")


# ── 1. Python version ─────────────────────────────────────────
section("1. Python Version")
major = sys.version_info.major
minor = sys.version_info.minor
version_str = f"{major}.{minor}.{sys.version_info.micro}"

if major == 3 and minor >= 10:
    ok(f"Python {version_str} — compatible ✓")
else:
    fail(f"Python {version_str} — need 3.10+")
    sys.exit(1)


# ── 2. Required packages ──────────────────────────────────────
section("2. Package Availability")

REQUIRED_PACKAGES = {
    "groq":                 "Groq SDK",
    "crewai":               "CrewAI agent framework",
    "langchain":            "LangChain orchestration",
    "langchain_groq":       "LangChain-Groq integration",
    "langchain_community":  "LangChain community tools",
    "pydantic":             "Data validation",
    "dotenv":               "Env file loader",
    "rich":                 "Terminal formatting",
    "requests":             "HTTP client (image gen)",
    "PIL":                  "Pillow image processing",
}

missing = []
for pkg, label in REQUIRED_PACKAGES.items():
    try:
        __import__(pkg)
        ok(f"{label} ({pkg})")
    except ImportError:
        fail(f"{label} ({pkg}) — NOT INSTALLED")
        missing.append(pkg)

if missing:
    print(f"\n⚠️  Missing packages detected.")
    print(f"   Run: pip install -r requirements.txt\n")


# ── 3. .env file check ────────────────────────────────────────
section("3. Environment File")

env_path = Path(".env")
env_example_path = Path(".env.example")

if env_path.exists():
    ok(".env file found")
    # Check for key presence without exposing it
    with open(env_path) as f:
        content = f.read()
    if "GROQ_API_KEY" in content and "your_groq_api_key_here" not in content:
        ok("GROQ_API_KEY is set in .env")
    else:
        warn("GROQ_API_KEY is missing or still set to placeholder in .env")
        print("   → Copy .env.example to .env and fill in your Groq key")
        print("   → Get free key at: https://console.groq.com")
else:
    fail(".env file not found")
    if env_example_path.exists():
        print("   → Run: cp .env.example .env")
        print("   → Then fill in GROQ_API_KEY")
    else:
        warn(".env.example also missing — re-download the project")


# ── 4. Groq API connectivity ──────────────────────────────────
section("4. Groq API Connectivity")

try:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY", "")

    if not api_key or api_key == "your_groq_api_key_here":
        warn("Skipping Groq connectivity test — no API key set")
    else:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say: AUTOGENIUS_OK"}],
            max_tokens=20,
        )
        reply = response.choices[0].message.content.strip()
        if "AUTOGENIUS_OK" in reply or len(reply) > 0:
            ok(f"Groq API connected — model responded ✓")
        else:
            warn(f"Groq API responded but with unexpected output: {reply}")
except Exception as e:
    fail(f"Groq API connection failed: {e}")


# ── 5. Output directory ───────────────────────────────────────
section("5. Output Directory")

output_dir = Path("./outputs")
output_dir.mkdir(exist_ok=True)
if output_dir.exists():
    ok(f"Output directory ready: {output_dir.resolve()}")


# ── 6. Pollinations.ai check ──────────────────────────────────
section("6. Image Generation (Pollinations.ai)")
try:
    import requests
    resp = requests.get("https://image.pollinations.ai", timeout=5)
    if resp.status_code < 500:
        ok("Pollinations.ai is reachable — image generation ready ✓")
    else:
        warn(f"Pollinations.ai returned status {resp.status_code}")
except Exception as e:
    warn(f"Pollinations.ai not reachable: {e} — check your internet connection")


# ── 7. Summary ────────────────────────────────────────────────
section("Setup Summary")

if not missing and env_path.exists():
    print("""
  ╔══════════════════════════════════════════╗
  ║   ✅  AutoGenius environment is ready!   ║
  ║                                          ║
  ║   Next step:                             ║
  ║   → python agents/langchain_tools.py     ║
  ╚══════════════════════════════════════════╝
""")
else:
    print("""
  ╔══════════════════════════════════════════╗
  ║   ⚠️  Setup incomplete — see issues above ║
  ║                                          ║
  ║   Fix the issues then re-run:            ║
  ║   → python setup_check.py               ║
  ╚══════════════════════════════════════════╝
""")
