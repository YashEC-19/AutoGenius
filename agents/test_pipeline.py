#!/usr/bin/env python3
"""
AutoGenius — STEP 7: End-to-End Pipeline Test
Tests the full agent pipeline with 2 different cars.
"""

import os, sys, subprocess, json, time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()
AGENTS_DIR = Path(__file__).parent

TESTS = [
    {"car": "BMW M3 2024",           "expect_hp": 400},
    {"car": "Ford Mustang GT500 2024","expect_hp": 700},
]

def run_test(car: str, expect_hp: int) -> dict:
    console.print(f"\n[bold cyan]🧪 Testing:[/bold cyan] {car}")
    start = time.time()

    result = subprocess.run(
        [sys.executable, str(AGENTS_DIR / "crew_orchestrator.py"), "--car", car],
        capture_output=True, text=True, timeout=120
    )
    duration = round(time.time() - start, 1)

    passed   = result.returncode == 0
    has_state = "STATE: COMPLETE" in result.stdout
    has_report= "FINAL_report" in result.stdout or "Pipeline Complete" in result.stdout

    return {
        "car":      car,
        "passed":   passed and has_state,
        "duration": duration,
        "returncode": result.returncode,
        "has_complete_state": has_state,
        "has_report": has_report,
    }

def main():
    console.print(Panel.fit(
        "[bold cyan]🚗 AutoGenius — STEP 7: End-to-End Test[/bold cyan]\n"
        "[white]Running full pipeline for 2 cars to verify everything works[/white]",
        border_style="cyan"
    ))

    results = []
    for t in TESTS:
        r = run_test(t["car"], t["expect_hp"])
        results.append(r)
        status = "[green]✅ PASS[/green]" if r["passed"] else "[red]❌ FAIL[/red]"
        console.print(f"  {status} — {r['car']} ({r['duration']}s)")

    # Summary table
    tbl = Table(title="🧪 Test Results", box=box.ROUNDED)
    tbl.add_column("Car",      style="cyan")
    tbl.add_column("Result",   justify="center")
    tbl.add_column("Duration", justify="right")
    tbl.add_column("State",    justify="center")
    tbl.add_column("Report",   justify="center")

    all_pass = True
    for r in results:
        ok = r["passed"]
        if not ok: all_pass = False
        tbl.add_row(
            r["car"],
            "✅ PASS" if ok else "❌ FAIL",
            f"{r['duration']}s",
            "✅" if r["has_complete_state"] else "❌",
            "✅" if r["has_report"] else "❌",
        )
    console.print(tbl)

    if all_pass:
        console.print(Panel.fit(
            "[bold green]✅ STEP 7 COMPLETE — All tests passed!\n[/bold green]"
            "[white]Project 1 (Multi-Agent Pipeline) is fully working.\n"
            "Next → STEP 8: Multimodal Vision Lab[/white]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            "[bold yellow]⚠️  Some tests failed — check output above[/bold yellow]",
            border_style="yellow"
        ))

    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())