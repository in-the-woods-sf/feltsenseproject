"""
Claude-powered social copy generator.

For each VC, takes their scraped profile signals and campaign brief,
then generates personalized post copy, a comment, and our reply.
Uses claude-opus-4-6 with adaptive thinking and prompt caching
on the shared campaign brief.
"""

import re
import anthropic
from dataclasses import dataclass
from typing import Optional
from scraper import ProfileData


@dataclass
class GeneratedCopy:
    name: str
    firm: str
    standalone_post: str
    comment: str               # Suggested copy for the VC to post ON Feltsense's post
    our_comment: str           # What Feltsense/Marik drops ON the VC's own post
    our_reply_casual: str      # Option A: warm thanks / acknowledgment
    our_reply_insight: str     # Option B: unintuitive push that deepens the thread
    our_reply_tease: str       # Option C: hint at more coming / stay tuned
    voice_notes: str
    insufficient_data: bool = False
    post_summary: str = ""        # Manually-entered sculpture/post summary (not AI-generated)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a social media copywriter for a VC and startup-focused campaign.
You specialize in writing in other people's voices — capturing their exact cadence, \
vocabulary, and register from their public posts.

Rules you must follow:
- Active voice only: "is building," "just shipped," never "has built"
- One target at a time when tagging people — only tag if there's a specific, individual reason
- No AI tells: no "full stop," no unnatural colons, no em dashes (—), no "delve"
- Tone: confident and direct — not stiff, not too casual
- Emojis: one or two max, only where truly earned; no clusters, no decoration
- In-process framing: keep things alive and ongoing, not retrospective
- Big vision posts: leave the reader with a question, not a handed conclusion
- Keep X posts at or under 280 characters (single tweet); LinkedIn posts can be longer and reflective
- Do not mention AI writing this copy
- Write as if you ARE this person — first person, their voice
- Enthusiasm calibration: match the person's natural energy level but always stay on the composed side of it. If they are naturally hype-forward, bring it down one notch — keep the spark, cut the exclamation-energy. The goal is "clearly excited about this idea" not "losing their mind over it". Never use words like "insane", "wild", "crazy", or "don't sleep on" even if the person uses them — replace with something sharper and more considered.
"""

_TONE_ANALYSIS_PROMPT = """\
Here are recent posts from {name} ({firm}):

---
{posts_block}
---

Bio/about: {bio}

In 3-5 concise bullet points, describe their voice.

IMPORTANT: [X] posts are the primary source — that is their real, unguarded register.
[LinkedIn] posts are supplementary context only. LinkedIn voice is often more polished
and performative than how someone actually writes, so do not let it override signals
from X. If X and LinkedIn feel different, trust X.

Cover:
- Sentence length and rhythm (draw from X examples)
- Formality level (scale of 1-10, 10 = most formal) — base this on X
- Emoji usage patterns
- Recurring vocabulary, phrases, or themes from X
- Overall register (punchy/measured/lyrical/etc.)

Be specific. Quote X examples where helpful. Keep it tight — this is internal notes."""


_COPY_GENERATION_PROMPT = """\
Write social copy for {name}, Partner at {firm}, for the following campaign.

=== VOICE PROFILE ===
{voice_notes}

=== CAMPAIGN BRIEF ===
{campaign_brief}

=== INSTRUCTIONS ===
Write three pieces in {name}'s voice:

1. STANDALONE POST (X + LinkedIn)
   - X version: 200-280 characters (use the space — don't leave it short), punchy, one question or one bold claim
   - LinkedIn version: 60-100 words HARD LIMIT (count before submitting). Punchy and direct — not a wall of text, no listicles, no bullet points. Still leaves reader with a question.
   - Both should feel like {name} decided to write this unprompted
   - Aim for "quietly confident" over "hyped up" — the idea should carry the energy, not the adjectives
   - FRAMING (NON-NEGOTIABLE): Feltsense went through EVERY startup in the YC W26 batch — not 20, not "some." The full scope is the entire batch. The public launch features 20 deep-dive replications with live products built; the full PDF covers every company. NEVER say "replicated 20 startups" or frame this as 20 companies. Always say "went through the entire YC W26 batch," "every startup in the batch," or "the whole W26 batch." If referencing the 20, it's only "20 featured deep-dives" or "20 live builds" — always in the context of the full batch. This framing applies to every piece of copy in every future version.

2. THEIR COMMENT (suggested copy for {name} to post on Feltsense's post)
   - 1-3 sentences max
   - Sounds like a natural, considered reaction from {name} — not a fan reply, more like a peer observation
   - No generic praise, no hype words — something specific, grounded, and in their voice
   - Written FROM {name}'s perspective, as if they are commenting on Feltsense's content

3. OUR COMMENT (what Feltsense / Marik drops on {name}'s OWN posts)
   - STRICTLY 1 sentence ONLY — no exceptions, no two-sentence exceptions, never more than one sentence
   - Should feel like a genuine peer reaction — not promotional, not begging for engagement
   - Reference something specific from their actual posts if possible
   - Ends the exchange feeling like two people who see the world similarly
   - Written FROM Feltsense's perspective, engaging with {name}'s content

4. OUR REPLY to their comment — two options (for Feltsense / Marik to pick from)
   Both are written as Feltsense (@feltsense) responding personally to {name}.
   Each is 1-2 sentences. Pick up something specific from their comment.

   OPTION A — CASUAL: Warm, genuine thanks or acknowledgment. Feels like a founder
   who appreciates the support without overdoing it. Human, not corporate.

   OPTION B — INSIGHT: A single unintuitive or surprising observation that pushes
   the thread deeper. Something that reframes the conversation or reveals something
   unexpected from the project — the kind of thing that makes someone stop scrolling.
   Not a summary of what we did. A new angle they haven't considered yet.

Format your response EXACTLY as:
### X POST
[200-280 characters — aim to fill the space, not leave it short]

### LINKEDIN POST
[60-100 words HARD LIMIT — count every word, do not exceed 100]

### THEIR COMMENT ON OUR POST
[1-3 sentences — written as {name} commenting on Feltsense's post]

### OUR COMMENT ON THEIR POST
[1 sentence ONLY — written as Feltsense commenting on {name}'s post]

### OUR REPLY A — CASUAL
[1-2 sentences]

### OUR REPLY B — INSIGHT
[1-2 sentences]

### VOICE NOTES
[1-2 sentences summarizing the tone/style used]"""


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class CopyGenerator:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.model = model

    def _build_posts_block(self, twitter: Optional[ProfileData], linkedin: Optional[ProfileData]) -> tuple[str, str]:
        """Build a combined posts block and bio string from scraped data.

        X/Twitter is the primary voice signal — this is where people write in their
        natural register. LinkedIn is supplementary context only (bio, role framing).
        We use up to 30 X posts and cap LinkedIn at 3 posts to avoid LinkedIn's more
        polished, performative tone bleeding into the voice model.
        """
        x_posts: list[str] = []
        linkedin_posts: list[str] = []
        bio_parts: list[str] = []

        if twitter and twitter.posts:
            x_posts.extend([f"[X] {p}" for p in twitter.posts[:30]])
        if twitter and twitter.bio:
            bio_parts.append(f"X bio: {twitter.bio}")

        if linkedin and linkedin.posts:
            # Cap at 3 — LinkedIn voice is often more polished/performative than real
            linkedin_posts.extend([f"[LinkedIn] {p}" for p in linkedin.posts[:3]])
        if linkedin and linkedin.bio:
            bio_parts.append(f"LinkedIn about: {linkedin.bio}")

        # X posts first, LinkedIn after — order signals priority to the tone analyzer
        all_posts = x_posts + linkedin_posts
        posts_block = "\n\n".join(all_posts) if all_posts else "(no posts scraped)"
        bio = " | ".join(bio_parts) if bio_parts else "(no bio available)"
        return posts_block, bio

    def _analyze_tone(self, name: str, firm: str, posts_block: str, bio: str) -> str:
        """Quick Claude call to extract voice signals from scraped posts."""
        prompt = _TONE_ANALYSIS_PROMPT.format(
            name=name, firm=firm, posts_block=posts_block, bio=bio
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        )
        for block in response.content:
            if block.type == "text":
                return block.text
        return "(tone analysis unavailable)"

    def generate(
        self,
        name: str,
        firm: str,
        campaign_brief: str,
        twitter: Optional[ProfileData] = None,
        linkedin: Optional[ProfileData] = None,
    ) -> GeneratedCopy:
        """Generate all copy for a single VC."""
        posts_block, bio = self._build_posts_block(twitter, linkedin)
        insufficient = posts_block == "(no posts scraped)"

        # Step 1: tone analysis (skip if no data)
        if insufficient:
            voice_notes = (
                "Insufficient public data — no posts could be scraped. "
                "Copy below uses general VC voice conventions for this person."
            )
        else:
            voice_notes = self._analyze_tone(name, firm, posts_block, bio)

        # Step 2: generate copy with prompt caching on the campaign brief
        # Cache the brief since it's shared across every VC in a run
        copy_prompt = _COPY_GENERATION_PROMPT.format(
            name=name,
            firm=firm,
            voice_notes=voice_notes,
            campaign_brief=campaign_brief,
        )

        # Stream the response (copy can be long, prevents timeouts)
        x_post = linkedin_post = comment = our_comment = ""
        our_reply_casual = our_reply_insight = our_reply_tease = final_voice_notes = ""

        with self.client.messages.stream(
            model=self.model,
            max_tokens=4000,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                },
                {
                    "type": "text",
                    "text": f"CAMPAIGN BRIEF (shared context):\n\n{campaign_brief}",
                    "cache_control": {"type": "ephemeral"},  # cache across all VC calls
                },
            ],
            messages=[{"role": "user", "content": copy_prompt}],
        ) as stream:
            full_response = stream.get_final_message()

        # Parse structured response
        raw = ""
        for block in full_response.content:
            if block.type == "text":
                raw = block.text
                break

        x_post = _extract_section(raw, "X POST")
        linkedin_post = _extract_section(raw, "LINKEDIN POST")
        comment = _extract_section(raw, "THEIR COMMENT ON OUR POST")
        our_comment = _extract_section(raw, "OUR COMMENT ON THEIR POST")
        our_reply_casual = _extract_section(raw, "OUR REPLY A — CASUAL")
        our_reply_insight = _extract_section(raw, "OUR REPLY B — INSIGHT")
        our_reply_tease = _extract_section(raw, "OUR REPLY C — TEASE")
        final_voice_notes = _extract_section(raw, "VOICE NOTES") or voice_notes

        return GeneratedCopy(
            name=name,
            firm=firm,
            standalone_post=f"**X:**\n{x_post}\n\n**LinkedIn:**\n{linkedin_post}",
            comment=comment,
            our_comment=our_comment,
            our_reply_casual=our_reply_casual,
            our_reply_insight=our_reply_insight,
            our_reply_tease=our_reply_tease,
            voice_notes=final_voice_notes,
            insufficient_data=insufficient,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_section(text: str, header: str) -> str:
    """Extract content under a ### HEADER section."""
    pattern = rf"###\s+{re.escape(header)}\s*\n(.*?)(?=###|\Z)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return ""
