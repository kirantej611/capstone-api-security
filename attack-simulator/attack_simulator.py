#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║       ATTACK SIMULATOR — API Shield Demo Traffic Generator       ║
╠══════════════════════════════════════════════════════════════════╣
║  Generates three types of traffic against the API Gateway:       ║
║    🟢  Normal    — Legitimate e-commerce browsing                ║
║    🔴  Attack    — SQL Injection, XSS, Path Traversal, CmdInj   ║
║    🟡  Anomalous — Credential stuffing, enumeration, scraping    ║
║                                                                  ║
║  All traffic flows through the API Gateway (port 8080),          ║
║  which intercepts, analyses via ML, and blocks threats.          ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
    python attack_simulator.py                     # Default: mixed traffic, 120s
    python attack_simulator.py --mode mixed        # Mixed traffic (all types)
    python attack_simulator.py --mode normal       # Normal traffic only
    python attack_simulator.py --mode attack        # Attack traffic only
    python attack_simulator.py --mode anomalous    # Anomalous traffic only
    python attack_simulator.py --mode demo          # Demo sequence (scripted)
    python attack_simulator.py --duration 60        # Run for 60 seconds
    python attack_simulator.py --duration 0         # Run forever
    python attack_simulator.py --url http://host:8080  # Custom gateway URL
"""

import asyncio
import random
import signal
import sys
import time
from datetime import datetime

import click
import httpx
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config import (
    GATEWAY_URL,
    NORMAL_TRAFFIC_DELAY,
    ATTACK_TRAFFIC_DELAY,
    ANOMALOUS_TRAFFIC_DELAY,
    NORMAL_TRAFFIC_PCT,
    ATTACK_TRAFFIC_PCT,
    ANOMALOUS_TRAFFIC_PCT,
    DEMO_DURATION,
)
from traffic.normal import NormalTrafficGenerator
from traffic.attacks import AttackTrafficGenerator
from traffic.anomalous import AnomalousTrafficGenerator

console = Console()

# ── Counters ──
stats = {
    "total": 0,
    "normal_sent": 0,
    "attack_sent": 0,
    "anomalous_sent": 0,
    "blocked": 0,
    "allowed": 0,
    "errors": 0,
    "start_time": 0.0,
}


def _traffic_type_label(ttype: str) -> Text:
    """Return a coloured label for the traffic type."""
    if ttype == "normal":
        return Text("🟢 NORMAL", style="bold green")
    elif ttype == "attack":
        return Text("🔴 ATTACK", style="bold red")
    elif ttype == "anomalous":
        return Text("🟡 ANOMALOUS", style="bold yellow")
    return Text(ttype)


def _status_label(status_code: int) -> Text:
    """Return a coloured label for the HTTP status."""
    if status_code == 0:
        return Text("ERR", style="bold red")
    elif status_code == 403:
        return Text("BLOCKED", style="bold red")
    elif status_code == 429:
        return Text("RATE-LIM", style="bold yellow")
    elif status_code == 502 or status_code == 504:
        return Text("UPSTREAM", style="dim")
    elif 200 <= status_code < 300:
        return Text("ALLOWED", style="bold green")
    elif 400 <= status_code < 500:
        return Text(f"{status_code}", style="yellow")
    else:
        return Text(f"{status_code}", style="dim")


def _build_stats_panel() -> Panel:
    """Build the live stats panel for the terminal."""
    elapsed = time.time() - stats["start_time"] if stats["start_time"] else 0
    rps = stats["total"] / elapsed if elapsed > 0 else 0

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan", width=20)
    table.add_column(width=12)
    table.add_column(style="bold cyan", width=20)
    table.add_column(width=12)

    table.add_row(
        "Total Requests", str(stats["total"]),
        "Requests/sec", f"{rps:.1f}",
    )
    table.add_row(
        "🟢 Normal", str(stats["normal_sent"]),
        "🔴 Blocked", str(stats["blocked"]),
    )
    table.add_row(
        "🔴 Attacks", str(stats["attack_sent"]),
        "✅ Allowed", str(stats["allowed"]),
    )
    table.add_row(
        "🟡 Anomalous", str(stats["anomalous_sent"]),
        "⚠️  Errors", str(stats["errors"]),
    )
    table.add_row(
        "Elapsed", f"{elapsed:.0f}s",
        "Block Rate", f"{(stats['blocked'] / max(stats['total'], 1) * 100):.1f}%",
    )

    return Panel(table, title="[bold cyan]API Shield — Attack Simulator[/]", border_style="cyan")


def _log_request(traffic_type: str, result: dict) -> None:
    """Log a single request result to the console."""
    stats["total"] += 1

    if traffic_type == "normal":
        stats["normal_sent"] += 1
    elif traffic_type == "attack":
        stats["attack_sent"] += 1
    elif traffic_type == "anomalous":
        stats["anomalous_sent"] += 1

    status = result.get("status", 0)
    if status == 0:
        stats["errors"] += 1
    elif status in (403, 429):
        stats["blocked"] += 1
    else:
        stats["allowed"] += 1


async def _run_mixed_traffic(
    client: httpx.AsyncClient,
    normal_gen: NormalTrafficGenerator,
    attack_gen: AttackTrafficGenerator,
    anomalous_gen: AnomalousTrafficGenerator,
    duration: int,
) -> None:
    """Run mixed traffic based on configured percentages."""
    start = time.time()

    console.print("\n[bold cyan]Mode:[/] Mixed Traffic")
    console.print(
        f"[bold cyan]Mix:[/]  🟢 {NORMAL_TRAFFIC_PCT}% Normal  "
        f"🔴 {ATTACK_TRAFFIC_PCT}% Attack  "
        f"🟡 {ANOMALOUS_TRAFFIC_PCT}% Anomalous"
    )
    console.print(f"[bold cyan]Duration:[/] {'∞ (Ctrl+C to stop)' if duration == 0 else f'{duration}s'}\n")

    with Live(_build_stats_panel(), refresh_per_second=2, console=console) as live:
        while True:
            if duration > 0 and (time.time() - start) >= duration:
                break

            # Pick traffic type based on percentages
            roll = random.randint(1, 100)
            if roll <= NORMAL_TRAFFIC_PCT:
                result = await normal_gen.generate_one(client)
                _log_request("normal", result)
                delay = NORMAL_TRAFFIC_DELAY
            elif roll <= NORMAL_TRAFFIC_PCT + ATTACK_TRAFFIC_PCT:
                result = await attack_gen.generate_one(client)
                _log_request("attack", result)
                delay = ATTACK_TRAFFIC_DELAY
            else:
                result = await anomalous_gen.generate_one(client)
                _log_request("anomalous", result)
                delay = ANOMALOUS_TRAFFIC_DELAY

            live.update(_build_stats_panel())
            await asyncio.sleep(delay)


async def _run_single_type(
    client: httpx.AsyncClient,
    generator,
    traffic_type: str,
    delay: float,
    duration: int,
) -> None:
    """Run a single type of traffic."""
    start = time.time()
    label = traffic_type.capitalize()

    console.print(f"\n[bold cyan]Mode:[/] {label} Traffic Only")
    console.print(f"[bold cyan]Delay:[/] {delay}s between requests")
    console.print(f"[bold cyan]Duration:[/] {'∞ (Ctrl+C to stop)' if duration == 0 else f'{duration}s'}\n")

    with Live(_build_stats_panel(), refresh_per_second=2, console=console) as live:
        while True:
            if duration > 0 and (time.time() - start) >= duration:
                break

            result = await generator.generate_one(client)
            _log_request(traffic_type, result)
            live.update(_build_stats_panel())
            await asyncio.sleep(delay)


async def _run_demo_sequence(
    client: httpx.AsyncClient,
    normal_gen: NormalTrafficGenerator,
    attack_gen: AttackTrafficGenerator,
    anomalous_gen: AnomalousTrafficGenerator,
) -> None:
    """
    Scripted demo sequence for business presentations.

    Phase 1 (20s): Normal traffic only — dashboard shows all green
    Phase 2 (30s): Mixed attack traffic — dashboard lights up red
    Phase 3 (20s): Credential stuffing burst — rapid anomaly detection
    Phase 4 (20s): Mixed traffic — showing real-time blocking
    Phase 5 (10s): Cool-down, normal traffic — back to green
    """
    phases = [
        ("Phase 1: Normal Browsing", "normal", 20, 0.8),
        ("Phase 2: Attacks Begin", "attack", 30, 0.3),
        ("Phase 3: Credential Stuffing", "anomalous", 20, 0.03),
        ("Phase 4: Mixed Assault", "mixed", 20, 0.3),
        ("Phase 5: Calm Restored", "normal", 10, 1.0),
    ]

    console.print("\n[bold magenta]═══ DEMO SEQUENCE ═══[/]")
    console.print("[dim]Scripted 5-phase demo for business presentations[/]\n")

    with Live(_build_stats_panel(), refresh_per_second=2, console=console) as live:
        for phase_name, phase_type, phase_duration, phase_delay in phases:
            console.print(f"\n[bold yellow]▶ {phase_name}[/] ({phase_duration}s)")
            phase_start = time.time()

            while (time.time() - phase_start) < phase_duration:
                if phase_type == "normal":
                    result = await normal_gen.generate_one(client)
                    _log_request("normal", result)
                elif phase_type == "attack":
                    result = await attack_gen.generate_one(client)
                    _log_request("attack", result)
                elif phase_type == "anomalous":
                    result = await anomalous_gen.generate_one(client)
                    _log_request("anomalous", result)
                elif phase_type == "mixed":
                    roll = random.randint(1, 100)
                    if roll <= 40:
                        result = await normal_gen.generate_one(client)
                        _log_request("normal", result)
                    elif roll <= 75:
                        result = await attack_gen.generate_one(client)
                        _log_request("attack", result)
                    else:
                        result = await anomalous_gen.generate_one(client)
                        _log_request("anomalous", result)

                live.update(_build_stats_panel())
                await asyncio.sleep(phase_delay)

    console.print("\n[bold green]✓ Demo sequence complete![/]")


async def _main(mode: str, duration: int, url: str) -> None:
    """Main async entry point."""
    stats["start_time"] = time.time()

    console.print(Panel.fit(
        "[bold cyan]API Shield — Attack Simulator[/]\n"
        f"[dim]Target: {url}[/]",
        border_style="cyan",
    ))

    # Verify gateway is reachable
    async with httpx.AsyncClient(timeout=5.0) as check_client:
        try:
            resp = await check_client.get(f"{url}/gateway/health")
            if resp.status_code == 200:
                health = resp.json()
                console.print(f"[green]✓ Gateway is healthy[/]  "
                              f"Redis: {'✓' if health.get('redis_connected') else '✗'}  "
                              f"Kafka: {'✓' if health.get('kafka_connected') else '✗'}  "
                              f"ML: {'✓' if health.get('ml_engine_connected') else '✗'}")
            else:
                console.print(f"[yellow]⚠ Gateway responded with {resp.status_code}[/]")
        except Exception as exc:
            console.print(f"[red]✗ Cannot reach gateway at {url}: {exc}[/]")
            console.print("[dim]Make sure the gateway is running (docker-compose up)[/]")
            return

    # Initialize generators
    normal_gen = NormalTrafficGenerator(url)
    attack_gen = AttackTrafficGenerator(url)
    anomalous_gen = AnomalousTrafficGenerator(url)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            if mode == "mixed":
                await _run_mixed_traffic(client, normal_gen, attack_gen, anomalous_gen, duration)
            elif mode == "normal":
                await _run_single_type(client, normal_gen, "normal", NORMAL_TRAFFIC_DELAY, duration)
            elif mode == "attack":
                await _run_single_type(client, attack_gen, "attack", ATTACK_TRAFFIC_DELAY, duration)
            elif mode == "anomalous":
                await _run_single_type(client, anomalous_gen, "anomalous", ANOMALOUS_TRAFFIC_DELAY, duration)
            elif mode == "demo":
                await _run_demo_sequence(client, normal_gen, attack_gen, anomalous_gen)
        except asyncio.CancelledError:
            pass

    # Final stats
    elapsed = time.time() - stats["start_time"]
    console.print("\n")
    console.print(_build_stats_panel())
    console.print(f"\n[bold cyan]Completed in {elapsed:.1f}s[/]")


@click.command()
@click.option(
    "--mode", "-m",
    type=click.Choice(["mixed", "normal", "attack", "anomalous", "demo"], case_sensitive=False),
    default="mixed",
    help="Traffic generation mode.",
)
@click.option(
    "--duration", "-d",
    type=int,
    default=None,
    help="Duration in seconds (0 = run forever). Defaults to config value.",
)
@click.option(
    "--url", "-u",
    type=str,
    default=None,
    help="Gateway URL. Defaults to config value.",
)
def cli(mode: str, duration: int, url: str) -> None:
    """API Shield Attack Simulator — Generate demo traffic."""
    target_url = url or GATEWAY_URL
    run_duration = duration if duration is not None else DEMO_DURATION

    # Handle Ctrl+C gracefully
    def _signal_handler(sig, frame):
        console.print("\n[yellow]Stopping simulator...[/]")
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)

    asyncio.run(_main(mode, run_duration, target_url))


if __name__ == "__main__":
    cli()
