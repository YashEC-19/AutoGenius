#!/usr/bin/env python3
"""
AutoGenius — Agent Output Formatter (STEP 6)
Reads the pipeline outputs and produces a clean,
structured final JSON + a pretty terminal summary.
"""

import os, sys, json, glob, argparse
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich import box

console = Console()

OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_latest_state(run_id: str | None = None) -> dict:
    """Load the most recent (or specified) FINAL_state JSON."""
    pattern = str(OUTPUTS_DIR / "FINAL_state_*.json")
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        raise FileNotFoundError("No FINAL_state_*.json files found in outputs/")

    if run_id:
        matches = [f for f in files if run_id in f]
        if not matches:
            raise FileNotFoundError(f"No state file found for run_id: {run_id}")
        path = matches[0]
    else:
        path = files[0]

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_report(run_id: str) -> str:
    """Load the markdown report for a given run_id."""
    pattern = str(OUTPUTS_DIR / f"FINAL_report_{run_id}_*.md")
    files = glob.glob(pattern)
    if not files:
        return "(report file not found)"
    return Path(files[0]).read_text(encoding="utf-8")


def load_logs(run_id: str) -> list:
    """Load agent logs for a given run_id."""
    pattern = str(OUTPUTS_DIR / f"agent_logs_{run_id}_*.json")
    files = glob.glob(pattern)
    if not files:
        return []
    with open(files[0], encoding="utf-8") as f:
        return json.load(f)


# ── Structured output builder ─────────────────────────────────────────────────

def build_structured_output(state: dict, report: str, logs: list) -> dict:
    """
    Produce the canonical AutoGenius structured output format.
    This is the 'Agent Output Format' required by STEP 6.
    """
    run_id    = state.get("crew_run_id", "unknown")
    car       = state.get("car", "unknown")
    rating    = state.get("rating", {})
    duration  = state.get("duration_sec", 0)
    timestamp = state.get("timestamp", datetime.now().isoformat())

    # Extract section titles from the markdown report
    sections = []
    for line in report.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            sections.append(line.lstrip("#").strip())

    # Build agent trace
    agent_trace = []
    for i, log in enumerate(logs):
        agent_trace.append({
            "step":      i + 1,
            "timestamp": log.get("timestamp"),
            "state":     log.get("state"),
            "message":   log.get("message", ""),
        })

    # Final structured output
    structured = {
        "autogenius_output": {
            "version":    "1.0",
            "schema":     "automotive_report_v1",
            "generated":  datetime.now().isoformat(),
        },
        "run_metadata": {
            "run_id":        run_id,
            "car":           car,
            "model":         state.get("model", ""),
            "timestamp":     timestamp,
            "duration_sec":  duration,
            "word_count":    state.get("word_count", len(report.split())),
            "pipeline":      "Researcher Agent → Handoff → Writer Agent",
            "framework":     "CrewAI + LangChain + Groq",
        },
        "agents": {
            "researcher": {
                "role":   "Automotive Research Specialist",
                "status": "complete",
                "output": "specs_json",
                "handoff_to": "writer",
            },
            "writer": {
                "role":   "Automotive Journalist",
                "status": "complete",
                "output": "markdown_report",
                "sections_produced": len(sections),
            },
        },
        "state_machine": {
            "transitions": state.get("state_machine", []),
            "agent_trace": agent_trace,
            "final_state": "COMPLETE",
        },
        "rating": {
            "performance": rating.get("performance", 0),
            "efficiency":  rating.get("efficiency",  0),
            "technology":  rating.get("technology",  0),
            "safety":      rating.get("safety",      0),
            "value":       rating.get("value",       0),
            "overall":     rating.get("overall",     0),
        },
        "report": {
            "format":   "markdown",
            "sections": sections,
            "preview":  report[:300] + "..." if len(report) > 300 else report,
            "full_report": report,
        },
        "files": state.get("files", {}),
    }

    return structured


# ── Pretty terminal display ───────────────────────────────────────────────────

def display_structured_output(output: dict):
    """Render the structured output as a rich terminal display."""

    meta  = output["run_metadata"]
    agent = output["agents"]
    rate  = output["rating"]
    rep   = output["report"]
    sm    = output["state_machine"]

    # ── Header ────────────────────────────────────────────────────
    console.print(Panel.fit(
        f"[bold cyan]🚗 AutoGenius — Agent Output Format[/bold cyan]\n"
        f"[white]STEP 6: Structured Pipeline Output[/white]",
        border_style="cyan"
    ))

    # ── Run Metadata ──────────────────────────────────────────────
    t1 = Table(title="📋 Run Metadata", box=box.ROUNDED, show_header=False)
    t1.add_column("Field", style="cyan", width=18)
    t1.add_column("Value", style="white")
    t1.add_row("Run ID",    meta["run_id"])
    t1.add_row("Car",       meta["car"])
    t1.add_row("Model",     meta["model"])
    t1.add_row("Framework", meta["framework"])
    t1.add_row("Duration",  f"{meta['duration_sec']:.1f}s")
    t1.add_row("Words",     str(meta["word_count"]))
    t1.add_row("Pipeline",  meta["pipeline"])
    console.print(t1)

    # ── Agent Status ──────────────────────────────────────────────
    t2 = Table(title="🤖 Agent Status", box=box.ROUNDED)
    t2.add_column("Agent",    style="cyan")
    t2.add_column("Role",     style="white")
    t2.add_column("Status",   style="green")
    t2.add_column("Output",   style="yellow")
    t2.add_column("Handoff",  style="magenta")
    t2.add_row(
        "Researcher",
        agent["researcher"]["role"],
        "✅ " + agent["researcher"]["status"],
        agent["researcher"]["output"],
        f"→ {agent['researcher']['handoff_to']}",
    )
    t2.add_row(
        "Writer",
        agent["writer"]["role"],
        "✅ " + agent["writer"]["status"],
        agent["writer"]["output"],
        f"{agent['writer']['sections_produced']} sections",
    )
    console.print(t2)

    # ── State Machine ─────────────────────────────────────────────
    t3 = Table(title="🔄 State Machine Transitions", box=box.ROUNDED)
    t3.add_column("#",     style="dim", width=4)
    t3.add_column("State", style="bold yellow")
    t3.add_column("Time",  style="dim")
    for entry in sm["agent_trace"]:
        ts = entry["timestamp"][:19].replace("T", " ") if entry["timestamp"] else ""
        t3.add_row(str(entry["step"]), entry["state"], ts)
    t3.add_row("→", f"[green]{sm['final_state']}[/green]", "")
    console.print(t3)

    # ── Rating ────────────────────────────────────────────────────
    t4 = Table(title="⭐ AutoGenius Rating", box=box.ROUNDED)
    t4.add_column("Category",    style="cyan")
    t4.add_column("Score",       style="white", justify="center")
    t4.add_column("Bar",         style="yellow")

    def bar(score):
        filled = int(score)
        return "█" * filled + "░" * (10 - filled)

    t4.add_row("⚡ Performance", f"{rate['performance']}/10", bar(rate['performance']))
    t4.add_row("🔋 Efficiency",  f"{rate['efficiency']}/10",  bar(rate['efficiency']))
    t4.add_row("🛡️ Technology",  f"{rate['technology']}/10",  bar(rate['technology']))
    t4.add_row("🛡️ Safety",      f"{rate['safety']}/10",      bar(rate['safety']))
    t4.add_row("💰 Value",        f"{rate['value']}/10",       bar(rate['value']))
    t4.add_row("[bold]🏆 Overall[/bold]",
               f"[bold green]{rate['overall']}/10[/bold green]",
               f"[bold green]{bar(rate['overall'])}[/bold green]")
    console.print(t4)

    # ── Report Sections ───────────────────────────────────────────
    t5 = Table(title="📄 Report Sections", box=box.ROUNDED)
    t5.add_column("#",       style="dim", width=4)
    t5.add_column("Section", style="white")
    for i, sec in enumerate(rep["sections"], 1):
        t5.add_row(str(i), sec)
    console.print(t5)

    # ── Report Preview ────────────────────────────────────────────
    console.print(Panel(
        rep["preview"],
        title="📝 Report Preview (first 300 chars)",
        border_style="dim"
    ))

    # ── Final summary ─────────────────────────────────────────────
    console.print(Panel.fit(
        f"[bold green]✅ STEP 6 Complete — Structured Output Ready[/bold green]\n\n"
        f"[white]JSON saved → [cyan]outputs/structured_output_{meta['run_id']}.json[/cyan]\n"
        f"Next: [yellow]python vision/multimodal_pipeline.py[/yellow]  (STEP 8)[/white]",
        border_style="green"
    ))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AutoGenius Output Formatter — STEP 6")
    parser.add_argument("--run-id", default=None,
                        help="Specific run ID to format (default: latest)")
    parser.add_argument("--save", action="store_true", default=True,
                        help="Save structured JSON to outputs/")
    args = parser.parse_args()

    console.print("\n[bold cyan]Loading pipeline outputs...[/bold cyan]")

    # Load source files
    state  = load_latest_state(args.run_id)
    run_id = state["crew_run_id"]
    report = load_report(run_id)
    logs   = load_logs(run_id)

    console.print(f"  ✅ State loaded  — run_id: [cyan]{run_id}[/cyan]")
    console.print(f"  ✅ Report loaded — {len(report.split())} words")
    console.print(f"  ✅ Logs loaded   — {len(logs)} state transitions\n")

    # Build structured output
    structured = build_structured_output(state, report, logs)

    # Save to disk
    out_path = OUTPUTS_DIR / f"structured_output_{run_id}.json"
    out_path.write_text(json.dumps(structured, indent=2, ensure_ascii=False), encoding="utf-8")
    console.print(f"  💾 Saved → [cyan]{out_path.name}[/cyan]\n")

    # Display
    display_structured_output(structured)

    return structured


if __name__ == "__main__":
    main()