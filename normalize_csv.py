#!/usr/bin/env python3
"""
Normalizer for the Notion-exported VC CSV format.

Expands multi-person rows into one row per person, extracts names from
the Private Notes field, and matches LinkedIn/Twitter URLs by position.

Usage:
    python3 normalize_csv.py \
        --input "/path/to/VC List and Social Accounts.csv" \
        --output vcs_normalized.csv
"""

import re
import csv
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

app = typer.Typer(add_completion=False)
console = Console()


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def split_urls(raw: str) -> list[str]:
    """Split a space/newline-separated list of URLs."""
    if not raw:
        return []
    return [u.strip() for u in re.split(r'\s+', raw.strip()) if u.strip().startswith("http")]


def parse_people_from_notes(notes: str) -> list[dict]:
    """
    Extract people from a Private Notes string like:
      "Jeff Bocan mailto:bocan@..., Marc Averitt mailto:averitt@..."
      "David Wieland (Motivate VC) mailto:david@motivate.vc"
      "mailto:ethan@outsideventurecapital.com"
    Returns list of {"name": str, "email": str}.
    """
    if not notes:
        return []

    people = []

    # Split on ", " only when followed by an uppercase letter or "mailto:"
    # This avoids splitting on commas inside parentheses or email addresses
    segments = re.split(r',\s*(?=[A-Z]|mailto:)', notes.strip())

    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue

        # Extract email
        email_match = re.search(r'mailto:(\S+)', seg)
        email = email_match.group(1).rstrip(",;") if email_match else ""

        # Name = everything before "mailto:", stripped of trailing parens/firm names
        name = re.sub(r'\s*mailto:\S+', '', seg).strip()
        name = re.sub(r'\s*\(.*?\)\s*$', '', name).strip()  # Remove "(Firm Name)"
        name = name.rstrip(",").strip()

        # Skip rows that are just a bare email or empty
        if not name and not email:
            continue

        people.append({"name": name, "email": email})

    return people


def name_from_linkedin_slug(url: str) -> str:
    """Best-effort name from a LinkedIn URL slug, e.g. arian-ghashghai-73ba4681 → Arian Ghashghai."""
    m = re.search(r"linkedin\.com/in/([^/?#]+)", url)
    if not m:
        return ""
    slug = m.group(1)
    # Strip trailing numeric ID segment (e.g. -73ba4681)
    slug = re.sub(r"-[0-9a-f]{6,}$", "", slug)
    return " ".join(part.capitalize() for part in slug.split("-") if part)


def normalize_row(row: dict) -> list[dict]:
    """
    Expand one CSV row into one dict per person.
    Returns a list of normalized dicts ready for the generator CSV.
    """
    firm = row.get("Firm", "").strip()
    notes = row.get("Private Notes", "").strip()
    linkedin_raw = row.get("LinkedIn Accounts", "").strip()
    twitter_raw = row.get("Twitter Account (s)", "").strip()

    linkedin_urls = split_urls(linkedin_raw)
    twitter_urls = split_urls(twitter_raw)

    people = parse_people_from_notes(notes)

    # If no people parsed (bare mailto: entries), derive name from LinkedIn slug
    if not people:
        email_match = re.search(r'mailto:(\S+)', notes)
        email = email_match.group(1).rstrip(",;") if email_match else ""
        name = name_from_linkedin_slug(linkedin_urls[0]) if linkedin_urls else ""
        if not name:
            name = firm  # last resort
        if not name:
            return []
        people = [{"name": name, "email": email}]

    results = []
    for i, person in enumerate(people):
        name = person["name"]
        email = person["email"]

        # Generic email prefixes that are not real people — skip
        _GENERIC_PREFIXES = {"updates", "info", "hello", "contact", "team", "news", "support"}
        if not name and email:
            prefix = email.split("@")[0].lower().split(".")[0]
            if prefix in _GENERIC_PREFIXES:
                continue

        # If name is missing, derive from LinkedIn slug or email username
        if not name:
            slug_name = name_from_linkedin_slug(linkedin_urls[i]) if i < len(linkedin_urls) else ""
            # Prefer email username over a slug that looks like a job title/pseudonym
            email_name = email.split("@")[0].replace(".", " ").title() if email else ""
            slug_looks_generic = any(
                w in slug_name.lower()
                for w in ("investor", "founder", "partner", "ventures", "capital", "fund")
            )
            name = email_name if slug_looks_generic else (slug_name or email_name)

        if not name:
            continue

        # Skip duplicates — same LinkedIn URL or same name+firm already in results
        linkedin_candidate = linkedin_urls[i] if i < len(linkedin_urls) else (linkedin_urls[0] if linkedin_urls else "")
        already_seen_linkedin = linkedin_candidate and any(
            r["linkedin_url"] == linkedin_candidate for r in results
        )
        already_seen_name = (name.lower(), firm.lower()) in {(r["name"].lower(), r["firm"].lower()) for r in results}
        if already_seen_linkedin or already_seen_name:
            continue

        # Match LinkedIn URL by position; fall back to first URL
        linkedin = linkedin_urls[i] if i < len(linkedin_urls) else (linkedin_urls[0] if linkedin_urls else "")

        # Match Twitter URL by position; fall back to first URL (often a firm account)
        twitter = twitter_urls[i] if i < len(twitter_urls) else (twitter_urls[0] if twitter_urls else "")

        results.append({
            "name": name,
            "firm": firm,
            "linkedin_url": linkedin,
            "x_url": twitter,
            "email": email,
        })

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

@app.command()
def main(
    input_file: Path = typer.Option(
        ..., "--input", "-i", help="Path to the raw Notion-exported CSV.", exists=True
    ),
    output_file: Path = typer.Option(
        Path("vcs_normalized.csv"), "--output", "-o", help="Where to write the normalized CSV."
    ),
) -> None:
    """Normalize the VC CSV into one-row-per-person format."""

    rows = []
    with open(input_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    all_people: list[dict] = []
    skipped = 0

    for row in rows:
        expanded = normalize_row(row)
        if expanded:
            all_people.extend(expanded)
        else:
            skipped += 1

    # Write output
    fieldnames = ["name", "firm", "linkedin_url", "x_url", "email"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_people)

    # Preview table
    table = Table(title=f"Normalized — {len(all_people)} people", show_header=True, header_style="bold cyan")
    table.add_column("Name")
    table.add_column("Firm")
    table.add_column("LinkedIn")
    table.add_column("X/Twitter")
    table.add_column("Email")

    for p in all_people:
        table.add_row(
            p["name"],
            p["firm"],
            "✓" if p["linkedin_url"] else "—",
            "✓" if p["x_url"] else "—",
            p["email"][:30] + "…" if len(p["email"]) > 30 else p["email"],
        )

    console.print(table)
    console.print(f"\n[bold green]Written to {output_file}[/bold green] ({skipped} rows skipped)")


if __name__ == "__main__":
    app()
