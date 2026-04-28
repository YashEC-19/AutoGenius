#!/usr/bin/env python3
"""
AutoGenius — STEP 8 & 9 & 10: Multimodal Vision Pipeline
LangChain + Groq (text) + Pollinations.ai (image generation)
"""

import os, sys, json, re, time, argparse, urllib.parse
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"
OUTPUTS_DIR  = Path(__file__).parent.parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


# ══════════════════════════════════════════════════════════════════════
#  STEP 8 — LangChain Text Chain  (narrative + image prompt)
# ══════════════════════════════════════════════════════════════════════

def generate_narrative(user_prompt: str) -> dict:
    """
    LangChain chain: user prompt → design narrative + optimised image prompt.
    Returns {"narrative": str, "image_prompt": str, "specs": dict}
    """
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate

    console.print(f"\n  [cyan]📝 Narrative Chain → generating design text...[/cyan]")

    llm = ChatGroq(model=GROQ_MODEL, temperature=0.7,
                   max_tokens=1200, groq_api_key=GROQ_API_KEY)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an elite automotive concept designer and journalist. "
         "Respond ONLY with valid JSON, no markdown fences."),
        ("human", """The user wants to visualise this automotive concept:

"{concept}"

Return exactly this JSON:
{{
  "title": "short catchy title for this concept (max 8 words)",
  "narrative": "A rich 4-paragraph design narrative. Cover: (1) overall design philosophy and silhouette, (2) powertrain and performance, (3) interior and technology, (4) cultural significance and target driver. Each paragraph 3-4 sentences.",
  "image_prompt": "A highly detailed Stable Diffusion prompt optimised for photorealistic automotive photography. Include: car style, exterior colors, setting/environment, lighting, camera angle, render quality tags. Max 80 words.",
  "specs": {{
    "body_style": "",
    "powertrain": "",
    "estimated_hp": 0,
    "top_speed_mph": 0,
    "design_era": "",
    "target_market": ""
  }}
}}""")
    ])

    chain = prompt | llm
    result = chain.invoke({"concept": user_prompt})
    raw = result.content.strip()

    # Strip markdown fences if present
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if JSON malformed
        data = {
            "title": user_prompt[:50],
            "narrative": raw[:800],
            "image_prompt": f"photorealistic {user_prompt}, automotive photography, studio lighting, 8k, ultra detailed",
            "specs": {}
        }

    console.print(f"  [green]✅ Narrative done — title: '{data.get('title', '')}'[/green]")
    return data


# ══════════════════════════════════════════════════════════════════════
#  STEP 9 — Pollinations.ai Image Generation
# ══════════════════════════════════════════════════════════════════════

def generate_image(image_prompt: str, title: str) -> dict:
    """
    Calls Pollinations.ai to generate a car design image.
    Returns {"url": str, "local_path": str, "success": bool}
    """
    console.print(f"\n  [cyan]🎨 Image Generation → Pollinations.ai...[/cyan]")

    # Add automotive quality tags
    enhanced = (
        image_prompt.rstrip(".") +
        ", photorealistic, 8k UHD, professional automotive photography, "
        "cinematic lighting, sharp focus, no text, no watermark"
    )

    encoded   = urllib.parse.quote(enhanced)
    # Add seed for reproducibility and nologo to keep it clean
    image_url = f"{POLLINATIONS_BASE}/{encoded}?width=1280&height=720&seed=42&nologo=true"

    console.print(f"  [dim]URL: {image_url[:80]}...[/dim]")

    try:
        # First request — Pollinations generates the image
        console.print(f"  [yellow]⏳ Waiting for image generation (15-30s)...[/yellow]")
        resp = requests.get(image_url, timeout=60, stream=True)
        resp.raise_for_status()

        # Save locally
        safe_title = re.sub(r'[^a-z0-9_]', '_', title.lower())[:40]
        ts         = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path   = OUTPUTS_DIR / f"vision_{safe_title}_{ts}.jpg"

        with open(img_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        size_kb = img_path.stat().st_size // 1024
        console.print(f"  [green]✅ Image saved → {img_path.name} ({size_kb} KB)[/green]")

        return {
            "url":        image_url,
            "local_path": str(img_path),
            "filename":   img_path.name,
            "size_kb":    size_kb,
            "success":    True,
        }

    except requests.exceptions.Timeout:
        console.print(f"  [yellow]⚠️  Image generation timed out — URL still valid[/yellow]")
        return {"url": image_url, "local_path": None, "success": False,
                "error": "timeout — open URL in browser to view"}

    except Exception as e:
        console.print(f"  [red]❌ Image error: {e}[/red]")
        return {"url": image_url, "local_path": None, "success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════
#  STEP 10 — Combined Multimodal Output
# ══════════════════════════════════════════════════════════════════════

def build_multimodal_output(user_prompt: str, narrative_data: dict,
                             image_data: dict) -> dict:
    """Package everything into the final multimodal output format."""
    ts = datetime.now().isoformat()

    output = {
        "autogenius_vision": {
            "version":   "1.0",
            "schema":    "automotive_concept_v1",
            "generated": ts,
        },
        "input": {
            "user_prompt": user_prompt,
        },
        "pipeline": {
            "step_8_text":  "LangChain + Groq → narrative + image prompt",
            "step_9_image": "Pollinations.ai → photorealistic render",
            "step_10_out":  "Combined multimodal output",
        },
        "concept": {
            "title":        narrative_data.get("title", ""),
            "narrative":    narrative_data.get("narrative", ""),
            "image_prompt": narrative_data.get("image_prompt", ""),
            "specs":        narrative_data.get("specs", {}),
        },
        "image": image_data,
        "combined_markdown": build_markdown(narrative_data, image_data, user_prompt),
    }
    return output


def build_markdown(narrative_data: dict, image_data: dict, prompt: str) -> str:
    title     = narrative_data.get("title", prompt)
    narrative = narrative_data.get("narrative", "")
    specs     = narrative_data.get("specs", {})
    img_url   = image_data.get("url", "")
    img_path  = image_data.get("local_path") or ""

    md = f"# 🚗 {title}\n\n"
    md += f"> *Concept visualisation for: \"{prompt}\"*\n\n"
    md += "---\n\n"

    if img_path:
        md += f"![{title}]({img_url})\n\n"
    else:
        md += f"**🖼️ Image:** [View Generated Render]({img_url})\n\n"

    md += "---\n\n"
    md += "## 📖 Design Narrative\n\n"
    md += narrative + "\n\n"

    if specs:
        md += "---\n\n## 📊 Concept Specifications\n\n"
        md += "| Attribute | Value |\n|---|---|\n"
        for k, v in specs.items():
            if v:
                md += f"| {k.replace('_', ' ').title()} | {v} |\n"

    md += "\n---\n*Generated by AutoGenius Vision Lab — Powered by Groq + Pollinations.ai*\n"
    return md


def display_output(output: dict):
    """Pretty print the multimodal output."""
    concept = output["concept"]
    image   = output["image"]

    console.print(Panel.fit(
        f"[bold cyan]🎨 AutoGenius Vision Lab — Output[/bold cyan]\n"
        f"[white]STEPS 8–10: Multimodal Automotive Concept[/white]",
        border_style="cyan"
    ))

    # Concept info
    t1 = Table(title="🚗 Concept", box=box.ROUNDED, show_header=False)
    t1.add_column("Field", style="cyan", width=16)
    t1.add_column("Value", style="white")
    t1.add_row("Title",   concept["title"])
    for k, v in concept.get("specs", {}).items():
        if v:
            t1.add_row(k.replace("_", " ").title(), str(v))
    console.print(t1)

    # Narrative preview
    narrative_preview = concept["narrative"][:400] + "..." \
        if len(concept["narrative"]) > 400 else concept["narrative"]
    console.print(Panel(narrative_preview, title="📖 Narrative Preview", border_style="dim"))

    # Image info
    t2 = Table(title="🖼️ Generated Image", box=box.ROUNDED, show_header=False)
    t2.add_column("Field", style="cyan", width=16)
    t2.add_column("Value", style="white")
    t2.add_row("Status",  "✅ Downloaded" if image.get("local_path") else "⚠️  URL only")
    t2.add_row("File",    image.get("filename", "N/A"))
    t2.add_row("Size",    f"{image.get('size_kb', 0)} KB" if image.get("size_kb") else "N/A")
    t2.add_row("URL",     image.get("url", "")[:60] + "...")
    console.print(t2)

    console.print(Panel.fit(
        "[bold green]✅ STEPS 8–10 Complete — Multimodal Output Ready![/bold green]\n\n"
        "[white]Files saved in outputs/:\n"
        "  • vision_*.jpg  — Generated car image\n"
        "  • vision_output_*.json  — Full structured output\n"
        "  • vision_report_*.md    — Markdown concept report\n\n"
        "Next → STEP 11: Laravel Automotive App[/white]",
        border_style="green"
    ))


# ══════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════

def run_vision_pipeline(prompt: str) -> dict:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    console.print(Panel.fit(
        f"[bold cyan]🎨 AutoGenius — Vision Lab[/bold cyan]\n"
        f"[white]STEPS 8–10: LangChain + Groq + Pollinations.ai[/white]\n"
        f"[yellow]Concept:[/yellow] {prompt}",
        border_style="cyan"
    ))

    # STEP 8 — Text pipeline
    console.print("\n[bold]━━━ STEP 8: LangChain Narrative Chain ━━━[/bold]")
    narrative_data = generate_narrative(prompt)

    # STEP 9 — Image generation
    console.print("\n[bold]━━━ STEP 9: Pollinations Image Generation ━━━[/bold]")
    image_data = generate_image(narrative_data["image_prompt"], narrative_data["title"])

    # STEP 10 — Combined output
    console.print("\n[bold]━━━ STEP 10: Combined Multimodal Output ━━━[/bold]")
    output = build_multimodal_output(prompt, narrative_data, image_data)

    # Save files
    safe = re.sub(r'[^a-z0-9_]', '_', prompt.lower())[:35]
    json_path = OUTPUTS_DIR / f"vision_output_{safe}_{ts}.json"
    md_path   = OUTPUTS_DIR / f"vision_report_{safe}_{ts}.md"

    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(output["combined_markdown"], encoding="utf-8")

    console.print(f"\n  💾 JSON  → [cyan]{json_path.name}[/cyan]")
    console.print(f"  💾 MD    → [cyan]{md_path.name}[/cyan]")

    display_output(output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoGenius Vision Lab — STEPS 8-10")
    parser.add_argument(
        "--prompt",
        default="a futuristic electric hypercar with sleek aerodynamic body, glowing blue accents, set against a neon-lit city at night",
        help="Automotive concept to visualise"
    )
    args = parser.parse_args()
    run_vision_pipeline(args.prompt)