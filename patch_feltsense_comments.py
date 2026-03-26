"""
Batch-generate the 'Feltsense Comment' (our_comment) for all existing March .md files.
Patches each file in-place — does not touch any other field.

Skips files that already have a non-empty Feltsense Comment section.
"""

import csv
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

import anthropic
from scraper import fetch_all_signals

BASE_DIR  = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH   = BASE_DIR / "vcs_normalized.csv"

_SYSTEM = """\
You are writing a short engagement comment for Feltsense (@feltsense).
Rules:
- 1-2 sentences only
- Written FROM Feltsense's perspective, commenting on the VC's own recent content
- Sounds like a genuine peer observation — not promotional, not begging for engagement
- Reference something specific from their recent posts if possible
- Ends the exchange feeling like two people who see the world similarly
- Active voice only; no em dashes; no "delve"; no AI tells
- No generic praise or hype words
"""


def load_vcs() -> list[dict]:
    col_map = {
        "name": ["name"],
        "firm": ["firm", "company", "fund"],
        "x_url": ["x_url", "twitter_url", "twitter", "x"],
        "linkedin_url": ["linkedin_url", "linkedin"],
    }
    def resolve(row, key):
        for alias in col_map[key]:
            val = row.get(alias, "").strip()
            if val:
                return val
        return ""
    vcs = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = resolve(row, "name")
            if not name:
                continue
            vcs.append({
                "name": name,
                "firm": resolve(row, "firm") or "Independent",
                "x_url": resolve(row, "x_url"),
                "linkedin_url": resolve(row, "linkedin_url"),
                "slug": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
            })
    return vcs


def already_has_comment(raw: str) -> bool:
    """Return True if the file already has a non-empty Feltsense Comment section."""
    m = re.search(
        r"### 💬 Feltsense Comment\s*\n[^\n]*\n\n(.+?)(?=\n\n---|\Z)",
        raw, re.DOTALL
    )
    return bool(m and m.group(1).strip())


def patch_file(md_path: Path, our_comment: str):
    """Add or replace the Feltsense Comment section in the .md file."""
    raw = md_path.read_text(encoding="utf-8")
    section_text = (
        f"### 💬 Feltsense Comment\n"
        f"*(What Feltsense / Marik drops on this person's own post)*\n\n"
        f"{our_comment}"
    )

    # Replace existing empty/placeholder section
    replaced = re.sub(
        r"### 💬 Feltsense Comment\s*\n[^\n]*\n\n.*?(?=\n\n---)",
        section_text,
        raw,
        count=1,
        flags=re.DOTALL,
    )
    if replaced != raw:
        md_path.write_text(replaced, encoding="utf-8")
        return

    # No existing section — insert before the replies block
    insert_before = "### 🔁 Our reply"
    if insert_before in raw:
        patched = raw.replace(
            insert_before,
            section_text + "\n\n---\n\n" + insert_before,
            1,
        )
    else:
        patched = raw.rstrip() + "\n\n---\n\n" + section_text + "\n"
    md_path.write_text(patched, encoding="utf-8")


def generate_comment(client: anthropic.Anthropic, name: str, firm: str,
                     recent_posts: str, voice_notes: str) -> str:
    prompt = (
        f"VC: {name}, {firm}\n\n"
        f"Their recent X posts:\n{recent_posts or '(no posts scraped)'}\n\n"
        f"Voice notes: {voice_notes or '(none)'}\n\n"
        f"Write a 1-2 sentence comment for Feltsense to drop on {name}'s own recent posts. "
        f"Reference something specific. Make it feel like a genuine peer observation between "
        f"two people who track the same signals."
    )
    resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=200,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def main():
    client = anthropic.Anthropic()
    vcs    = load_vcs()
    done   = 0
    skipped = 0

    for vc in vcs:
        md_path = OUTPUT_DIR / f"{vc['slug']}.md"
        if not md_path.exists():
            print(f"  — skip {vc['name']:28s} no March file")
            continue

        raw = md_path.read_text(encoding="utf-8")
        if already_has_comment(raw):
            print(f"  ✓ skip {vc['name']:28s} already has comment")
            skipped += 1
            continue

        # Extract voice notes from existing file
        vn_m = re.search(r"\*\*Voice notes:\*\*\s*(.+?)(?:\n|$)", raw)
        voice_notes = vn_m.group(1).strip() if vn_m else ""

        # Scrape recent X posts for fresh context
        recent_posts = ""
        if vc.get("x_url"):
            try:
                scraped = fetch_all_signals(
                    name=vc["name"],
                    x_url=vc["x_url"],
                    linkedin_url="",
                )
                tw = scraped.get("twitter")
                if tw and tw.posts:
                    recent_posts = "\n".join(tw.posts[:12])
            except Exception as e:
                print(f"    scrape warn for {vc['name']}: {e}")

        print(f"  → generating for {vc['name']} ({vc['firm']})…", end="", flush=True)
        try:
            comment = generate_comment(client, vc["name"], vc["firm"], recent_posts, voice_notes)
            patch_file(md_path, comment)
            print(f" ✓")
            print(f"     {comment[:100]}{'…' if len(comment) > 100 else ''}")
            done += 1
        except Exception as e:
            print(f" ERROR: {e}")

    print(f"\nDone. {done} generated, {skipped} already had comments.")


if __name__ == "__main__":
    main()
