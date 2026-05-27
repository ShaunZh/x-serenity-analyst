#!/usr/bin/env python3
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Core configurations
WIKI_ROOT = Path("wiki")
RAW_PATH = WIKI_ROOT / "raw" / "tweets_aleabitoreddit.json"
CACHE_PATH = WIKI_ROOT / "raw" / "translations_cache.json"
CONCEPTS_DIR = WIKI_ROOT / "concepts"
TICKERS_DIR = WIKI_ROOT / "tickers"
REPORTS_DIR = WIKI_ROOT / "reports"
MONTHLY_DIR = WIKI_ROOT / "monthly"
INDEX_PATH = WIKI_ROOT / "index.md"

# Define target tickers with matching patterns and descriptions
TICKER_DEFS = {
    "SIVE": {
        "pattern": r"\$SIVE|sivers",
        "name": "Sivers Semiconductors",
        "sector": "Silicon Photonics / CPO Laser Sources",
        "role": "Exclusive high-power DFB laser array provider for major CPO engines (Ayar, Lightmatter, POET, etc.). Volume producer of 1.6T LRO with Jabil.",
    },
    "AXTI": {
        "pattern": r"\$AXTI|axt",
        "name": "AXT Inc.",
        "sector": "Substrates / Compounds",
        "role": "Near-monopoly in global high-purity Indium Phosphide (InP) substrate manufacturing. Crucial raw material chokehold.",
    },
    "SOI": {
        "pattern": r"\$SOI|soitec",
        "name": "Soitec",
        "sector": "Substrates / Silicon Photonics Wafers",
        "role": "Monopoly provider of SOI (Silicon-on-Insulator) wafers required for Silicon Photonics chip designs.",
    },
    "LPK": {
        "pattern": r"\$LPK|lpkf",
        "name": "LPKF Laser & Electronics",
        "sector": "Advanced Packaging Equipment",
        "role": "The 'ASML of Glass Substrates' (TGV laser drilling). Holds ~80% global market share in advanced glass packaging tools.",
    },
    "IQE": {
        "pattern": r"\$IQE|iqe",
        "name": "IQE plc",
        "sector": "Epiwafers / Western Supply Chain",
        "role": "Crucial European epiwafer manufacturer for optoelectronic and RF devices, systemic backstop for MACOM & Lumentum.",
    },
    "AAOI": {
        "pattern": r"\$AAOI|aaoi",
        "name": "Applied Optoelectronics",
        "sector": "Optical Transceiver Manufacturing",
        "role": "Made-in-America supply chain anchor for CW laser fabs and high-speed (800G/1.6T) assembly, serving Microsoft and Amazon.",
    },
    "JBL": {
        "pattern": r"\$JBL|jabil",
        "name": "Jabil",
        "sector": "System Assembly & ODM",
        "role": "Mass manufacturing partner for 1.6T LRO transceivers using Sivers laser arrays. Primary commercial volume driver.",
    },
    "NBIS": {
        "pattern": r"\$NBIS|nebius",
        "name": "Nebius Group",
        "sector": "AI Cloud / Neocloud",
        "role": "Premium Neocloud with direct Nvidia capital financing, operating advanced full-stack GPU clusters with high margins.",
    },
    "FOCI": {
        "pattern": r"foci|3363",
        "name": "Foci Fiber Optic Communications",
        "sector": "CPO Packaging Components",
        "role": "Taiwan-based manufacturer of Fiber Array Units (FAU) and high-precision fiber couplings for TSMC/Nvidia CPO deployments.",
    },
    "AEVA": {
        "pattern": r"\$AEVA|aeva",
        "name": "Aeva Technologies",
        "sector": "LIDAR / Robotics Integration",
        "role": "Pioneering 4D FMCW LIDAR provider powered by Sivers laser engines, integrating downstream into LG Innotek and Boston Dynamics.",
    },
}

# Define target concepts with matching patterns and descriptions
CONCEPT_DEFS = {
    "CPO": {
        "pattern": r"cpo|co-packaged|共封装",
        "name": "Co-Packaged Optics (共封装光学)",
        "summary": "Next-generation optical packaging architecture that places optical transceivers directly on the same multi-chip module as the ASIC/switch, bypassing traditional pluggable copper/fiber bottlenecks.",
    },
    "Silicon Photonics": {
        "pattern": r"siph|silicon photonics|硅光",
        "name": "Silicon Photonics (硅光子学)",
        "summary": "The integration of active and passive optical components (lasers, modulators, detectors) directly onto silicon chips, leveraging mature semiconductor fabrication lines to scale light-speed communication.",
    },
    "Glass Substrates": {
        "pattern": r"glass substrate|玻璃基板|lpkf|lpk",
        "name": "Glass Substrates (玻璃基板)",
        "summary": "The paradigm shift in advanced packaging away from organic materials. Enables tighter interconnects, zero warpage, and higher thermal tolerances for next-gen edge and data center processors.",
    },
    "InP Substrates": {
        "pattern": r"inp|indium phosphide|磷化铟",
        "name": "Indium Phosphide (InP) Substrates (磷化铟衬底)",
        "summary": "The critical compound semiconductor material that acts as the physical foundation for fabricating high-performance semiconductor lasers and photodetectors used throughout the AI optical infrastructure.",
    },
    "Advanced Packaging": {
        "pattern": r"advanced packaging|先進封裝|先进包装|tgv|cowos",
        "name": "Advanced Packaging (先进封装)",
        "summary": "High-density semiconductor packaging techniques (such as CoWoS, TGV, and 3D stacking) used to bridge the memory and computing gaps when Moore's Law scaling hits physical boundaries.",
    },
    "Physical AI": {
        "pattern": r"physical ai|humanoid|robotics|机器人|人形机器人",
        "name": "Physical AI & Humanoids (物理智能与人形机器人)",
        "summary": "The convergence of advanced AI foundational models with physical hardware, mapping photonics/laser supply chains directly onto real-time sensor processing, FMCW LIDAR, and robotic joints.",
    },
}


def log(msg: str):
    print(f"[WIKI COMPILER] {msg}")


def clean_text(text: str) -> str:
    # Strip URL attachments from X posts for clean reading
    return re.sub(r"https://t\.co/\S+", "", text).strip()


def extract_tweet_ids_from_md(filepath: Path) -> set:
    """Extract tweet IDs already present in a markdown file."""
    if not filepath.is_file():
        return set()
    ids = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            # Ticker/concept format: ID: `1234567890`
            m = re.search(r"ID:\s*`(\d+)`", line)
            if m:
                ids.add(m.group(1))
                continue
            # Monthly format: status/1234567890
            m = re.search(r"/status/(\d+)", line)
            if m:
                ids.add(m.group(1))
    return ids


def render_timeline_entry(tweet: dict, idx: int, trans_cache: dict) -> str:
    """Render a single tweet entry for ticker/concept timelines."""
    lines = []
    cleaned = clean_text(tweet["text"]).replace("\n", "\n    ")
    dt_str = tweet["created_at"][:10]
    tweet_id = tweet["id"]
    lines.append(
        f"{idx}. **{dt_str}** (❤️ {tweet['favorite_count']} | 🔁 {tweet['retweet_count']} | "
        f"ID: `{tweet_id}` | [X.com Post](https://x.com/aleabitoreddit/status/{tweet_id}))"
    )
    lines.append(f"    {cleaned}")
    if str(tweet_id) in trans_cache:
        zh_trans = trans_cache[str(tweet_id)]["zh"].replace("\n", "\n    > ")
        lines.append(f"    > [!TIP] **中文译文**\n    > {zh_trans}")
    lines.append("")
    return "\n".join(lines)


def compile_tickers(ticker_tweets: dict, trans_cache: dict, full_rebuild: bool):
    """Compile all ticker files. Incremental by default, full rebuild with --full."""
    for tk, defs in TICKER_DEFS.items():
        matched = ticker_tweets[tk]
        filepath = TICKERS_DIR / f"{tk}.md"

        # Determine linked concepts
        linked_concepts = []
        for cp, cdefs in CONCEPT_DEFS.items():
            for tweet in matched:
                if re.search(cdefs["pattern"], tweet["text"].lower()):
                    linked_concepts.append(cp)
                    break

        # Full rebuild if file doesn't exist or --full flag
        if full_rebuild or not filepath.is_file():
            log(f"  Ticker ${tk}: full rebuild with {len(matched)} tweets.")
            _write_ticker_full(tk, defs, matched, linked_concepts, trans_cache, filepath)
            continue

        # Incremental mode
        existing_ids = extract_tweet_ids_from_md(filepath)
        new_tweets = [t for t in matched if t["id"] not in existing_ids]

        if not new_tweets:
            log(f"  Ticker ${tk}: no new tweets, skipping.")
            continue

        log(f"  Ticker ${tk}: {len(new_tweets)} new tweets to prepend "
            f"(had {len(existing_ids)} existing).")

        # Read old file, extract the pre-timeline portion (header + thesis)
        with open(filepath, "r", encoding="utf-8") as f:
            old_content = f.read()

        timeline_marker = "## 📜 Historical Timeline (Reverse Chronological)"
        marker_pos = old_content.find(timeline_marker)

        if marker_pos == -1:
            log(f"  Ticker ${tk}: timeline marker not found, falling back to full rebuild.")
            _write_ticker_full(tk, defs, matched, linked_concepts, trans_cache, filepath)
            continue

        # Keep everything before the timeline header (header + thesis)
        prefix = old_content[:marker_pos + len(timeline_marker)]

        # Deduplicate all tweets (existing + new) and sort by date descending
        all_tweets = {t["id"]: t for t in matched}
        sorted_tweets = sorted(all_tweets.values(), key=lambda t: t["created_at"], reverse=True)

        # Rebuild timeline
        timeline_lines = ["\n"]
        for idx, tweet in enumerate(sorted_tweets, 1):
            timeline_lines.append(render_timeline_entry(tweet, idx, trans_cache))

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(prefix)
            f.write("\n".join(timeline_lines))


def _write_ticker_full(tk: str, defs: dict, matched: list, linked_concepts: list,
                       trans_cache: dict, filepath: Path):
    """Full rebuild of a single ticker file."""
    content = []
    content.append(f"# 📈 Ticker Study: ${tk} ({defs['name']})")
    content.append("")
    content.append(f"> **Sector**: `{defs['sector']}`")
    content.append(f"> **Industrial Role**: {defs['role']}")
    content.append("")

    if linked_concepts:
        links_str = " | ".join([f"[[{c}]]" for c in linked_concepts])
        content.append(f"🔗 **Related Concepts**: {links_str}")
        content.append("")

    content.append("## 💡 Core Investment Thesis")
    content.append("Auto-extracted from Serenity's timeline:")
    if matched:
        thesis_tweet = max(matched, key=lambda tw: len(tw["text"]))
        cleaned_thesis = clean_text(thesis_tweet["text"]).replace("\n", "\n> ")
        thesis_id = thesis_tweet["id"]
        content.append(
            f"> [!NOTE]\n> {cleaned_thesis}\n> \n> — *Source Tweet ID: `{thesis_id}` "
            f"([X.com Post](https://x.com/aleabitoreddit/status/{thesis_id}))*"
        )
        if str(thesis_id) in trans_cache:
            zh_thesis = trans_cache[str(thesis_id)]["zh"].replace("\n", "\n> ")
            content.append(f"\n> [!TIP] **中文译文**\n> {zh_thesis}")
    else:
        content.append("> No direct analytical thesis scraped yet.")
    content.append("")

    content.append("## 📜 Historical Timeline (Reverse Chronological)")
    if matched:
        sorted_tweets = sorted(matched, key=lambda t: t["created_at"], reverse=True)
        for idx, tweet in enumerate(sorted_tweets, 1):
            content.append(render_timeline_entry(tweet, idx, trans_cache))
    else:
        content.append("No posts recorded.")

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write("\n".join(content))


def compile_concepts(concept_tweets: dict, trans_cache: dict, full_rebuild: bool):
    """Compile all concept files. Incremental by default, full rebuild with --full."""
    for cp, defs in CONCEPT_DEFS.items():
        matched = concept_tweets[cp]
        filepath = CONCEPTS_DIR / f"{cp}.md"

        # Determine linked tickers
        linked_tickers = []
        for tk, tdefs in TICKER_DEFS.items():
            for tweet in matched:
                if re.search(tdefs["pattern"], tweet["text"].lower()):
                    linked_tickers.append(tk)
                    break

        # Full rebuild if file doesn't exist or --full flag
        if full_rebuild or not filepath.is_file():
            log(f"  Concept [{cp}]: full rebuild with {len(matched)} tweets.")
            _write_concept_full(cp, defs, matched, linked_tickers, trans_cache, filepath)
            continue

        # Incremental mode
        existing_ids = extract_tweet_ids_from_md(filepath)
        new_tweets = [t for t in matched if t["id"] not in existing_ids]

        if not new_tweets:
            log(f"  Concept [{cp}]: no new tweets, skipping.")
            continue

        log(f"  Concept [{cp}]: {len(new_tweets)} new tweets to prepend "
            f"(had {len(existing_ids)} existing).")

        with open(filepath, "r", encoding="utf-8") as f:
            old_content = f.read()

        timeline_marker = "## 📜 Analytical Quotes from Timeline"
        marker_pos = old_content.find(timeline_marker)

        if marker_pos == -1:
            log(f"  Concept [{cp}]: timeline marker not found, falling back to full rebuild.")
            _write_concept_full(cp, defs, matched, linked_tickers, trans_cache, filepath)
            continue

        prefix = old_content[:marker_pos + len(timeline_marker)]

        # Deduplicate and sort
        all_tweets = {t["id"]: t for t in matched}
        sorted_tweets = sorted(all_tweets.values(), key=lambda t: t["created_at"], reverse=True)

        timeline_lines = ["\n"]
        for idx, tweet in enumerate(sorted_tweets, 1):
            timeline_lines.append(render_timeline_entry(tweet, idx, trans_cache))

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(prefix)
            f.write("\n".join(timeline_lines))


def _write_concept_full(cp: str, defs: dict, matched: list, linked_tickers: list,
                        trans_cache: dict, filepath: Path):
    """Full rebuild of a single concept file."""
    content = []
    content.append(f"# 🧪 Concept: {defs['name']}")
    content.append("")
    content.append(f"**Brief Summary**:\n{defs['summary']}")
    content.append("")

    if linked_tickers:
        links_str = " | ".join([f"[[{tk}]]" for tk in linked_tickers])
        content.append(f"🔗 **Primary Tickers**: {links_str}")
        content.append("")

    content.append("## 📜 Analytical Quotes from Timeline")
    if matched:
        sorted_tweets = sorted(matched, key=lambda t: t["created_at"], reverse=True)
        for idx, tweet in enumerate(sorted_tweets, 1):
            content.append(render_timeline_entry(tweet, idx, trans_cache))
    else:
        content.append("No mentions recorded.")

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write("\n".join(content))


def compile_monthly(tweets: list, trans_cache: dict, full_rebuild: bool):
    """Compile monthly archive files. Incremental by default."""
    # Define Ticker and Concept patterns for filter matching
    all_ticker_patterns = [defs["pattern"] for defs in TICKER_DEFS.values()]
    all_concept_patterns = [defs["pattern"] for defs in CONCEPT_DEFS.values()]

    # Build signal-filtered tweets grouped by month
    monthly_new = {}
    for tweet in tweets:
        tweet_id = str(tweet["id"])
        created_at = tweet["created_at"]
        month_key = created_at[:7]

        text_lower = tweet["text"].lower()
        has_ticker = any(re.search(pat, text_lower) for pat in all_ticker_patterns)
        has_concept = any(re.search(pat, text_lower) for pat in all_concept_patterns)

        is_high_signal = (
            len(tweet["text"]) >= 100
            and (has_ticker or has_concept)
            and tweet.get("favorite_count", 0) > 50
        )
        is_manually_curated = tweet_id in trans_cache

        if is_high_signal or is_manually_curated:
            if month_key not in monthly_new:
                monthly_new[month_key] = []
            monthly_new[month_key].append(tweet)

    for month, m_tweets in monthly_new.items():
        filepath = MONTHLY_DIR / f"{month}.md"
        m_tweets.sort(key=lambda t: t["created_at"], reverse=True)

        if full_rebuild or not filepath.is_file():
            log(f"  Monthly [{month}]: full rebuild with {len(m_tweets)} tweets.")
            _write_monthly_full(month, m_tweets, trans_cache, filepath)
            continue

        # Incremental
        existing_ids = extract_tweet_ids_from_md(filepath)
        new_tweets = [t for t in m_tweets if t["id"] not in existing_ids]

        if not new_tweets:
            log(f"  Monthly [{month}]: no new tweets, skipping.")
            continue

        log(f"  Monthly [{month}]: {len(new_tweets)} new tweets to prepend "
            f"(had {len(existing_ids)} existing).")

        # Read old file, extract prefix before first tweet entry
        with open(filepath, "r", encoding="utf-8") as f:
            old_content = f.read()

        # Find the first ### tweet heading to split prefix from entries
        first_entry = old_content.find("\n### 📅 ")
        if first_entry == -1:
            _write_monthly_full(month, m_tweets, trans_cache, filepath)
            continue

        prefix = old_content[:first_entry]

        # Deduplicate and sort all tweets for this month
        all_month_tweets = {}
        # Parse existing tweets from the old file to include them
        for tid in existing_ids:
            # Find the tweet in the new data if available, otherwise skip
            for t in m_tweets:
                if t["id"] == tid:
                    all_month_tweets[tid] = t
                    break
        for t in new_tweets:
            all_month_tweets[t["id"]] = t

        sorted_tweets = sorted(all_month_tweets.values(),
                               key=lambda t: t["created_at"], reverse=True)

        # Rebuild entries
        entries = []
        for tweet in sorted_tweets:
            tweet_id = str(tweet["id"])
            created_at = tweet["created_at"]
            dt_display = created_at.replace("T", " ")[:16]
            cleaned_eng = clean_text(tweet["text"]).replace("\n", "\n> ")
            fav = tweet.get("favorite_count", 0)
            rt = tweet.get("retweet_count", 0)

            entries.append(f"\n### 📅 {dt_display} ([X.com Post](https://x.com/aleabitoreddit/status/{tweet_id}))")
            entries.append("")
            entries.append(f"> **Original (ENG)**")
            entries.append(f"> {cleaned_eng}")
            entries.append("")

            if tweet_id in trans_cache:
                zh_val = trans_cache[tweet_id]["zh"].replace("\n", "\n> ")
                entries.append(f"> ★ **中文精选对照 (Bilingual)**")
                entries.append(f"> {zh_val}")
            else:
                entries.append(
                    f"> 💡 *此推文尚未翻译。您可以在 Claude 中输入 "
                    f"`翻译并归档推文 {tweet_id}` 强制一键获取中英对照并自动归档！*"
                )

            entries.append("")
            entries.append(f"*互动指标：❤️ {fav} | 🔁 {rt}*")
            entries.append("")
            entries.append("---")

        # Update header count
        prefix_lines = prefix.split("\n")
        updated_prefix_lines = []
        for line in prefix_lines:
            if "**Total Curated Tweets**" in line:
                updated_prefix_lines.append(
                    f"> **Total Curated Tweets**: `{len(sorted_tweets)}` | "
                    f"*Noise filtered out: celebrate posts, war comments, short replies.*"
                )
            else:
                updated_prefix_lines.append(line)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(updated_prefix_lines))
            f.write("\n".join(entries))


def _write_monthly_full(month: str, m_tweets: list, trans_cache: dict, filepath: Path):
    """Full rebuild of a single monthly archive file."""
    m_tweets.sort(key=lambda t: t["created_at"], reverse=True)

    m_content = []
    m_content.append(f"# 📅 Monthly Archive: {month}")
    m_content.append("")
    m_content.append(
        f"This is the curated, high-signal investment timeline of Serenity "
        f"for the month of **{month}**."
    )
    m_content.append("")
    m_content.append("> [!NOTE]")
    m_content.append(
        f"> **Total Curated Tweets**: `{len(m_tweets)}` | "
        f"*Noise filtered out: celebrate posts, war comments, short replies.*"
    )
    m_content.append("")

    for tweet in m_tweets:
        tweet_id = str(tweet["id"])
        created_at = tweet["created_at"]
        dt_display = created_at.replace("T", " ")[:16]
        cleaned_eng = clean_text(tweet["text"]).replace("\n", "\n> ")
        fav = tweet.get("favorite_count", 0)
        rt = tweet.get("retweet_count", 0)

        m_content.append(f"### 📅 {dt_display} ([X.com Post](https://x.com/aleabitoreddit/status/{tweet_id}))")
        m_content.append("")
        m_content.append(f"> **Original (ENG)**")
        m_content.append(f"> {cleaned_eng}")
        m_content.append("")

        if tweet_id in trans_cache:
            zh_val = trans_cache[tweet_id]["zh"].replace("\n", "\n> ")
            m_content.append(f"> ★ **中文精选对照 (Bilingual)**")
            m_content.append(f"> {zh_val}")
        else:
            m_content.append(
                f"> 💡 *此推文尚未翻译。您可以在 Claude 中输入 "
                f"`翻译并归档推文 {tweet_id}` 强制一键获取中英对照并自动归档！*"
            )

        m_content.append("")
        m_content.append(f"*互动指标：❤️ {fav} | 🔁 {rt}*")
        m_content.append("")
        m_content.append("---")
        m_content.append("")

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write("\n".join(m_content))


def compile_index(tweets: list, monthly_tweets: dict):
    """Always fully regenerate index.md (lightweight metadata page)."""
    reports = sorted(list(REPORTS_DIR.glob("*.md")), reverse=True)
    months = sorted(list(monthly_tweets.keys()), reverse=True)

    index_content = []
    index_content.append("# 🧭 Personal Investment Knowledge Base (Wiki Home)")
    index_content.append("")
    index_content.append(
        "Welcome to your personal investment research portal compiled by your AI agent "
        "based on historical expert timelines and research sessions."
    )
    index_content.append("")
    index_content.append(
        f"> [!TIP]\n> **Last Sync Date**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"> **Total Tweets Scraped**: `{len(tweets)}` since `2025-01-01`"
    )
    index_content.append("")

    if months:
        index_content.append("## 📅 Monthly Archives (中英对照月份时间线)")
        month_links = [f"[[{m}]]" for m in months]
        index_content.append(" | ".join(month_links))
        index_content.append("")

    index_content.append("## 📈 Core Stock Tickers")
    index_content.append(
        "| Ticker | Company Name | Primary Sub-Sector | Industrial Role |"
    )
    index_content.append(
        "| :--- | :--- | :--- | :--- |"
    )
    for tk, defs in TICKER_DEFS.items():
        index_content.append(
            f"| **[[{tk}]]** | {defs['name']} | `{defs['sector']}` | {defs['role']} |"
        )
    index_content.append("")

    index_content.append("## 🧪 Advanced Semiconductor & AI Concepts")
    for cp, defs in CONCEPT_DEFS.items():
        index_content.append(
            f"*   **[[{cp}]]** — *{defs['name']}*: {defs['summary']}"
        )
    index_content.append("")

    index_content.append("## 📂 Filed Research Reports & Q&A")
    if reports:
        for rep in reports:
            rel_path = f"reports/{rep.name}"
            display_name = rep.stem.replace("-", " ")
            index_content.append(
                f"*   [{display_name}]({rel_path}) — "
                f"*Filed on {datetime.fromtimestamp(rep.stat().st_mtime).strftime('%Y-%m-%d')}*"
            )
    else:
        index_content.append(
            "> No reports filed yet. Ask your agent to write a report to compile "
            "a new research archive!"
        )

    index_content.append("")
    index_content.append("---")
    index_content.append(
        "*Note: This Personal Wiki is 100% auto-compiled by the AI agent and designed "
        "to be opened as an Obsidian Vault folder for optimal visual graph networks.*"
    )

    with open(INDEX_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(index_content))


def compile_wiki():
    full_rebuild = "--full" in sys.argv
    mode_str = "FULL REBUILD" if full_rebuild else "INCREMENTAL"
    log(f"Starting wiki compilation ({mode_str})...")

    # Create directories
    WIKI_ROOT.mkdir(exist_ok=True)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONCEPTS_DIR.mkdir(exist_ok=True)
    TICKERS_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    MONTHLY_DIR.mkdir(exist_ok=True)

    if not RAW_PATH.is_file():
        log(f"Raw tweets file not found at {RAW_PATH}. Please run the scraper first.")
        sys.exit(1)

    # 1. Load data
    with open(RAW_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    tweets = data.get("tweets", [])
    log(f"Loaded {len(tweets)} tweets to classify.")

    # Load translation cache
    trans_cache = {}
    if CACHE_PATH.is_file():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as cfh:
                trans_cache = json.load(cfh)
            log(f"Loaded {len(trans_cache)} cached translations.")
        except Exception as exc:
            log(f"Failed to read translations cache: {exc}")

    # 2. Classify tweets to tickers and concepts
    ticker_tweets = {t: [] for t in TICKER_DEFS}
    concept_tweets = {c: [] for c in CONCEPT_DEFS}

    for tweet in tweets:
        text_lower = tweet["text"].lower()

        for tk, defs in TICKER_DEFS.items():
            if re.search(defs["pattern"], text_lower):
                ticker_tweets[tk].append(tweet)

        for cp, defs in CONCEPT_DEFS.items():
            if re.search(defs["pattern"], text_lower):
                concept_tweets[cp].append(tweet)

    # 3. Compile Tickers
    compile_tickers(ticker_tweets, trans_cache, full_rebuild)

    # 4. Compile Concepts
    compile_concepts(concept_tweets, trans_cache, full_rebuild)

    # 5. Compile Monthly Archives
    compile_monthly(tweets, trans_cache, full_rebuild)

    # 6. Generate index.md (always full rebuild)
    log("Generating index.md...")
    compile_index(tweets, {
        m: [] for m in set(t["created_at"][:7] for t in tweets)
    })

    log("Wiki compilation successfully complete ✓")


if __name__ == "__main__":
    compile_wiki()
