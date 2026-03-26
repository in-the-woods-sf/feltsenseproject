"""
Feltsense Social Copy — Interactive Web App

Lets teammates browse generated VC copy, give instructions,
and regenerate any section on the fly.
"""

import csv
import json
import os
import re
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dataclasses import asdict

import httpx
import random
from typing import Optional
from flask import Flask, render_template, request, jsonify, abort
from dotenv import load_dotenv

load_dotenv(override=True)

from generator import CopyGenerator, GeneratedCopy
from scraper import fetch_all_signals

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = BASE_DIR / "vcs_normalized.csv"
BRIEF_PATH = BASE_DIR / "campaign_brief.md"
STATUS_PATH = BASE_DIR / "vc_status.json"

OUTPUT_DIR.mkdir(exist_ok=True)

# Partner status options — label, value, color hint
PARTNER_STATUSES = [
    {"value": "",           "label": "No status"},
    {"value": "active",     "label": "Active Posting Partner"},
    {"value": "periodic",   "label": "Periodic Posting Partner"},
    {"value": "cold",       "label": "Not engaged"},
]

ROLE_TYPES = [
    {"value": "",                    "label": "No role"},
    {"value": "vc",                  "label": "VC"},
    {"value": "feltsense_teammate",  "label": "Feltsense Teammate"},
    {"value": "friend",              "label": "Friend of Feltsense"},
    {"value": "mentor_advisor",      "label": "Mentor / Advisor"},
    {"value": "investor_update",     "label": "Prev. Investor Update List"},
]

POC_OPTIONS = ["", "Marik", "Matt"]

ENGAGEMENT_MONTHS = [
    "", "March 2026", "April 2026", "May 2026", "June 2026",
    "July 2026", "August 2026", "September 2026", "October 2026",
    "November 2026", "December 2026",
]

CAMPAIGNS = [
    {"id": "march", "label": "March YC Demo Day"},
    {"id": "april", "label": "April 10 Founders 10 Weeks"},
    {"id": "may",   "label": "May Founder Launch"},
    {"id": "june",  "label": "June Series A Stunt"},
]

# Rows in the copy table, grouped by platform section
# (section, field_id, label, textarea_rows)
COPY_FIELDS = [
    ("summary",    "post_summary",  "Summary",            2),
    ("x",          "x_post",        "VC X Post",          3),
    ("x",          "reply_casual",  "Feltsense Reply A",  2),
    ("x",          "reply_insight", "Feltsense Reply B",  2),
    ("linkedin",   "linkedin_post", "VC LinkedIn Post",   6),
    ("engagement", "comment",       "Their Comment",      3),
    ("engagement", "our_comment",   "Feltsense Comment",  3),
]

# Hub view: VC-facing only — summary, posts, no replies or internal comments
HUB_COPY_FIELDS = [
    ("summary",    "post_summary",  "Summary",            2),
    ("x",          "x_post",        "VC X Post",          3),
    ("linkedin",   "linkedin_post", "VC LinkedIn Post",   6),
]


def load_statuses() -> dict:
    """Load slug -> {status, engagement_month} map from JSON file.
    Backwards-compatible: migrates old flat {slug: 'status'} format."""
    if STATUS_PATH.exists():
        data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        migrated = {}
        for slug, val in data.items():
            if isinstance(val, str):
                migrated[slug] = {"status": val, "engagement_month": "", "role": ""}
            else:
                migrated[slug] = {
                    "status": val.get("status", ""),
                    "engagement_month": val.get("engagement_month", ""),
                    "role": val.get("role", ""),
                    "approved": val.get("approved", False),
                    "poc": val.get("poc", ""),
                }
        return migrated
    return {}

def save_statuses(statuses: dict):
    STATUS_PATH.write_text(json.dumps(statuses, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_vcs() -> list[dict]:
    col_map = {
        "name": ["name"],
        "firm": ["firm", "company", "fund"],
        "x_url": ["x_url", "twitter_url", "twitter", "x"],
        "linkedin_url": ["linkedin_url", "linkedin"],
        "email": ["email"],
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
                "email": resolve(row, "email"),
                "slug": slugify(name),
            })
    return vcs


def _copy_path(slug: str, campaign: str = "march") -> Path:
    """Return the output path for a given slug + campaign."""
    if campaign == "march":
        return OUTPUT_DIR / f"{slug}.md"
    return OUTPUT_DIR / f"{slug}-{campaign}.md"


def load_copy(slug: str, campaign: str = "march") -> Optional[dict]:
    path = _copy_path(slug, campaign)
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")

    def extract(header):
        # Match markdown bold labels like **X:** or section headers
        pattern = rf"###\s+{re.escape(header)}\s*\n(.*?)(?=###|\Z)"
        m = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        if not m:
            return ""
        # Strip trailing horizontal rules and whitespace
        return re.sub(r'\s*\n---+\s*$', '', m.group(1)).strip()

    # Parse standalone post sub-sections
    post_block = extract("📣 Post (X + LinkedIn)")
    x_match = re.search(r"\*\*X:\*\*\s*\n(.*?)(?=\*\*LinkedIn:|$)", post_block, re.DOTALL)
    li_match = re.search(r"\*\*LinkedIn:\*\*\s*\n(.*?)$", post_block, re.DOTALL)

    def extract_reply(label):
        pattern = rf"\*\*{re.escape(label)}\*\*[^\n]*\n(.*?)(?=\*\*[A-C] —|\Z)"
        m = re.search(pattern, raw, re.DOTALL)
        return m.group(1).strip() if m else ""

    # "Their Comment" — new header first, fall back to old single-comment header
    their_comment = (
        extract("💬 Their Comment")
        or extract("💬 Comment to drop on our post")
        or extract("💬 Comment")
    )

    # Parse scrape counts from metadata lines if present
    x_count_m = re.search(r'> X/Twitter.*?\((\d+) posts\)', raw)
    li_count_m = re.search(r'> LinkedIn.*?\((\d+) posts\)', raw)

    return {
        "post_summary": extract("📋 Sculpture Summary"),
        "x_post": x_match.group(1).strip() if x_match else "",
        "linkedin_post": li_match.group(1).strip() if li_match else "",
        "comment": their_comment,
        "our_comment": extract("💬 Feltsense Comment"),
        "reply_casual": extract_reply("A — Casual"),
        "reply_insight": extract_reply("B — Insight"),
        "reply_tease": extract_reply("C — Tease"),
        "voice_notes": "",
        "insufficient_data": "⚠️" in raw,
        "generated": True,
        "x_scraped": int(x_count_m.group(1)) if x_count_m else None,
        "li_scraped": int(li_count_m.group(1)) if li_count_m else None,
    }


def save_copy(slug: str, copy: GeneratedCopy, campaign: str = "march"):
    """Persist a GeneratedCopy to its markdown file."""
    path = _copy_path(slug, campaign)
    insufficient_flag = "\n\n> ⚠️ **Insufficient data:** No posts were scraped. Copy uses general VC conventions — review carefully." if copy.insufficient_data else ""
    post_summary = getattr(copy, "post_summary", "")
    content = f"""## {copy.name} — {copy.firm}
{insufficient_flag}

### 📋 Sculpture Summary

{post_summary}

---

### 📣 Post (X + LinkedIn)

**X:**
{copy.standalone_post.split('**LinkedIn:**')[0].replace('**X:**', '').strip()}

**LinkedIn:**
{copy.standalone_post.split('**LinkedIn:**')[1].strip() if '**LinkedIn:**' in copy.standalone_post else ''}

---

### 💬 Their Comment
*(Suggested copy for {copy.name} to post on Feltsense's post)*

{copy.comment}

---

### 💬 Feltsense Comment
*(What Feltsense / Marik drops on {copy.name}'s own post)*

{copy.our_comment}

---

### 🔁 Our reply to their comment — pick one (internal use)

**A — Casual** *(warm thanks / acknowledgment)*
{copy.our_reply_casual}

**B — Insight** *(unintuitive push that deepens the thread)*
{copy.our_reply_insight}

---

**Voice notes:** {copy.voice_notes}
"""
    path.write_text(content, encoding="utf-8")


def load_campaign_brief() -> str:
    if BRIEF_PATH.exists():
        return BRIEF_PATH.read_text(encoding="utf-8")
    return ""


# ---------------------------------------------------------------------------
# Mention count (X API v2 — app-only Bearer Token, no VC auth needed)
# ---------------------------------------------------------------------------

_mention_cache: dict = {"count": None, "ts": 0.0}
_MENTION_TTL = 3600  # re-fetch at most once per hour


def _fetch_mention_count() -> Optional[int]:
    """Return @feltsensefund mention count for the last 7 days via X API tweet counts."""
    global _mention_cache
    now = time.time()
    if _mention_cache["count"] is not None and (now - _mention_cache["ts"]) < _MENTION_TTL:
        return _mention_cache["count"]

    bearer = os.environ.get("TWITTER_BEARER_TOKEN", "")
    if not bearer:
        return None

    try:
        resp = httpx.get(
            "https://api.twitter.com/2/tweets/counts/recent",
            headers={"Authorization": f"Bearer {bearer}"},
            params={"query": "@feltsensefund", "granularity": "day"},
            timeout=8,
        )
        if resp.status_code == 200:
            total = resp.json().get("meta", {}).get("total_tweet_count", 0)
            _mention_cache = {"count": total, "ts": now}
            return total
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def load_march_quotes(max_quotes: int = 8) -> list:
    """Pull random X post snippets from generated March copy files for the carousel."""
    quotes = []
    for path in sorted(OUTPUT_DIR.glob("*.md")):
        # Skip campaign-suffixed files (april/may/june) and the index log
        stem = path.stem
        if stem in ("index", "run_log") or stem.endswith(("-april", "-may", "-june")):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except Exception:
            continue
        # Extract VC name
        name_match = re.match(r"## (.+?) —", raw)
        if not name_match:
            continue
        name = name_match.group(1).strip()
        # Extract X post text
        x_match = re.search(r"\*\*X:\*\*\s*\n(.*?)(?=\n\n\*\*LinkedIn:|\Z)", raw, re.DOTALL)
        if x_match:
            text = x_match.group(1).strip()
            if text and len(text) > 30:
                quotes.append({"text": text, "name": name})
    random.shuffle(quotes)
    return quotes[:max_quotes]


@app.route("/")
def index():
    vcs = load_vcs()
    statuses = load_statuses()
    for vc in vcs:
        vc["generated"] = (OUTPUT_DIR / f"{vc['slug']}.md").exists()
        entry = statuses.get(vc["slug"], {})
        vc["status"] = entry.get("status", "") if isinstance(entry, dict) else entry
        vc["engagement_month"] = entry.get("engagement_month", "") if isinstance(entry, dict) else ""
        vc["role"] = entry.get("role", "") if isinstance(entry, dict) else ""
        vc["approved"] = entry.get("approved", False) if isinstance(entry, dict) else False
        vc["poc"] = entry.get("poc", "") if isinstance(entry, dict) else ""
    generated = sum(1 for v in vcs if v["generated"])
    quotes = load_march_quotes()
    return render_template("index.html", vcs=vcs, total=len(vcs), generated=generated,
                           partner_statuses=PARTNER_STATUSES, engagement_months=ENGAGEMENT_MONTHS,
                           role_types=ROLE_TYPES, poc_options=POC_OPTIONS, quotes=quotes)


@app.route("/vc/<slug>")
def vc_profile(slug):
    vcs = load_vcs()
    vc = next((v for v in vcs if v["slug"] == slug), None)
    if not vc:
        abort(404)
    statuses = load_statuses()
    entry = statuses.get(slug, {})
    vc["status"] = entry.get("status", "") if isinstance(entry, dict) else entry
    vc["engagement_month"] = entry.get("engagement_month", "") if isinstance(entry, dict) else ""
    vc["role"] = entry.get("role", "") if isinstance(entry, dict) else ""
    vc["approved"] = entry.get("approved", False) if isinstance(entry, dict) else False
    vc["poc"] = entry.get("poc", "") if isinstance(entry, dict) else ""
    copies = {c["id"]: load_copy(slug, c["id"]) for c in CAMPAIGNS}
    # Grab scrape counts from the first available campaign file
    for c in CAMPAIGNS:
        cp = copies.get(c["id"])
        if cp and (cp.get("x_scraped") is not None or cp.get("li_scraped") is not None):
            vc["x_scraped"] = cp.get("x_scraped")
            vc["li_scraped"] = cp.get("li_scraped")
            break
    return render_template("vc.html", vc=vc, copies=copies, campaigns=CAMPAIGNS,
                           copy_fields=COPY_FIELDS, partner_statuses=PARTNER_STATUSES,
                           engagement_months=ENGAGEMENT_MONTHS, role_types=ROLE_TYPES,
                           hub_mode=False)


@app.route("/hub/<slug>")
def hub_profile(slug):
    vcs = load_vcs()
    vc = next((v for v in vcs if v["slug"] == slug), None)
    if not vc:
        abort(404)
    statuses = load_statuses()
    entry = statuses.get(slug, {})
    vc["status"] = entry.get("status", "") if isinstance(entry, dict) else entry
    vc["engagement_month"] = entry.get("engagement_month", "") if isinstance(entry, dict) else ""
    vc["role"] = entry.get("role", "") if isinstance(entry, dict) else ""
    vc["approved"] = entry.get("approved", False) if isinstance(entry, dict) else False
    vc["poc"] = entry.get("poc", "") if isinstance(entry, dict) else ""
    copies = {c["id"]: load_copy(slug, c["id"]) for c in CAMPAIGNS}
    for c in CAMPAIGNS:
        cp = copies.get(c["id"])
        if cp and (cp.get("x_scraped") is not None or cp.get("li_scraped") is not None):
            vc["x_scraped"] = cp.get("x_scraped")
            vc["li_scraped"] = cp.get("li_scraped")
            break
    return render_template("vc.html", vc=vc, copies=copies, campaigns=CAMPAIGNS,
                           copy_fields=HUB_COPY_FIELDS, partner_statuses=PARTNER_STATUSES,
                           engagement_months=ENGAGEMENT_MONTHS, role_types=ROLE_TYPES,
                           hub_mode=True)


@app.route("/api/set-status/<slug>", methods=["POST"])
def set_status(slug):
    """Set partner status and/or engagement month for a VC."""
    data = request.get_json() or {}
    status = data.get("status")
    engagement_month = data.get("engagement_month")
    role = data.get("role")

    statuses = load_statuses()
    entry = statuses.get(slug, {"status": "", "engagement_month": "", "role": ""})
    if not isinstance(entry, dict):
        entry = {"status": entry, "engagement_month": "", "role": ""}

    if status is not None:
        valid = {s["value"] for s in PARTNER_STATUSES}
        if status not in valid:
            return jsonify({"error": "Invalid status"}), 400
        entry["status"] = status

    if engagement_month is not None:
        entry["engagement_month"] = engagement_month

    if role is not None:
        valid_roles = {r["value"] for r in ROLE_TYPES}
        if role not in valid_roles:
            return jsonify({"error": "Invalid role"}), 400
        entry["role"] = role

    approved = data.get("approved")
    if approved is not None:
        entry["approved"] = bool(approved)

    poc = data.get("poc")
    if poc is not None:
        entry["poc"] = poc

    statuses[slug] = entry
    save_statuses(statuses)
    return jsonify({"ok": True, "slug": slug, "status": entry["status"],
                    "engagement_month": entry["engagement_month"], "role": entry["role"],
                    "approved": entry.get("approved", False), "poc": entry.get("poc", "")})


@app.route("/api/regenerate/<slug>", methods=["POST"])
def regenerate(slug):
    """
    Regenerate copy for a single VC.
    Body: { "section": "x_post"|"linkedin_post"|"comment"|"reply_casual"|"reply_insight"|"all",
            "instruction": "make it shorter and more casual" }
    """
    vcs = load_vcs()
    vc = next((v for v in vcs if v["slug"] == slug), None)
    if not vc:
        return jsonify({"error": "VC not found"}), 404

    data = request.get_json() or {}
    section = data.get("section", "all")
    instruction = data.get("instruction", "").strip()
    campaign = data.get("campaign", "march")
    campaign_label = next((c["label"] for c in CAMPAIGNS if c["id"] == campaign), "March YC Demo Day")

    try:
        gen = CopyGenerator()
        brief = load_campaign_brief()

        # Always re-scrape for freshest data, but use skip flag if no URLs
        scraped = {}
        if vc.get("x_url") or vc.get("linkedin_url"):
            scraped = fetch_all_signals(
                name=vc["name"],
                x_url=vc.get("x_url", ""),
                linkedin_url=vc.get("linkedin_url", ""),
            )

        # Prepend campaign context, then append any extra instruction
        brief_with_instruction = f"## Campaign: {campaign_label}\n\n" + brief
        if instruction:
            brief_with_instruction += f"\n\n## Special instruction for this regeneration\n{instruction}"
            if section != "all":
                brief_with_instruction += f"\nApply this instruction specifically to the {section.replace('_', ' ')} section."

        copy = gen.generate(
            name=vc["name"],
            firm=vc["firm"],
            campaign_brief=brief_with_instruction,
            twitter=scraped.get("twitter"),
            linkedin=scraped.get("linkedin"),
        )

        # Preserve any manually-entered sculpture summary from the existing file
        existing = load_copy(slug, campaign)
        if existing and existing.get("post_summary"):
            copy.post_summary = existing["post_summary"]

        save_copy(slug, copy, campaign)

        # Parse x_post and linkedin_post from standalone_post
        sp = copy.standalone_post
        x_post = sp.split("**LinkedIn:**")[0].replace("**X:**", "").strip()
        linkedin_post = sp.split("**LinkedIn:**")[1].strip() if "**LinkedIn:**" in sp else ""

        return jsonify({
            "ok": True,
            "copy": {
                "post_summary": getattr(copy, "post_summary", ""),
                "x_post": x_post,
                "linkedin_post": linkedin_post,
                "comment": copy.comment,
                "our_comment": copy.our_comment,
                "reply_casual": copy.our_reply_casual,
                "reply_insight": copy.our_reply_insight,
                "reply_tease": copy.our_reply_tease,
                "voice_notes": copy.voice_notes,
                "insufficient_data": copy.insufficient_data,
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/save-edit/<slug>", methods=["POST"])
def save_edit(slug):
    """Save a manual inline edit to the markdown file."""
    data = request.get_json() or {}
    field = data.get("field")
    value = data.get("value", "")
    campaign = data.get("campaign", "march")

    path = _copy_path(slug, campaign)
    if not path.exists():
        return jsonify({"error": "File not found"}), 404

    raw = path.read_text(encoding="utf-8")

    field_patterns = {
        "post_summary":(r"(### 📋 Sculpture Summary\s*\n\n)(.*?)(\n\n---)", re.DOTALL),
        "x_post":      (r"(\*\*X:\*\*\s*\n)(.*?)(\n\n\*\*LinkedIn:)", re.DOTALL),
        "linkedin_post":(r"(\*\*LinkedIn:\*\*\s*\n)(.*?)(\n\n---)", re.DOTALL),
        "comment":     (r"(### 💬 Their Comment\s*\n[^\n]*\n\n)(.*?)(\n\n---)", re.DOTALL),
        "our_comment": (r"(### 💬 Feltsense Comment\s*\n[^\n]*\n\n)(.*?)(\n\n---)", re.DOTALL),
        "reply_casual":(r"(\*\*A — Casual\*\*[^\n]*\n)(.*?)(\n\n\*\*B —)", re.DOTALL),
        "reply_insight":(r"(\*\*B — Insight\*\*[^\n]*\n)(.*?)(\n\n---)", re.DOTALL),
        "reply_tease": (r"(\*\*C — Tease\*\*[^\n]*\n)(.*?)(\n\n---)", re.DOTALL),
    }

    if field not in field_patterns:
        return jsonify({"error": "Unknown field"}), 400

    pattern, flags = field_patterns[field]
    new_raw = re.sub(pattern, lambda m: m.group(1) + value + m.group(3), raw, count=1, flags=flags)
    path.write_text(new_raw, encoding="utf-8")

    return jsonify({"ok": True})


@app.route("/api/send-email/<slug>", methods=["POST"])
def send_email(slug):
    """Send personalized copy email to a single VC."""
    vcs = load_vcs()
    vc = next((v for v in vcs if v["slug"] == slug), None)
    if not vc:
        return jsonify({"error": "VC not found"}), 404
    if not vc.get("email"):
        return jsonify({"error": "No email on file for this VC"}), 400

    copy = load_copy(slug)
    if not copy:
        return jsonify({"error": "No copy generated yet — generate copy first"}), 400

    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not gmail_user or not gmail_pass:
        return jsonify({"error": "GMAIL_USER or GMAIL_APP_PASSWORD not set in environment"}), 500

    try:
        _send_vc_email(gmail_user, gmail_pass, vc, copy)
        return jsonify({"ok": True, "sent_to": vc["email"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/send-email-bulk", methods=["POST"])
def send_email_bulk():
    """Send emails to multiple VCs at once."""
    data = request.get_json() or {}
    slugs = data.get("slugs", [])
    if not slugs:
        return jsonify({"error": "No slugs provided"}), 400

    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not gmail_user or not gmail_pass:
        return jsonify({"error": "GMAIL_USER or GMAIL_APP_PASSWORD not set in environment"}), 500

    vcs = load_vcs()
    vc_map = {v["slug"]: v for v in vcs}

    sent, failed = [], []
    for slug in slugs:
        vc = vc_map.get(slug)
        if not vc or not vc.get("email"):
            failed.append({"slug": slug, "reason": "No email on file"})
            continue
        copy = load_copy(slug)
        if not copy:
            failed.append({"slug": slug, "reason": "No copy generated"})
            continue
        try:
            _send_vc_email(gmail_user, gmail_pass, vc, copy)
            sent.append(vc["email"])
        except Exception as e:
            failed.append({"slug": slug, "reason": str(e)})

    return jsonify({"ok": True, "sent": sent, "failed": failed})


def _send_vc_email(gmail_user: str, gmail_pass: str, vc: dict, copy: dict):
    """Compose and send personalized copy email to a VC via Gmail SMTP."""
    first_name = vc["name"].split()[0]
    x_post = copy.get("x_post", "").strip()
    linkedin_post = copy.get("linkedin_post", "").strip()
    comment = copy.get("comment", "").strip()

    html = f"""
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto;padding:24px;">
  <p>Hey {first_name},</p>
  <p>We went through every startup in the YC W26 batch using agentic AI founders to stress-test defensibility. The results are live — and we'd love your take.</p>
  <p>We wrote some copy in your voice in case you want to share or engage. Use it, ignore it, or rewrite it — totally up to you.</p>

  <hr style="border:none;border-top:1px solid #e5e5e5;margin:24px 0;">

  <p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#888;">Your X Post</p>
  <p style="background:#f5f5f5;padding:14px 16px;border-radius:8px;font-size:14px;line-height:1.6;">{x_post}</p>

  <p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin-top:20px;">Your LinkedIn Post</p>
  <p style="background:#f5f5f5;padding:14px 16px;border-radius:8px;font-size:14px;line-height:1.6;">{linkedin_post}</p>

  <p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin-top:20px;">Suggested Comment on Our Post</p>
  <p style="background:#f5f5f5;padding:14px 16px;border-radius:8px;font-size:14px;line-height:1.6;">{comment}</p>

  <hr style="border:none;border-top:1px solid #e5e5e5;margin:24px 0;">

  <p>See the full project here: <a href="https://feltsenseproject-production.up.railway.app" style="color:#7c6ff7;">feltsenseproject-production.up.railway.app</a></p>
  <p style="color:#888;font-size:12px;">— Marik &amp; the Feltsense team</p>
</body></html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your copy for the Feltsense YC W26 campaign"
    msg["From"] = gmail_user
    msg["To"] = vc["email"]
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, vc["email"], msg.as_string())


@app.route("/api/mention-count")
def mention_count_route():
    """Return cached @feltsensefund mention count for the last 7 days."""
    count = _fetch_mention_count()
    return jsonify({"count": count})


@app.route("/api/status")
def status():
    vcs = load_vcs()
    return jsonify({
        "total": len(vcs),
        "generated": sum(1 for v in vcs if (OUTPUT_DIR / f"{v['slug']}.md").exists()),
        "vcs": [{"name": v["name"], "slug": v["slug"], "generated": (OUTPUT_DIR / f"{v['slug']}.md").exists()} for v in vcs]
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
