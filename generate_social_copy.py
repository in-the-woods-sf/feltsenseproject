#!/usr/bin/env python3
"""
Feltsense VC Social Copy Generator

Reads a CSV of VC partners, scrapes their public social profiles,
and generates personalized campaign copy using Claude.

Usage:
    python generate_social_copy.py --csv vcs_sample.csv
    python generate_social_copy.py --csv vcs.csv --brief campaign_brief.md --output ./output
    python generate_social_copy.py --help
"""

import csv
import os
import sys
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

from scraper import fetch_all_signals, ProfileData
from generator import CopyGenerator, GeneratedCopy

load_dotenv(override=True)

app = typer.Typer(
    help="Generate personalized VC social copy for campaigns.",
    add_completion=False,
)
console = Console()


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class VCProfile:
    name: str
    firm: str
    linkedin_url: str = ""
    x_url: str = ""
    email: str = ""


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> list[VCProfile]:
    """Load VCs from CSV. Supports flexible column names."""
    profiles = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalise key names (strip whitespace, lowercase)
            row = {k.strip().lower(): v.strip() for k, v in row.items()}

            name = row.get("name", "")
            firm = row.get("firm", row.get("company", row.get("fund", "")))
            linkedin = row.get("linkedin_url", row.get("linkedin", ""))
            x_url = row.get("x_url", row.get("twitter_url", row.get("twitter", row.get("x", ""))))
            email = row.get("email", "")

            if not name:
                continue

            profiles.append(VCProfile(
                name=name,
                firm=firm,
                linkedin_url=linkedin,
                x_url=x_url,
                email=email,
            ))
    return profiles


def load_brief(path: Optional[Path]) -> str:
    """Load campaign brief from file or use the default."""
    if path and path.exists():
        return path.read_text(encoding="utf-8")

    # Fall back to campaign_brief.md in script directory
    default = Path(__file__).parent / "campaign_brief.md"
    if default.exists():
        return default.read_text(encoding="utf-8")

    # Hardcoded fallback
    return """\
Campaign: YC Replication Sculpture — March 24th launch.
We replicated 20 startups from the YC W26 batch using agentic AI founders.
Three claims: (1) The future of founding is agentic. (2) The YC model is evolving.
(3) True defensibility is rare — replicating 20 companies reveals which ones have it.
Central question: If an AI agent can replicate your startup in days, was it ever a real moat?
Our handle: @feltsense
"""


def slugify(name: str) -> str:
    """Convert a name to a safe filename slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render_markdown(copy: GeneratedCopy, twitter: Optional[ProfileData], linkedin: Optional[ProfileData]) -> str:
    """Render a VC's copy as a single Markdown file."""
    # Build scrape status note
    scrape_lines = []
    if twitter:
        icon = "✓" if twitter.scrape_status == "ok" else ("~" if twitter.scrape_status == "partial" else "✗")
        scrape_lines.append(f"X/Twitter [{icon}]: {twitter.notes or twitter.scrape_status} ({len(twitter.posts)} posts)")
    if linkedin:
        icon = "✓" if linkedin.scrape_status == "ok" else ("~" if linkedin.scrape_status == "partial" else "✗")
        scrape_lines.append(f"LinkedIn [{icon}]: {linkedin.notes or linkedin.scrape_status} ({len(linkedin.posts)} posts)")

    scrape_status_block = "\n".join(f"> {line}" for line in scrape_lines) if scrape_lines else "> No scraping attempted"

    flag = "\n\n> ⚠️ **Insufficient data:** No posts were scraped. Copy uses general VC conventions — review carefully." if copy.insufficient_data else ""

    return f"""## {copy.name} — {copy.firm}
{flag}

### 📣 Post (X + LinkedIn)

{copy.standalone_post}

---

### 💬 Comment to drop on our post

{copy.comment}

---

### 🔁 Our reply to their comment — pick one (internal use)

**A — Casual** *(warm thanks / acknowledgment)*
{copy.our_reply_casual}

**B — Insight** *(unintuitive push that deepens the thread)*
{copy.our_reply_insight}

**C — Tease** *(hint at more coming / stay tuned)*
{copy.our_reply_tease}

---

**Voice notes:** {copy.voice_notes}

**Scrape status:**
{scrape_status_block}
"""


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

@app.command()
def main(
    csv_file: Path = typer.Option(
        ...,
        "--csv", "-c",
        help="Path to CSV file with VC profiles (required columns: name, firm, x_url, linkedin_url).",
        exists=True,
    ),
    brief_file: Optional[Path] = typer.Option(
        None,
        "--brief", "-b",
        help="Path to campaign brief text/markdown file. Defaults to ./campaign_brief.md.",
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output", "-o",
        help="Directory to write per-person markdown files.",
    ),
    model: str = typer.Option(
        "claude-opus-4-6",
        "--model", "-m",
        help="Claude model to use for copy generation.",
    ),
    skip_scraping: bool = typer.Option(
        False,
        "--skip-scraping",
        help="Skip social scraping and generate copy from name/firm only.",
    ),
    twitter_bearer: Optional[str] = typer.Option(
        None,
        "--twitter-bearer",
        envvar="TWITTER_BEARER_TOKEN",
        help="Twitter API v2 bearer token for higher-quality scraping.",
        show_default=False,
    ),
    anthropic_key: Optional[str] = typer.Option(
        None,
        "--anthropic-key",
        envvar="ANTHROPIC_API_KEY",
        help="Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.",
        show_default=False,
    ),
    single: Optional[str] = typer.Option(
        None,
        "--single",
        help="Process only one VC by name (useful for testing).",
    ),
) -> None:
    """
    Generate personalized social copy for each VC in the CSV.

    Produces one markdown file per person in the output directory,
    plus a combined index file.

    Example:
        python generate_social_copy.py --csv vcs.csv --brief campaign_brief.md
    """
    # --- Load inputs ---
    console.print(Panel.fit("[bold]Feltsense VC Social Copy Generator[/bold]", border_style="cyan"))

    vcs = load_csv(csv_file)
    if not vcs:
        console.print("[red]No VC profiles found in CSV.[/red]")
        raise typer.Exit(1)

    campaign_brief = load_brief(brief_file)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter to single VC if requested
    if single:
        vcs = [v for v in vcs if single.lower() in v.name.lower()]
        if not vcs:
            console.print(f"[red]No VC found matching '{single}'[/red]")
            raise typer.Exit(1)

    console.print(f"[dim]Loaded {len(vcs)} VC(s) from {csv_file}[/dim]")
    console.print(f"[dim]Output directory: {output_dir}[/dim]")
    console.print(f"[dim]Model: {model}[/dim]\n")

    # Validate API key
    api_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]ANTHROPIC_API_KEY not set. Use --anthropic-key or set the env var.[/red]")
        raise typer.Exit(1)

    generator = CopyGenerator(api_key=api_key, model=model)

    # --- Process each VC ---
    results: list[tuple[VCProfile, GeneratedCopy, dict]] = []
    failed: list[tuple[VCProfile, str]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing VCs...", total=len(vcs))

        for vc in vcs:
            progress.update(task, description=f"[cyan]{vc.name}[/cyan] ({vc.firm})")

            try:
                # Step 1: Scrape
                scraped: dict[str, ProfileData] = {}
                if not skip_scraping:
                    progress.update(task, description=f"[cyan]{vc.name}[/cyan] — scraping...")
                    scraped = fetch_all_signals(
                        name=vc.name,
                        x_url=vc.x_url,
                        linkedin_url=vc.linkedin_url,
                        twitter_bearer_token=twitter_bearer,
                    )

                    # Log scrape results
                    for platform, data in scraped.items():
                        icon = "✓" if data.scrape_status == "ok" else ("~" if data.scrape_status == "partial" else "✗")
                        console.print(
                            f"  [dim]{icon} {platform}: {len(data.posts)} posts[/dim]",
                            highlight=False,
                        )

                # Step 2: Generate copy
                progress.update(task, description=f"[cyan]{vc.name}[/cyan] — generating copy...")
                copy = generator.generate(
                    name=vc.name,
                    firm=vc.firm,
                    campaign_brief=campaign_brief,
                    twitter=scraped.get("twitter"),
                    linkedin=scraped.get("linkedin"),
                )

                # Step 3: Write markdown file
                md_content = render_markdown(copy, scraped.get("twitter"), scraped.get("linkedin"))
                out_path = output_dir / f"{slugify(vc.name)}.md"
                out_path.write_text(md_content, encoding="utf-8")

                results.append((vc, copy, scraped))
                console.print(f"  [green]✓[/green] {vc.name} → {out_path.name}")

            except Exception as e:
                msg = str(e)
                failed.append((vc, msg))
                console.print(f"  [red]✗[/red] {vc.name}: {msg}")

            progress.advance(task)

    # --- Write combined index ---
    _write_index(output_dir, results, campaign_brief)

    # --- Summary table ---
    console.print()
    table = Table(title="Results", show_header=True, header_style="bold cyan")
    table.add_column("VC", style="bold")
    table.add_column("Firm")
    table.add_column("X posts")
    table.add_column("LinkedIn posts")
    table.add_column("Status")

    for vc, copy, scraped in results:
        tw = scraped.get("twitter")
        li = scraped.get("linkedin")
        flag = "⚠️ low data" if copy.insufficient_data else "✓"
        table.add_row(
            vc.name,
            vc.firm,
            str(len(tw.posts)) if tw else "—",
            str(len(li.posts)) if li else "—",
            flag,
        )
    for vc, err in failed:
        table.add_row(vc.name, vc.firm, "—", "—", f"[red]FAILED: {err[:40]}[/red]")

    console.print(table)
    console.print(f"\n[bold green]Done.[/bold green] Files written to [cyan]{output_dir}[/cyan]")

    if failed:
        console.print(f"[yellow]{len(failed)} VC(s) failed — check errors above.[/yellow]")
        raise typer.Exit(2)


def _write_index(output_dir: Path, results: list, campaign_brief: str) -> None:
    """Write a combined index markdown file."""
    lines = [
        "# Feltsense Social Copy — Campaign Index\n",
        f"Campaign brief summary: {campaign_brief[:200].strip()}...\n\n",
        "---\n\n",
    ]
    for vc, copy, scraped in results:
        slug = slugify(vc.name)
        flag = " ⚠️" if copy.insufficient_data else ""
        lines.append(f"- [{vc.name} — {vc.firm}](./{slug}.md){flag}\n")

    index_path = output_dir / "index.md"
    index_path.write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
