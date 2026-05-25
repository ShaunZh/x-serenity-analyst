#!/usr/bin/env python3
"""
X.com Tweet Scraper — x-analyst skill
======================================
Scrapes all tweets from a given X (Twitter) user since 2025-01-01
using the twscrape library. Outputs structured JSON.

Usage:
    python scraper.py --username <handle> --cookie-path <path> --output-path <path> [--proxy <url>]
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from twscrape import API, AccountsPool, gather
except ImportError:
    print(
        "[ERROR] twscrape is not installed. Run: pip install twscrape",
        file=sys.stderr,
    )
    sys.exit(1)


# ── Constants ────────────────────────────────────────────────────────────────
CUTOFF_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)
PAGE_DELAY_SECONDS = 2          # polite delay between paginated requests
RATE_LIMIT_WAIT = 60            # seconds to wait on rate-limit (429)
DB_PATH = ".claude/skills/x-analyst/accounts.db"


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_tweet_date(raw) -> datetime:
    """Parse tweet date into a timezone-aware datetime."""
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=timezone.utc)
        return raw
    raw = str(raw)
    # Twitter API format: "Thu Oct 26 15:00:00 +0000 2023"
    try:
        dt = datetime.strptime(raw, "%a %b %d %H:%M:%S %z %Y")
    except (ValueError, TypeError):
        # Fallback: try ISO format
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
    return dt


def tweet_to_dict(tweet) -> dict:
    """Extract key fields from a twscrape Tweet object."""
    created = tweet.date if hasattr(tweet, 'date') else getattr(tweet, 'created_at', None)
    return {
        "id": str(tweet.id),
        "text": getattr(tweet, 'rawContent', '') or getattr(tweet, 'text', '') or "",
        "created_at": created.isoformat() if isinstance(created, datetime) else str(created),
        "retweet_count": getattr(tweet, "retweetCount", 0) or getattr(tweet, "retweet_count", 0) or 0,
        "favorite_count": getattr(tweet, "likeCount", 0) or getattr(tweet, "favorite_count", 0) or 0,
    }


def log(msg: str, level: str = "INFO"):
    """Print a timestamped log line."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)


def detect_system_proxy() -> str | None:
    """
    Auto-detect proxy from macOS system preferences (scutil --proxy),
    environment variables, or common proxy ports.
    """
    # 1. Check environment variables first
    for var in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
        val = os.environ.get(var)
        if val:
            log(f"Proxy detected from env ${var}: {val}")
            return val

    # 2. Try macOS scutil --proxy
    try:
        result = subprocess.run(
            ["scutil", "--proxy"],
            capture_output=True, text=True, timeout=5,
        )
        lines = result.stdout.strip().splitlines()
        proxy_info: dict[str, str] = {}
        for line in lines:
            if ":" in line:
                key, _, value = line.partition(":")
                proxy_info[key.strip()] = value.strip()

        # Prefer SOCKS5 proxy (httpx handles socks5 more reliably than
        # HTTP CONNECT tunneling through Clash/V2Ray style proxies)
        if proxy_info.get("SOCKSEnable") == "1":
            host = proxy_info.get("SOCKSProxy", "127.0.0.1")
            port = proxy_info.get("SOCKSPort", "7890")
            url = f"socks5://{host}:{port}"
            log(f"SOCKS5 proxy detected from macOS system preferences: {url}")
            return url

        if proxy_info.get("HTTPEnable") == "1":
            host = proxy_info.get("HTTPProxy", "127.0.0.1")
            port = proxy_info.get("HTTPPort", "7890")
            url = f"http://{host}:{port}"
            log(f"HTTP proxy detected from macOS system preferences: {url}")
            return url
    except Exception:
        pass

    return None


def load_cookies_from_json(cookie_path: str) -> str:
    """
    Load cookies from a JSON file and return as a semicolon-separated string
    in the format twscrape expects: "key1=val1; key2=val2".
    """
    with open(cookie_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, dict):
        # Simple {key: value} format
        return "; ".join(f"{k}={v}" for k, v in data.items())
    elif isinstance(data, list):
        # Array of cookie objects (e.g. from browser extension)
        parts = []
        for cookie in data:
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            if name:
                parts.append(f"{name}={value}")
        return "; ".join(parts)
    else:
        raise ValueError(f"Unexpected cookie format in {cookie_path}")


# ── Main scraping logic ─────────────────────────────────────────────────────

async def scrape_user_tweets(
    username: str,
    cookie_path: str,
    output_path: str,
    proxy: str | None = None,
) -> None:
    """
    Main entry-point: authenticate via cookies, paginate through all
    tweets for *username*, filter to ≥ 2025-01-01, and write JSON.
    """

    # ── 1. Validate cookie file ──────────────────────────────────────────
    cookie_file = Path(cookie_path)
    if not cookie_file.is_file():
        log(f"Cookie file not found: {cookie_path}", "FATAL")
        sys.exit(1)

    # ── 2. Resolve proxy ─────────────────────────────────────────────────
    if proxy is None:
        proxy = detect_system_proxy()
    if proxy:
        log(f"Using proxy: {proxy}")
    else:
        log("No proxy configured — connecting directly to X.com")

    # ── Monkey-patch twscrape's XClIdGen client factory to use our proxy ──
    # twscrape's _make_client() doesn't accept a proxy, causing XClIdGen
    # to fail in environments that require proxy access to x.com.
    if proxy:
        import twscrape.xclid as _xclid
        import httpx as _httpx
        from fake_useragent import UserAgent as _UA
        _original_make_client = _xclid._make_client
        def _patched_make_client() -> _httpx.AsyncClient:
            headers = {"user-agent": _UA().chrome}
            return _httpx.AsyncClient(headers=headers, follow_redirects=True, proxy=proxy, timeout=30.0)
        _xclid._make_client = _patched_make_client
        log("Patched twscrape XClIdGen to use proxy ✓")

    # ── Monkey-patch twscrape's Account.make_client to use higher timeout ──
    # Default httpx timeout of 5s is too short through proxy, causing ConnectTimeout.
    import twscrape.account as _account
    import httpx as _httpx
    _original_account_make_client = _account.Account.make_client
    def _patched_account_make_client(self, proxy: str | None = None) -> _httpx.AsyncClient:
        client = _original_account_make_client(self, proxy)
        client.timeout = _httpx.Timeout(30.0)
        return client
    _account.Account.make_client = _patched_account_make_client
    log("Patched twscrape Account.make_client to use 30s timeout ✓")


    # ── 3. Load cookies and initialise twscrape ──────────────────────────
    log("Loading session cookies …")
    try:
        cookies_str = load_cookies_from_json(str(cookie_file))
    except Exception as exc:
        log(f"Failed to load cookies: {exc}", "FATAL")
        sys.exit(1)

    db_file = Path(DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    # Remove stale DB to force fresh cookie injection
    if db_file.exists():
        db_file.unlink()

    pool = AccountsPool(str(db_file))
    await pool.add_account(
        username="scraper_session",
        password="not_used",
        email="not_used@x.com",
        email_password="not_used",
        cookies=cookies_str,
        proxy=proxy,
    )
    # Mark the account as active without attempting login
    await pool.set_active("scraper_session", True)

    api = API(pool=pool, proxy=proxy)
    log("Cookies loaded and session initialised ✓")

    # ── 4. Resolve user id ───────────────────────────────────────────────
    log(f"Resolving user @{username} …")
    try:
        user = await api.user_by_login(username)
    except Exception as exc:
        log(f"Could not resolve user @{username}: {exc}", "FATAL")
        sys.exit(1)

    if user is None:
        log(f"User @{username} not found", "FATAL")
        sys.exit(1)

    user_id = user.id
    followers = getattr(user, 'followersCount', getattr(user, 'followers_count', '?'))
    log(f"Resolved @{username} → id={user_id} (followers={followers})")

    # ── 5. Load existing cache ───────────────────────────────────────────
    existing_tweets = []
    existing_ids = set()
    output_file = Path(output_path)
    if output_file.is_file():
        try:
            with open(output_file, "r", encoding="utf-8") as fh:
                existing_data = json.load(fh)
                if isinstance(existing_data, dict) and "tweets" in existing_data:
                    existing_tweets = existing_data["tweets"]
                    existing_ids = {str(t["id"]) for t in existing_tweets}
                    log(f"Loaded {len(existing_tweets)} existing cached tweets from {output_file} ✓")
        except Exception as exc:
            log(f"Failed to read existing cache, starting fresh: {exc}", "WARN")

    # ── 6. Collect tweets with date & incremental duplicate filtering ────
    all_tweets: list[dict] = []
    count = 0
    hit_boundary = False
    duplicate_count = 0

    log("Beginning tweet collection (target: 2025-01-01 → present) …")

    try:
        async for tweet in api.user_tweets(user_id, limit=-1):
            count += 1
            tweet_id = str(tweet.id)
            tweet_dt = parse_tweet_date(tweet.date if hasattr(tweet, 'date') else tweet.created_at)

            # Strict boundary: stop once we hit pre-2025
            if tweet_dt < CUTOFF_DATE:
                log(
                    f"  ↳ Hit pre-2025 tweet ({tweet_dt.strftime('%Y-%m-%d')}). "
                    "Boundary reached — stopping.",
                )
                hit_boundary = True
                break

            # Incremental boundary: if we see 5 consecutive already-cached IDs,
            # we can stop, as we've caught up with the existing archive.
            if tweet_id in existing_ids:
                duplicate_count += 1
                if duplicate_count >= 5:
                    log("  ↳ Encountered 5 consecutive cached tweets. Up-to-date — stopping incremental sync.")
                    break
            else:
                duplicate_count = 0

            all_tweets.append(tweet_to_dict(tweet))

            if count % 50 == 0:
                log(f"  Progress: {count} tweets scanned, {len(all_tweets)} kept")

    except Exception as exc:
        exc_str = str(exc).lower()
        if "rate" in exc_str or "429" in exc_str or "too many" in exc_str:
            log(f"Rate limited after {count} tweets. Collected {len(all_tweets)} so far.", "WARN")
        elif "unauthorized" in exc_str or "401" in exc_str or "forbidden" in exc_str:
            log(
                "Session cookies appear invalid or expired. "
                "Please re-export cookies from your browser.",
                "FATAL",
            )
            sys.exit(1)
        else:
            log(f"Error during collection: {exc}", "WARN")

    log(f"Scanned {count} tweets total, kept {len(all_tweets)} new tweets (2025+)")

    # ── 7. Deduplicate and merge by tweet id ─────────────────────────────
    combined_tweets = all_tweets + existing_tweets
    seen_ids: set[str] = set()
    unique_tweets: list[dict] = []
    for t in combined_tweets:
        if t["id"] not in seen_ids:
            seen_ids.add(t["id"])
            unique_tweets.append(t)
    unique_tweets.sort(key=lambda t: t["created_at"], reverse=True)

    # ── 8. Write output JSON ─────────────────────────────────────────────
    output_file.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "meta": {
            "username": username,
            "user_id": str(user_id),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_tweets": len(unique_tweets),
            "date_range": {
                "from": "2025-01-01",
                "to": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            },
        },
        "tweets": unique_tweets,
    }

    with open(output_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    log(f"Done ✓  {len(unique_tweets)} total tweets saved to {output_file}")


# ── CLI entrypoint ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scrape X.com user tweets since 2025 via twscrape.",
    )
    parser.add_argument(
        "--username",
        required=True,
        help="X handle to scrape (without the @ sign).",
    )
    parser.add_argument(
        "--cookie-path",
        required=True,
        help="Path to the x_cookies.json file exported from your browser.",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        help="File path for the output JSON (will be created/overwritten).",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="Proxy URL (e.g. http://127.0.0.1:7890 or socks5://127.0.0.1:1080). "
             "Auto-detected from system settings if not specified.",
    )
    args = parser.parse_args()

    log(f"x-analyst scraper starting — target: @{args.username}")
    asyncio.run(
        scrape_user_tweets(
            username=args.username,
            cookie_path=args.cookie_path,
            output_path=args.output_path,
            proxy=args.proxy,
        )
    )


if __name__ == "__main__":
    main()
