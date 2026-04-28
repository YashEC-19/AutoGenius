# ============================================================
# AutoGenius — LangChain Tools + Prompt Templates
# File: agents/langchain_tools.py
# STEP 2: All prompt templates and LangChain tools used
#         by Researcher and Writer agents
# ============================================================

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnableSequence
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

load_dotenv()
console = Console()


# ============================================================
# SECTION 1: Pydantic Schemas (Structured Output Formats)
# ============================================================

class CarSpecs(BaseModel):
    """Schema for raw car specifications from Researcher Agent."""
    make: str = Field(description="Car manufacturer e.g. Tesla, BMW")
    model: str = Field(description="Car model name e.g. Model S, M3")
    year: int = Field(description="Manufacturing year")
    category: str = Field(description="Category: Sedan, SUV, Coupe, Truck etc.")

    # Engine & Performance
    engine_type: str = Field(description="Engine type: Electric, V6, V8, Hybrid etc.")
    horsepower: str = Field(description="Horsepower output e.g. 1020 hp")
    torque: str = Field(description="Torque output e.g. 1050 lb-ft")
    transmission: str = Field(description="Transmission type")
    drivetrain: str = Field(description="AWD, RWD, FWD etc.")
    zero_to_sixty: str = Field(description="0-60 mph time e.g. 1.99 seconds")
    top_speed: str = Field(description="Top speed e.g. 200 mph")

    # Range & Efficiency
    range_miles: Optional[str] = Field(description="EV range or fuel range in miles")
    fuel_economy: Optional[str] = Field(description="MPG or MPGe rating")
    battery_capacity: Optional[str] = Field(description="Battery kWh for EVs")

    # Dimensions & Weight
    curb_weight: str = Field(description="Vehicle weight in lbs")
    seating_capacity: str = Field(description="Number of seats")
    cargo_space: str = Field(description="Cargo space in cubic feet")

    # Technology & Safety
    safety_rating: str = Field(description="NHTSA or IIHS safety rating")
    key_features: list[str] = Field(description="Top 5 key features")
    infotainment: str = Field(description="Infotainment system details")
    driver_assistance: list[str] = Field(description="Driver assistance features")

    # Pricing
    base_price: str = Field(description="Base price in USD")
    target_market: str = Field(description="Target customer segment")

    # Research metadata
    confidence_score: float = Field(description="Researcher confidence 0.0-1.0")
    data_notes: str = Field(description="Any caveats about the data")


class WriterReport(BaseModel):
    """Schema for the final formatted report from Writer Agent."""
    title: str = Field(description="Report title")
    executive_summary: str = Field(description="2-3 sentence summary")
    full_report_markdown: str = Field(description="Complete markdown report")
    verdict: str = Field(description="Final verdict on the car")
    rating: float = Field(description="Overall rating out of 10")
    word_count: int = Field(description="Approximate word count")


# ============================================================
# SECTION 2: LLM Initialization
# ============================================================

def get_researcher_llm() -> ChatGroq:
    """
    Returns a Groq LLM configured for the Researcher Agent.
    Low temperature = more factual, consistent outputs.
    """
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        max_tokens=4096,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def get_writer_llm() -> ChatGroq:
    """
    Returns a Groq LLM configured for the Writer Agent.
    Higher temperature = more expressive, engaging writing.
    """
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.6,
        max_tokens=8192,
        api_key=os.getenv("GROQ_API_KEY"),
    )


# ============================================================
# SECTION 3: Prompt Templates
# ============================================================

# ── Researcher Agent Prompt ───────────────────────────────────
RESEARCHER_SYSTEM_PROMPT = """You are an elite automotive research specialist with 20 years of 
experience analyzing vehicles. You work for AutoGenius, a premium automotive intelligence platform.

Your job is to research and extract PRECISE, ACCURATE specifications for any vehicle requested.

STRICT RULES:
- Only provide factual, verifiable specifications
- If you are unsure about a spec, clearly note it with "(estimated)" or "(varies by trim)"
- Always provide a confidence score between 0.0 and 1.0 for your research
- Include pricing in USD
- Be specific with numbers — no vague answers
- Research ALL sections: performance, efficiency, dimensions, technology, safety, pricing

OUTPUT FORMAT: You must return a valid JSON object matching the CarSpecs schema exactly.
Do not include any text before or after the JSON object."""

RESEARCHER_HUMAN_PROMPT = """Research the following vehicle comprehensively:

Vehicle: {car_name}

Provide complete specifications including:
1. Basic info (make, model, year, category)
2. Engine & Performance (horsepower, torque, 0-60, top speed)
3. Range & Efficiency (range, fuel economy, battery if EV)
4. Dimensions & Weight
5. Technology & Safety features
6. Pricing & Target market

Return ONLY a JSON object with all fields from the CarSpecs schema."""

researcher_prompt = ChatPromptTemplate.from_messages([
    ("system", RESEARCHER_SYSTEM_PROMPT),
    ("human", RESEARCHER_HUMAN_PROMPT),
])


# ── Writer Agent Prompt ───────────────────────────────────────
WRITER_SYSTEM_PROMPT = """You are a world-class automotive journalist and technical writer for 
AutoGenius Magazine. You write compelling, accurate, and beautifully structured car reports.

Your writing style:
- Professional yet engaging and accessible
- Data-driven with vivid context (don't just list specs — explain what they MEAN)
- Balanced: highlight strengths AND weaknesses honestly
- Use automotive industry terminology correctly
- Structure reports with clear sections using Markdown

YOUR REPORT MUST INCLUDE THESE SECTIONS:
1. 🚗 Title & Executive Summary
2. 📊 At-a-Glance Specs Table
3. ⚡ Performance Analysis
4. 🔋 Efficiency & Range (if applicable)
5. 🛡️ Safety & Technology
6. 💰 Value Proposition & Pricing
7. ✅ Pros & Cons
8. 🏁 Final Verdict & Rating (out of 10)

Make the report feel like it belongs in a premium automotive publication."""

WRITER_HUMAN_PROMPT = """Write a comprehensive automotive report based on this research data:

RESEARCH DATA:
{research_json}

ADDITIONAL CONTEXT:
- Original query: {car_name}
- Report style: Professional automotive journalism
- Target audience: Car enthusiasts and buyers

Create a full markdown report with all 8 required sections.
Be specific about the numbers — reference the exact specs from the research data.
End with a clear rating out of 10 and a one-paragraph verdict."""

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", WRITER_SYSTEM_PROMPT),
    ("human", WRITER_HUMAN_PROMPT),
])


# ── Handoff Summary Prompt ────────────────────────────────────
HANDOFF_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["car_name", "specs_summary"],
    template="""
=== AGENT HANDOFF PROTOCOL ===
FROM: Researcher Agent
TO:   Writer Agent
RE:   {car_name}

HANDOFF SUMMARY:
{specs_summary}

STATUS: Research complete. Passing structured data to Writer Agent.
Writer Agent should now synthesize this into a full report.
==============================
"""
)


# ============================================================
# SECTION 4: LangChain Tool Definitions (used by CrewAI)
# ============================================================

@tool
def research_car_specs(car_name: str) -> str:
    """
    Research comprehensive specifications for a given car.
    Input: Car name (e.g. 'Tesla Model S Plaid 2024')
    Output: JSON string with complete car specifications
    """
    console.print(f"\n[bold cyan]🔍 Researcher Tool:[/bold cyan] Looking up specs for '{car_name}'")

    llm = get_researcher_llm()
    chain = researcher_prompt | llm | StrOutputParser()

    result = chain.invoke({"car_name": car_name})
    console.print(f"[green]✅ Research complete for {car_name}[/green]")
    return result


@tool
def format_car_report(car_name: str, research_json: str) -> str:
    """
    Format raw car research data into a professional markdown report.
    Input: car_name and research_json (from research_car_specs tool)
    Output: Full formatted markdown report
    """
    console.print(f"\n[bold magenta]✍️  Writer Tool:[/bold magenta] Formatting report for '{car_name}'")

    llm = get_writer_llm()
    chain = writer_prompt | llm | StrOutputParser()

    result = chain.invoke({
        "car_name": car_name,
        "research_json": research_json
    })
    console.print(f"[green]✅ Report formatted for {car_name}[/green]")
    return result


@tool
def validate_car_name(car_name: str) -> str:
    """
    Validate and normalize a car name input.
    Input: Raw car name string
    Output: Normalized car name with make, model, year
    """
    validation_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an automotive expert. Normalize car names to 'Year Make Model Trim' format."),
        ("human", "Normalize this car name: {car_name}\nReturn ONLY the normalized name, nothing else.")
    ])

    llm = get_researcher_llm()
    chain = validation_prompt | llm | StrOutputParser()
    result = chain.invoke({"car_name": car_name})
    console.print(f"[yellow]📝 Normalized:[/yellow] '{car_name}' → '{result.strip()}'")
    return result.strip()


# ============================================================
# SECTION 5: Chain Builders (reusable LangChain chains)
# ============================================================

def build_research_chain() -> RunnableSequence:
    """Builds and returns the researcher LangChain chain."""
    llm = get_researcher_llm()
    return researcher_prompt | llm | StrOutputParser()


def build_writer_chain() -> RunnableSequence:
    """Builds and returns the writer LangChain chain."""
    llm = get_writer_llm()
    return writer_prompt | llm | StrOutputParser()


# ============================================================
# SECTION 6: Quick Test (run directly to verify)
# ============================================================

if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold cyan]🚗 AutoGenius — LangChain Tools Test[/bold cyan]\n"
        "Testing prompt templates and LangChain chains...",
        border_style="cyan"
    ))

    # Test 1: Validate car name tool
    console.print("\n[bold]Test 1: Car Name Validation[/bold]")
    normalized = validate_car_name.invoke("tesla model s plaid")
    console.print(f"Result: [green]{normalized}[/green]")

    # Test 2: Research chain (quick test)
    console.print("\n[bold]Test 2: Research Chain (quick)[/bold]")
    console.print("[yellow]Running research chain for 'BMW M3 2024'...[/yellow]")
    research_chain = build_research_chain()
    result = research_chain.invoke({"car_name": "BMW M3 2024"})

    # Show first 500 chars
    preview = result[:500] + "..." if len(result) > 500 else result
    syntax = Syntax(preview, "json", theme="monokai", line_numbers=False)
    console.print(syntax)

    console.print(Panel.fit(
        "[bold green]✅ LangChain Tools — All tests passed![/bold green]\n"
        "Next: python agents/researcher_agent.py",
        border_style="green"
    ))