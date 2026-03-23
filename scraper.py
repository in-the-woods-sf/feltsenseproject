"""
Social media scraper for Twitter/X and LinkedIn profiles.

Tries multiple strategies per platform and degrades gracefully.
Returns raw post text and profile signals for tone analysis.
"""

import re
import time
import random
import httpx
from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup


# Rotating user agents to reduce bot detection
_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# Public nitter instances (some may be down — we try each)
_NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
]


@dataclass
class ProfileData:
    name: str
    platform: str                     # "twitter" | "linkedin"
    username: str = ""
    bio: str = ""
    posts: list[str] = field(default_factory=list)
    scrape_status: str = "not_attempted"  # "ok" | "partial" | "failed"
    notes: str = ""


def _random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    time.sleep(random.uniform(min_s, max_s))


def _get_headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def _extract_x_username(x_url: str) -> str:
    """Extract @handle from a Twitter/X URL."""
    if not x_url:
        return ""
    x_url = x_url.rstrip("/")
    parts = x_url.split("/")
    return parts[-1].lstrip("@") if parts else ""


def _extract_linkedin_username(linkedin_url: str) -> str:
    """Extract profile slug from a LinkedIn URL."""
    if not linkedin_url:
        return ""
    m = re.search(r"linkedin\.com/in/([^/?#]+)", linkedin_url)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# Twitter/X scraping
# ---------------------------------------------------------------------------

def _scrape_twitter_via_nitter(username: str) -> ProfileData:
    """Try fetching the profile from a nitter instance."""
    profile = ProfileData(name=username, platform="twitter", username=username)

    for instance in _NITTER_INSTANCES:
        url = f"{instance}/{username}"
        try:
            with httpx.Client(timeout=15, follow_redirects=True) as client:
                resp = client.get(url, headers=_get_headers())
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            # Bio
            bio_el = soup.select_one(".profile-bio")
            if bio_el:
                profile.bio = bio_el.get_text(strip=True)

            # Posts — nitter uses `.tweet-content` or `.timeline-item .content`
            tweets = soup.select(".timeline-item .tweet-content")
            if not tweets:
                tweets = soup.select(".tweet-content")

            posts = []
            for t in tweets[:30]:
                text = t.get_text(separator=" ", strip=True)
                if text and len(text) > 10:
                    posts.append(text)

            if posts:
                profile.posts = posts
                profile.scrape_status = "ok"
                profile.notes = f"Scraped via {instance}"
                return profile

        except Exception:
            continue

    profile.scrape_status = "failed"
    profile.notes = "All nitter instances failed or returned no posts"
    return profile


def _scrape_twitter_api(username: str, bearer_token: str) -> ProfileData:
    """Use Twitter API v2 bearer token to fetch recent tweets."""
    profile = ProfileData(name=username, platform="twitter", username=username)

    try:
        with httpx.Client(timeout=20) as client:
            # Look up user ID by username
            user_resp = client.get(
                f"https://api.twitter.com/2/users/by/username/{username}",
                params={"user.fields": "description,public_metrics"},
                headers={"Authorization": f"Bearer {bearer_token}"},
            )
            if user_resp.status_code != 200:
                profile.scrape_status = "failed"
                profile.notes = f"Twitter API user lookup failed: {user_resp.status_code}"
                return profile

            user_data = user_resp.json().get("data", {})
            user_id = user_data.get("id")
            profile.bio = user_data.get("description", "")

            if not user_id:
                profile.scrape_status = "failed"
                profile.notes = "Twitter API returned no user ID"
                return profile

            # Fetch recent tweets
            tweets_resp = client.get(
                f"https://api.twitter.com/2/users/{user_id}/tweets",
                params={
                    "max_results": 30,
                    "tweet.fields": "text,created_at",
                    "exclude": "retweets,replies",
                },
                headers={"Authorization": f"Bearer {bearer_token}"},
            )
            if tweets_resp.status_code != 200:
                profile.scrape_status = "partial"
                profile.notes = "Got bio only; tweets request failed"
                return profile

            tweets_data = tweets_resp.json().get("data", [])
            profile.posts = [t["text"] for t in tweets_data if t.get("text")]
            profile.scrape_status = "ok" if profile.posts else "partial"
            profile.notes = "Twitter API v2"
            return profile

    except Exception as e:
        profile.scrape_status = "failed"
        profile.notes = f"Twitter API exception: {e}"
        return profile


def scrape_twitter(x_url: str, twitter_bearer_token: Optional[str] = None) -> ProfileData:
    """
    Main Twitter scraping entry point.
    1. Twitter API bearer token (if provided)
    2. Nitter instances
    3. Returns failed ProfileData on all failures
    """
    username = _extract_x_username(x_url)
    if not username:
        p = ProfileData(name="unknown", platform="twitter")
        p.scrape_status = "failed"
        p.notes = f"Could not extract username from URL: {x_url}"
        return p

    # Try API first (best quality)
    if twitter_bearer_token:
        result = _scrape_twitter_api(username, twitter_bearer_token)
        if result.scrape_status == "ok":
            return result

    # Try nitter
    _random_delay(0.5, 1.5)
    result = _scrape_twitter_via_nitter(username)
    return result


# ---------------------------------------------------------------------------
# LinkedIn scraping
# ---------------------------------------------------------------------------

def scrape_linkedin(linkedin_url: str) -> ProfileData:
    """
    Attempt to scrape LinkedIn public profile.
    LinkedIn is heavily protected; this is best-effort.
    Returns partial data if it gets anything useful.
    """
    slug = _extract_linkedin_username(linkedin_url)
    profile = ProfileData(
        name=slug, platform="linkedin", username=slug
    )

    if not slug:
        profile.scrape_status = "failed"
        profile.notes = f"Could not extract slug from URL: {linkedin_url}"
        return profile

    try:
        # Try the public profile page
        url = f"https://www.linkedin.com/in/{slug}/"
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(url, headers=_get_headers())

        if resp.status_code in (999, 403, 429, 401):
            profile.scrape_status = "failed"
            profile.notes = f"LinkedIn blocked request (status {resp.status_code}) — this is normal"
            return profile

        if resp.status_code != 200:
            profile.scrape_status = "failed"
            profile.notes = f"LinkedIn returned status {resp.status_code}"
            return profile

        soup = BeautifulSoup(resp.text, "lxml")

        # Extract any visible text signals
        # LinkedIn sometimes renders partial content for crawlers
        about_section = soup.find("section", {"data-section": "summary"})
        if not about_section:
            about_section = soup.find("div", class_=re.compile(r"summary|about", re.I))

        if about_section:
            profile.bio = about_section.get_text(separator=" ", strip=True)[:500]

        # Try to grab any post-like text snippets
        post_candidates = soup.find_all(
            ["p", "span"],
            class_=re.compile(r"post|update|feed|content|body", re.I)
        )
        posts = []
        seen = set()
        for el in post_candidates:
            text = el.get_text(separator=" ", strip=True)
            if len(text) > 40 and text not in seen:
                seen.add(text)
                posts.append(text)
            if len(posts) >= 15:
                break

        profile.posts = posts
        profile.scrape_status = "partial" if (profile.bio or posts) else "failed"
        profile.notes = (
            "LinkedIn partial scrape (not logged in)" if profile.scrape_status == "partial"
            else "LinkedIn: no meaningful content extracted (likely JS-gated)"
        )
        return profile

    except Exception as e:
        profile.scrape_status = "failed"
        profile.notes = f"LinkedIn scrape exception: {e}"
        return profile


# ---------------------------------------------------------------------------
# Combined profile fetch
# ---------------------------------------------------------------------------

def fetch_all_signals(
    name: str,
    x_url: str,
    linkedin_url: str,
    twitter_bearer_token: Optional[str] = None,
) -> dict[str, ProfileData]:
    """Fetch Twitter and LinkedIn signals for a person."""
    results: dict[str, ProfileData] = {}

    if x_url:
        results["twitter"] = scrape_twitter(x_url, twitter_bearer_token)
        results["twitter"].name = name
        _random_delay(1.0, 2.5)

    if linkedin_url:
        results["linkedin"] = scrape_linkedin(linkedin_url)
        results["linkedin"].name = name
        _random_delay(1.5, 3.0)

    return results
