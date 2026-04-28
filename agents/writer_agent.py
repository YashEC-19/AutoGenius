# ============================================================
# AutoGenius — Writer Agent
# File: agents/writer_agent.py
# STEP 4: CrewAI Writer Agent that synthesizes research
#         into a professional formatted automotive report
# ============================================================

import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Agent, Task, Crew
from crewai.tools import tool
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from dotenv import load_dotenv

from langchain_tools import build_writer_chain

load_dotenv()
console = Console()

GROQ_MODEL = "groq/llama-3.3-70b-versatile"

# ============================================================
# SECTION 1: CrewAI-compatible Writer Tools
# ============================================================

@tool("Format Automotive Report")
def format_report_tool(car_name: str, research_data: str) -> str:
    """
    Transform raw car research data into a professional markdown report.
    Input: car_name (string) and research_data (JSON string of car specs).
    Output: Full formatted markdown report with all sections.
    """
    console.print(f"\n[bold magenta]✍️  Writer Tool:[/bold magenta] Formatting report for '{car_name}'")
    chain = build_writer_chain()
    result = chain.invoke({
        "car_name": car_name,
        "research_json": research_data
    })
    console.print(f"[green]✅ Report formatted — {len(result)} characters[/green]")
    return result


@tool("Calculate Car Rating")
def calculate_rating_tool(specs_json: str) -> str:
    """
    Calculate an overall rating for a car based on its specifications.
    Input: JSON string of car specs.
    Output: Rating breakdown as a formatted string.
    """
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_groq import ChatGroq

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an automotive rating expert. 
        Rate a car out of 10 across these categories:
        - Performance (0-10)
        - Efficiency (0-10)  
        - Technology (0-10)
        - Safety (0-10)
        - Value for Money (0-10)
        - Overall (average of above)
        
        Return ONLY a JSON object with these exact keys:
        performance, efficiency, technology, safety, value, overall, summary
        """),
        ("human", "Rate this car based on specs:\n{specs}\n\nReturn only JSON.")
    ])

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY")
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"specs": specs_json})
    console.print(f"[green]✅ Rating calculated[/green]")
    return result


# ============================================================
# SECTION 2: Agent + Task
# ============================================================

def create_writer_agent() -> Agent:
    """
    Creates the Writer Agent with CrewAI 1.x API.
    Role: Automotive Journalist & Technical Writer
    Tools: format_report_tool, calculate_rating_tool
    LLM: Groq Llama 3.3 70B (higher temp for creative writing)
    """
    agent = Agent(
        role="Automotive Journalist and Technical Writer",
        goal=(
            "Transform raw automotive research data into compelling, accurate, "
            "and beautifully structured reports that inform and engage car enthusiasts."
        ),
        backstory=(
            "You are an award-winning automotive journalist with bylines in Top Gear, "
            "Car and Driver, and Motor Trend. You have 15 years of experience writing "
            "car reviews that balance technical precision with engaging storytelling. "
            "You understand what buyers need to know and how to present complex specs "
            "in a way that is both accurate and accessible. Every report you write "
            "feels like it belongs in a premium automotive publication."
        ),
        tools=[format_report_tool, calculate_rating_tool],
        llm=GROQ_MODEL,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    console.print(Panel.fit(
        "[bold magenta]✍️  Writer Agent Created[/bold magenta]\n"
        f"Role: {agent.role}\n"
        f"Tools: format_report_tool, calculate_rating_tool\n"
        f"LLM: {GROQ_MODEL}",
        border_style="magenta"
    ))
    return agent


def create_writer_task(agent: Agent, car_name: str, research_data: str) -> Task:
    """Creates the writing task with research data embedded."""
    return Task(
        description=f"""
        Write a comprehensive professional automotive report for: {car_name}

        RESEARCH DATA FROM RESEARCHER AGENT:
        {research_data}

        YOUR TASKS:
        STEP 1: Use the Format Automotive Report tool with the car name and research data
        STEP 2: Use the Calculate Car Rating tool to generate ratings
        STEP 3: Combine both into a final complete report

        THE REPORT MUST CONTAIN THESE 8 SECTIONS:
        1. 🚗 Title & Executive Summary
        2. 📊 At-a-Glance Specs Table
        3. ⚡ Performance Analysis
        4. 🔋 Efficiency & Range
        5. 🛡️ Safety & Technology
        6. 💰 Value Proposition & Pricing
        7. ✅ Pros & Cons
        8. 🏁 Final Verdict & Rating (out of 10)

        Write like a premium automotive journalist. Be specific with numbers.
        Make it engaging, accurate, and publication-ready.
        """,
        expected_output=(
            f"A complete, publication-ready markdown report for {car_name} "
            "with all 8 required sections, accurate specs, rating breakdown, "
            "pros/cons list, and a clear final verdict with score out of 10."
        ),
        agent=agent,
    )


# ============================================================
# SECTION 3: Run Writer Agent
# ============================================================

def run_writer(car_name: str, research_data: str) -> dict:
    """
    Runs the Writer Agent to produce a formatted report.

    Args:
        car_name: The car being reported on
        research_data: JSON string from Researcher Agent

    Returns:
        dict with report, metadata, and state info
    """
    run_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().isoformat()

    console.print("\n")
    console.print(Panel(
        f"[bold white]✍️  AutoGenius — Writer Agent[/bold white]\n\n"
        f"[magenta]Run ID:[/magenta]    {run_id}\n"
        f"[magenta]Target:[/magenta]    {car_name}\n"
        f"[magenta]Input:[/magenta]     {len(research_data)} chars of research data\n"
        f"[magenta]Started:[/magenta]   {timestamp}\n"
        f"[magenta]Status:[/magenta]    [yellow]INITIALIZING...[/yellow]",
        title="[bold magenta]WRITER AGENT[/bold magenta]",
        border_style="magenta",
        expand=False
    ))

    state = {
        "run_id": run_id,
        "timestamp": timestamp,
        "car_name": car_name,
        "agent": "Writer",
        "status": "IDLE",
        "report_markdown": None,
        "report_complete": False,
        "error": None,
        "duration_seconds": None,
        "word_count": 0,
    }

    start_time = datetime.now()

    try:
        # ── STATE: WRITING ────────────────────────────────────
        state["status"] = "WRITING"
        console.print(f"\n[bold yellow]✍️  STATE: {state['status']}[/bold yellow]")

        agent = create_writer_agent()
        task  = create_writer_task(agent, car_name, research_data)
        crew  = Crew(agents=[agent], tasks=[task], verbose=True)

        console.print(f"\n[bold yellow]🚀 Launching Writer for: {car_name}[/bold yellow]\n")
        result = crew.kickoff()

        # ── STATE: FORMATTING ─────────────────────────────────
        state["status"] = "FORMATTING"
        console.print(f"\n[bold yellow]📝 STATE: {state['status']}[/bold yellow]")

        report_markdown       = str(result)
        state["report_markdown"]  = report_markdown
        state["word_count"]       = len(report_markdown.split())
        state["status"]           = "COMPLETE"
        state["report_complete"]  = True
        state["duration_seconds"] = round((datetime.now() - start_time).total_seconds(), 2)

        console.print(f"\n[bold green]✅ STATE: {state['status']}[/bold green]")

        _display_writer_summary(state, report_markdown)
        _save_writer_output(state, report_markdown)

        return state

    except Exception as e:
        state["status"] = "ERROR"
        state["error"]  = str(e)
        state["duration_seconds"] = round((datetime.now() - start_time).total_seconds(), 2)
        console.print(Panel(
            f"[bold red]❌ Writer Agent Error[/bold red]\n\n{str(e)}",
            border_style="red"
        ))
        raise


# ============================================================
# SECTION 4: Display & Save Helpers
# ============================================================

def _display_writer_summary(state: dict, report_markdown: str):
    """Displays rich summary and markdown report preview."""
    console.print("\n")

    table = Table(
        title="✍️  Writer Agent — Execution Summary",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("Field",  style="bold white", width=20)
    table.add_column("Value",  style="green")

    table.add_row("Run ID",         state["run_id"])
    table.add_row("Car",            state["car_name"])
    table.add_row("Status",         f"[bold green]{state['status']}[/bold green]")
    table.add_row("Duration",       f"{state['duration_seconds']}s")
    table.add_row("Word Count",     str(state["word_count"]))
    table.add_row("Report Complete","✅ Yes" if state["report_complete"] else "❌ No")
    table.add_row("Format",         "Markdown")
    console.print(table)

    # Show rendered markdown preview (first 1500 chars)
    preview = report_markdown[:1500] + "\n\n*...report continues...*" if len(report_markdown) > 1500 else report_markdown
    console.print(Panel(
        Markdown(preview),
        title="[bold magenta]📰 Report Preview[/bold magenta]",
        border_style="magenta"
    ))


def _save_writer_output(state: dict, report_markdown: str):
    """Saves the report as both .md and .json files."""
    output_dir = Path("../outputs")
    output_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save markdown report
    md_path = output_dir / f"report_{state['run_id']}_{ts}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# AutoGenius Report — {state['car_name']}\n")
        f.write(f"*Generated: {state['timestamp']}*\n\n")
        f.write(report_markdown)
    console.print(f"\n[green]📄 Markdown report saved:[/green] {md_path}")

    # Save JSON state
    json_path = output_dir / f"writer_{state['run_id']}_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {k: v for k, v in state.items() if k != "report_markdown"},
            "report_markdown": report_markdown,
        }, f, indent=2)
    console.print(f"[green]💾 JSON state saved:[/green]    {json_path}")


# ============================================================
# SECTION 5: Entry Point
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AutoGenius Writer Agent")
    parser.add_argument("--car",      type=str, default="Tesla Model S Plaid 2024")
    parser.add_argument("--research", type=str, default=None,
                        help="Path to researcher JSON output file")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold magenta]✍️  AutoGenius — Writer Agent[/bold magenta]\n"
        "STEP 4: CrewAI Writer with Groq + LangChain",
        border_style="magenta"
    ))

    # Load research data
    if args.research and Path(args.research).exists():
        with open(args.research) as f:
            data = json.load(f)
            research_data = data.get("raw_research_output", str(data))
        console.print(f"[green]📂 Loaded research from:[/green] {args.research}")
    else:
        # Use sample research data for standalone testing
        console.print("[yellow]⚠️  No research file provided — using sample Tesla data[/yellow]")
        research_data = json.dumps({
            "Basic Info": {"Make": "Tesla", "Model": "Model S Plaid", "Year": 2024, "Category": "Full-size Luxury Sedan"},
            "Engine & Performance": {"Engine Type": "3-phase, 4-pole electric motor", "Horsepower": 1020, "Torque": 1050, "0-60 mph": 2.0, "Top Speed": 163},
            "Range & Efficiency": {"Range": 396, "Fuel Economy": "N/A (electric)", "Battery Type": "100 kWh lithium-ion"},
            "Dimensions & Weight": {"Length": 203.7, "Width": 77.3, "Height": 56.9, "Curb Weight": 4940},
            "Technology Features": ["17-inch touchscreen", "22-speaker audio", "Autopilot", "OTA updates"],
            "Safety Features": ["8 airbags", "Blind-spot monitoring", "Forward collision warning", "Lane departure warning"],
            "Pricing": {"Base Price": 129990, "Target Market": "Luxury EV segment"},
            "confidence_score": 0.95
        }, indent=2)

    # Run the Writer Agent
    result_state = run_writer(args.car, research_data)

    if result_state["status"] == "COMPLETE":
        console.print(Panel.fit(
            f"[bold green]✅ Report Complete![/bold green]\n\n"
            f"Car:        {result_state['car_name']}\n"
            f"Words:      {result_state['word_count']}\n"
            f"Duration:   {result_state['duration_seconds']}s\n\n"
            f"[yellow]Next:[/yellow] python crew_orchestrator.py --car \"{args.car}\"",
            border_style="green"
        ))