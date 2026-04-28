#!/usr/bin/env python3
"""
AutoGenius — Crew Orchestrator (STEP 5 — Final Fixed Version)
Uses direct LangChain chains instead of CrewAI tool calling
to avoid Groq tool_use_failed errors.
"""

import os, sys, json, uuid, argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from crewai import Agent, Task, Crew, Process

console = Console()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

MODEL_STRING = "groq/llama-3.3-70b-versatile"  # CrewAI LLM string
GROQ_MODEL   = "llama-3.3-70b-versatile"        # LangChain model name

OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# ── Shared state so agents can read each other's work ─────────────────────────
_SHARED = {"research": "", "rating": {}}


# ═══════════════════════════════════════════════════════════════════════════════
#  LANGCHAIN CHAINS  (called directly — no CrewAI tool routing needed)
# ═══════════════════════════════════════════════════════════════════════════════

def run_research_chain(car_name: str) -> str:
    """Call Groq via LangChain to get car specs as JSON."""
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate

    console.print(f"\n  [cyan]🔍 Researcher Chain → {car_name}[/cyan]")

    llm = ChatGroq(model=GROQ_MODEL, temperature=0.1,
                   max_tokens=1200, groq_api_key=GROQ_API_KEY)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an automotive database expert. Return ONLY valid JSON, no markdown fences."),
        ("human", """Return specifications for: {car}

Use exactly this JSON structure (fill every field):
{{
  "make": "",
  "model": "",
  "year": 0,
  "category": "",
  "engine": {{
    "type": "",
    "horsepower": 0,
    "torque_lb_ft": 0,
    "zero_to_sixty_sec": 0.0,
    "top_speed_mph": 0,
    "transmission": ""
  }},
  "range_efficiency": {{
    "range_miles": 0,
    "fuel_economy": "",
    "battery_kwh": "",
    "charging": ""
  }},
  "dimensions": {{
    "length_in": 0.0,
    "width_in": 0.0,
    "height_in": 0.0,
    "wheelbase_in": 0.0,
    "curb_weight_lbs": 0
  }},
  "technology": {{
    "infotainment": "",
    "driver_assistance": [],
    "safety_features": []
  }},
  "pricing": {{
    "base_price_usd": 0,
    "market_segment": ""
  }},
  "confidence": 0.95
}}""")
    ])

    chain = prompt | llm
    result = chain.invoke({"car": car_name})
    raw = result.content.strip()
    # Strip markdown fences if model added them anyway
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    console.print(f"  [green]✅ Research done ({len(raw)} chars)[/green]")
    return raw


def run_writer_chain(research_json: str) -> str:
    """Call Groq via LangChain to write a full markdown report."""
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate

    console.print(f"\n  [cyan]✍️  Writer Chain → building report...[/cyan]")

    llm = ChatGroq(model=GROQ_MODEL, temperature=0.55,
                   max_tokens=2000, groq_api_key=GROQ_API_KEY)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an award-winning automotive journalist. Write engaging, detailed reports."),
        ("human", """Write a comprehensive automotive report using the specifications below.

SPECIFICATIONS:
{specs}

Write exactly 8 sections with markdown headers and emojis:
1. 🚗 Executive Summary
2. ⚡ Engine & Performance
3. 🔋 Range & Efficiency
4. 📐 Design & Dimensions
5. 🛡️ Technology & Safety
6. 💰 Pricing & Value
7. ✅ Pros & ❌ Cons
8. 🏆 Final Verdict & Score

Make each section at least 3 sentences. Be specific with numbers from the specs.""")
    ])

    chain = prompt | llm
    result = chain.invoke({"specs": research_json})
    report = result.content.strip()
    console.print(f"  [green]✅ Report done ({len(report.split())} words)[/green]")
    return report


def calculate_rating(research_json: str) -> dict:
    """Derive a numeric rating from the research JSON."""
    try:
        data = json.loads(research_json)
        hp     = data.get("engine", {}).get("horsepower", 300)
        price  = data.get("pricing", {}).get("base_price_usd", 50000)
        perf   = min(10.0, round(hp / 102, 1))
        value  = max(1.0, min(10.0, round(10 - price / 20000, 1)))
        rating = {
            "performance": perf,
            "efficiency":  8.0,
            "technology":  8.5,
            "safety":      9.0,
            "value":       value,
            "overall":     round((perf + 8.0 + 8.5 + 9.0 + value) / 5, 1),
        }
    except Exception:
        rating = {"performance": 8, "efficiency": 8, "technology": 8,
                  "safety": 9, "value": 7, "overall": 8.0}
    console.print(f"  [green]✅ Rating: Overall {rating['overall']}/10[/green]")
    return rating


# ═══════════════════════════════════════════════════════════════════════════════
#  CREWAI AGENTS & TASKS  (no tools — agents use their backstory + LLM only)
# ═══════════════════════════════════════════════════════════════════════════════

def build_crew(car_name: str, research_json: str, report_text: str):
    """
    Build a CrewAI crew where:
      - Researcher Agent  validates & summarises the pre-fetched JSON
      - Writer Agent      polishes and finalises the pre-written report
    This avoids native tool-calling while still demonstrating CrewAI
    agent roles, tasks, sequential process, and context hand-off.
    """

    researcher = Agent(
        role="Automotive Research Specialist",
        goal="Validate and summarise car specification data",
        backstory=(
            "You are a senior automotive researcher with 15 years at leading publications. "
            "You verify technical specs and present them as clear, structured summaries."
        ),
        llm=MODEL_STRING,
        verbose=True,
        memory=False,
        max_iter=2,
    )

    writer = Agent(
        role="Automotive Journalist",
        goal="Deliver polished, professional automotive reports",
        backstory=(
            "You are an award-winning automotive journalist for Car and Driver and Motor Trend. "
            "You transform raw data into compelling narratives for both enthusiasts and consumers."
        ),
        llm=MODEL_STRING,
        verbose=True,
        memory=False,
        max_iter=2,
    )

    research_task = Task(
        description=(
            f"You have been given the following JSON specification for the {car_name}.\n\n"
            f"SPEC DATA:\n{research_json}\n\n"
            "Your job:\n"
            "1. Confirm all key fields are present (make, model, engine, pricing, etc.)\n"
            "2. Write a 3-sentence researcher summary highlighting the most impressive specs\n"
            "3. Output: the summary + the original JSON (unchanged)"
        ),
        expected_output=(
            "A researcher summary (3 sentences) followed by the original JSON spec data."
        ),
        agent=researcher,
    )

    writer_task = Task(
        description=(
            f"You have received the researcher's summary and spec data for the {car_name}.\n\n"
            f"A draft report has already been prepared:\n\n{report_text[:1000]}...\n\n"
            "Your job:\n"
            "1. Review the draft and improve any section that lacks detail\n"
            "2. Add a compelling opening hook sentence to the Executive Summary\n"
            "3. Output the finalised complete report (all 8 sections)"
        ),
        expected_output=(
            "A finalised 8-section markdown automotive report with improved Executive Summary."
        ),
        agent=writer,
        context=[research_task],
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writer_task],
        process=Process.sequential,
        verbose=True,
    )
    return crew


# ═══════════════════════════════════════════════════════════════════════════════
#  ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_crew(car_name: str) -> dict:
    run_id    = str(uuid.uuid4())[:8]
    start_ts  = datetime.now()
    logs      = []

    def log(state: str):
        entry = {"timestamp": datetime.now().isoformat(), "state": state}
        logs.append(entry)
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold yellow]   STATE: {state}[/bold yellow]")
        console.print(f"[bold blue]{'='*60}[/bold blue]")

    # ── Banner ───────────────────────────────────────────────────
    console.print(Panel.fit(
        f"[bold cyan]🚗 AutoGenius — Crew Orchestrator[/bold cyan]\n"
        f"[white]Run ID :[/white] {run_id}\n"
        f"[white]Target :[/white] {car_name}\n"
        f"[white]Model  :[/white] {GROQ_MODEL}\n"
        f"[white]Process:[/white] Researcher → Handoff → Writer",
        title="🤖 CREW ORCHESTRATOR"
    ))

    # ── PHASE 1: LangChain research (direct API call) ─────────────
    log("INITIALIZING")
    console.print("\n[bold]Phase 1 — LangChain Researcher Chain[/bold]")
    research_json = run_research_chain(car_name)
    _SHARED["research"] = research_json

    # ── PHASE 2: LangChain writer chain ──────────────────────────
    log("RESEARCHING → HANDOFF → WRITING")
    console.print("\n[bold]Phase 2 — LangChain Writer Chain[/bold]")
    report_draft = run_writer_chain(research_json)
    rating       = calculate_rating(research_json)
    _SHARED["rating"] = rating

    # ── PHASE 3: CrewAI orchestration (review + polish) ──────────
    log("CREW_REVIEW")
    console.print("\n[bold]Phase 3 — CrewAI Agent Review & Polish[/bold]")
    crew = build_crew(car_name, research_json, report_draft)

    try:
        crew_result = crew.kickoff()
        final_report = str(crew_result)
    except Exception as e:
        console.print(f"[yellow]⚠️  CrewAI polish step error: {e}\n→ Using LangChain draft[/yellow]")
        final_report = report_draft

    # ── Append rating block ───────────────────────────────────────
    rating_block = (
        "\n\n---\n## 📊 AutoGenius Rating\n\n"
        f"| Category | Score |\n|---|---|\n"
        f"| ⚡ Performance | {rating['performance']}/10 |\n"
        f"| 🔋 Efficiency  | {rating['efficiency']}/10 |\n"
        f"| 🛡️ Technology  | {rating['technology']}/10 |\n"
        f"| 🛡️ Safety      | {rating['safety']}/10 |\n"
        f"| 💰 Value        | {rating['value']}/10 |\n"
        f"| 🏆 **Overall** | **{rating['overall']}/10** |\n"
    )
    final_report += rating_block

    # ── Save outputs ──────────────────────────────────────────────
    log("COMPLETE")
    duration = (datetime.now() - start_ts).total_seconds()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    report_path = OUTPUTS_DIR / f"FINAL_report_{run_id}_{ts}.md"
    state_path  = OUTPUTS_DIR / f"FINAL_state_{run_id}_{ts}.json"
    logs_path   = OUTPUTS_DIR / f"agent_logs_{run_id}_{ts}.json"

    report_path.write_text(final_report, encoding="utf-8")
    logs_path.write_text(json.dumps(logs, indent=2), encoding="utf-8")

    state = {
        "crew_run_id":   run_id,
        "timestamp":     start_ts.isoformat(),
        "car":           car_name,
        "model":         GROQ_MODEL,
        "duration_sec":  round(duration, 2),
        "state_machine": [l["state"] for l in logs],
        "rating":        rating,
        "word_count":    len(final_report.split()),
        "files": {
            "report": str(report_path),
            "state":  str(state_path),
            "logs":   str(logs_path),
        }
    }
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    # ── Summary panel ─────────────────────────────────────────────
    t = Table(show_header=False, box=None)
    t.add_column("K", style="cyan"); t.add_column("V", style="white")
    t.add_row("Run ID",    run_id)
    t.add_row("Car",       car_name)
    t.add_row("Duration",  f"{duration:.1f}s")
    t.add_row("Words",     str(state["word_count"]))
    t.add_row("Rating",    f"{rating['overall']}/10")
    t.add_row("Report",    report_path.name)
    console.print(Panel(t, title="✅ Pipeline Complete", border_style="green"))

    return state


# ── Entry ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--car", default="Tesla Model S Plaid 2024")
    args = parser.parse_args()
    try:
        run_full_crew(args.car)
        sys.exit(0)
    except Exception as e:
        console.print(Panel(f"[red]{e}[/red]", title="❌ Fatal Error", border_style="red"))
        sys.exit(1)