# ============================================================
# AutoGenius — Researcher Agent
# File: agents/researcher_agent.py
# STEP 3: CrewAI 1.x Researcher Agent
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
from langchain_groq import ChatGroq
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

from langchain_tools import build_research_chain, build_writer_chain

load_dotenv()
console = Console()

GROQ_MODEL = "groq/llama-3.3-70b-versatile"

# ============================================================
# SECTION 1: CrewAI-compatible Tools
# ============================================================

@tool("Research Car Specifications")
def research_car_specs_tool(car_name: str) -> str:
    """Research comprehensive specifications for a given car model.
    Input should be the full car name including year, make, and model."""
    console.print(f"\n[bold cyan]🔍 Researching:[/bold cyan] {car_name}")
    chain = build_research_chain()
    result = chain.invoke({"car_name": car_name})
    console.print(f"[green]✅ Research complete[/green]")
    return result


@tool("Validate Car Name")
def validate_car_name_tool(car_name: str) -> str:
    """Validate and normalize a car name to standard format: Year Make Model Trim.
    Input should be any car name string."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an automotive expert. Normalize car names to 'Year Make Model Trim' format."),
        ("human", "Normalize this car name: {car_name}\nReturn ONLY the normalized name, nothing else.")
    ])
    from langchain_groq import ChatGroq
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY")
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"car_name": car_name})
    return result.strip()


# ============================================================
# SECTION 2: Agent + Task
# ============================================================

def create_researcher_agent() -> Agent:
    agent = Agent(
        role="Automotive Research Specialist",
        goal=(
            "Research and extract precise, comprehensive specifications for any vehicle. "
            "Ensure all data is accurate, well-structured, and ready for the Writer Agent."
        ),
        backstory=(
            "You are a senior automotive research analyst with 20 years of experience "
            "studying vehicles across all segments. You have deep knowledge of engine specs, "
            "safety ratings, technology features, and market positioning. "
            "AutoGenius relies on your research as the foundation for all its premium reports."
        ),
        tools=[research_car_specs_tool, validate_car_name_tool],
        llm=GROQ_MODEL,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    console.print(Panel.fit(
        "[bold cyan]🔍 Researcher Agent Created[/bold cyan]\n"
        f"Role: {agent.role}\n"
        f"Tools: research_car_specs_tool, validate_car_name_tool\n"
        f"LLM: {GROQ_MODEL}",
        border_style="cyan"
    ))
    return agent


def create_research_task(agent: Agent, car_name: str) -> Task:
    return Task(
        description=f"""
        Research comprehensive specifications for: {car_name}

        STEP 1: Validate and normalize the car name using the Validate Car Name tool
        STEP 2: Research full specifications using the Research Car Specifications tool
        STEP 3: Return the complete specification data

        The output must include:
        - Basic info (make, model, year, category)
        - Engine & performance metrics (hp, torque, 0-60, top speed)
        - Range & efficiency data
        - Dimensions & weight
        - Technology & safety features
        - Pricing information

        Be thorough and accurate. The Writer Agent depends on your research.
        """,
        expected_output=(
            f"Complete specifications for {car_name} including all performance, "
            "efficiency, safety, technology, and pricing data in structured format."
        ),
        agent=agent,
    )


# ============================================================
# SECTION 3: Run Researcher
# ============================================================

def run_researcher(car_name: str) -> dict:
    run_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().isoformat()

    console.print("\n")
    console.print(Panel(
        f"[bold white]🚗 AutoGenius — Researcher Agent[/bold white]\n\n"
        f"[cyan]Run ID:[/cyan]    {run_id}\n"
        f"[cyan]Target:[/cyan]    {car_name}\n"
        f"[cyan]Started:[/cyan]   {timestamp}\n"
        f"[cyan]Status:[/cyan]    [yellow]INITIALIZING...[/yellow]",
        title="[bold cyan]RESEARCHER AGENT[/bold cyan]",
        border_style="cyan",
        expand=False
    ))

    state = {
        "run_id": run_id,
        "timestamp": timestamp,
        "car_name": car_name,
        "agent": "Researcher",
        "status": "IDLE",
        "raw_output": None,
        "handoff_ready": False,
        "error": None,
        "duration_seconds": None,
    }

    start_time = datetime.now()

    try:
        state["status"] = "RESEARCHING"
        console.print(f"\n[bold yellow]📡 STATE: {state['status']}[/bold yellow]")

        agent  = create_researcher_agent()
        task   = create_research_task(agent, car_name)
        crew   = Crew(agents=[agent], tasks=[task], verbose=True)

        console.print(f"\n[bold yellow]🚀 Launching Researcher for: {car_name}[/bold yellow]\n")
        result = crew.kickoff()

        state["status"]       = "PROCESSING"
        console.print(f"\n[bold yellow]⚙️  STATE: {state['status']}[/bold yellow]")

        raw_output            = str(result)
        state["raw_output"]   = raw_output
        state["status"]       = "HANDOFF_READY"
        state["handoff_ready"] = True
        state["duration_seconds"] = round((datetime.now() - start_time).total_seconds(), 2)

        console.print(f"\n[bold green]✅ STATE: {state['status']}[/bold green]")
        _display_summary(state, raw_output)
        _save_output(state, raw_output)
        return state

    except Exception as e:
        state["status"] = "ERROR"
        state["error"]  = str(e)
        state["duration_seconds"] = round((datetime.now() - start_time).total_seconds(), 2)
        console.print(Panel(
            f"[bold red]❌ Error[/bold red]\n\n{str(e)}",
            border_style="red"
        ))
        raise


# ============================================================
# SECTION 4: Helpers
# ============================================================

def _display_summary(state: dict, raw_output: str):
    table = Table(title="🔍 Researcher Agent — Summary", header_style="bold cyan")
    table.add_column("Field", style="bold white", width=20)
    table.add_column("Value", style="green")
    table.add_row("Run ID",        state["run_id"])
    table.add_row("Car",           state["car_name"])
    table.add_row("Status",        f"[bold green]{state['status']}[/bold green]")
    table.add_row("Duration",      f"{state['duration_seconds']}s")
    table.add_row("Handoff Ready", "✅ Yes")
    table.add_row("Output Length", f"{len(raw_output)} chars")
    table.add_row("Next Agent",    "Writer Agent")
    console.print(table)

    preview = raw_output[:600] + "..." if len(raw_output) > 600 else raw_output
    console.print(Panel(preview, title="[bold cyan]📄 Research Preview[/bold cyan]", border_style="cyan"))


def _save_output(state: dict, raw_output: str):
    output_dir = Path("../outputs")
    output_dir.mkdir(exist_ok=True)
    filename = f"researcher_{state['run_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump({"metadata": state, "raw_research_output": raw_output}, f, indent=2)
    console.print(f"\n[green]💾 Saved:[/green] {filepath}")


# ============================================================
# SECTION 5: Entry Point
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AutoGenius Researcher Agent")
    parser.add_argument("--car", type=str, default="Tesla Model S Plaid 2024")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold cyan]🚗 AutoGenius — Researcher Agent[/bold cyan]\n"
        "STEP 3: CrewAI Researcher with Groq + LangChain",
        border_style="cyan"
    ))

    result_state = run_researcher(args.car)

    if result_state["status"] == "HANDOFF_READY":
        console.print(Panel.fit(
            f"[bold green]✅ Research Complete![/bold green]\n\n"
            f"Car: {result_state['car_name']}\n"
            f"Duration: {result_state['duration_seconds']}s\n\n"
            f"[yellow]Next:[/yellow] python writer_agent.py --car \"{args.car}\"",
            border_style="green"
        ))