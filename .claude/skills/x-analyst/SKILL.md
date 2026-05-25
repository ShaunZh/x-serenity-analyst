---
name: x-analyst
description: >
  Deep-dive X.com analyst — scrapes a user's tweet history (2025-present) incrementally,
  compiles an Obsidian-style Investment Knowledge Base (wiki/), and archives
  all analysis/reports locally so they persistently grow.
dependencies:
  - twscrape
  - python3 (>= 3.10)
---

# X-Analyst Skill

## When to Activate

Trigger this skill whenever the user's message matches any of the following
patterns (case-insensitive):

- `分析 X 用户 @<username>`
- `analyze X user @<username>`
- `scrape @<username>`
- `翻译并归档推文 <ID1>, <ID2>...`
- `translate and curate tweets <ID1>, <ID2>...`
- Any request that mentions analysing an X/Twitter account's posts, querying the Personal Wiki, or translating/curating specific tweet IDs.

## Execution Steps

### A. If the request is for targeted translation (`翻译并归档推文 <ID1>, <ID2>...`):
1. Load `wiki/raw/tweets_aleabitoreddit.json` and locate the tweets with the specified IDs.
2. Provide high-quality professional financial and semi-conductor bilingual translations for the target tweets.
3. Update `wiki/raw/translations_cache.json` by adding the translated content matching each ID (format: `{"<ID>": {"zh": "<Translation>", "translated_at": "<Timestamp>"}}`). Save the file.
4. Execute the compilation script:
   ```bash
   .venv/bin/python3 .claude/skills/x-analyst/compile_wiki.py
   ```
5. Present the high-fidelity translation directly to the user in a stunning layout and remind them that this tweet is now permanent in their monthly timeline with double links!

### B. Standard Scrape Workflow:
1. **Run the Scraper (Incremental Sync)**:
   Execute the following command in the terminal **in the background**:
   ```bash
   .venv/bin/python3 .claude/skills/x-analyst/scraper.py \
     --username <USERNAME> \
     --cookie-path x_cookies.json \
     --output-path wiki/raw/tweets_<USERNAME>.json
   ```
   Wait for the script to finish successfully.
2. **Compile the Knowledge Base (Wiki Compilation)**:
   Execute the compilation script to update the Obsidian-style Investment Wiki:
   ```bash
   .venv/bin/python3 .claude/skills/x-analyst/compile_wiki.py
   ```
3. **Analysis & Automatic Report Filing (Filing)**:

When answering the user's query or generating a research report:
1. Read the updated files in `wiki/concepts/` and `wiki/tickers/` to capture the most precise historical contexts.
2. Produce a publication-grade semiconductor and financial supply chain analysis according to the four pillars (Bottlenecks, Tickers & Supply Chain, Thesis Evolution, Risk Matrix).
3. **CRITICAL REQUIREMENT (Filing)**: Automatically save your generated research report or Q&A interaction as a local Markdown file under the `wiki/reports/` directory with the filename format:
   `wiki/reports/Report-<YYYY-MM-DD>-<Topic>.md`
   *(Replace `<YYYY-MM-DD>` with today's date, and `<Topic>` with a short snake_case description of the query).*
4. Run `.venv/bin/python3 .claude/skills/x-analyst/compile_wiki.py` again to register and index the newly filed report in `wiki/index.md`'s **Filed Research Reports** section!
5. Present the final report directly to the user in a well-structured Markdown response, pointing them to the persistent local Wiki file they can view in their browser or Obsidian.

---

## Analysis Framework (The Four Pillars)

Using the compiled wiki pages and raw JSON as input, analyze according to these dimensions:

### Pillar I — Unknown Structural Bottlenecks（未知的结构性瓶颈）
Identify and elaborate on structural, physics-level, or capacity-level bottlenecks in niche semiconductor segments (e.g. CPO, Silicon Photonics modulators/foundries, Glass Substrates drilling, InP compound substrate capacity constraints). Detail severity and expected resolution timelines.

### Pillar II — Ticker & Supply Chain Mapping（标的与供应链图谱）
Map all tickers (e.g. `$SIVE`, `$AXTI`, `$LPK`, `$SOI`, `$IQE`, `$AAOI`, `$JBL`, `$NBIS`, `$FOCI`, `$AEVA`) into their ecological position (upstream materials, midstream IP, downstream module integration). Provide a Mermaid supply-chain relationship diagram.

### Pillar III — Thesis Evolution（逻辑主线演变）
Track how the core narrative has evolved chronologically from early 2025 to the present day, noting contradictions, logic reversals, or key trigger events (earnings, policy shifts, M&A).

### Pillar IV — Risk & Liquidity Matrix（风险与流动性矩阵）
Separate risks into Technology Obsolescence, Capacity Execution, Float/Liquidity (e.g. small-cap short squeeze potentials, ETF passive inflows), and Geopolitical Decoupling.

---

## Notes

- The cookie file (`x_cookies.json`) must be present in the project root. If missing or expired, instruct the user to re-export cookies in JSON format from their browser.

### How to Export X.com Cookies
1. Install the browser extension **"Get cookies.txt LOCALLY"** (Chrome) or similar cookie manager.
2. Log in to [x.com](https://x.com).
3. Export cookies for `x.com` in **JSON format**.
4. Save the file as `x_cookies.json` in the project root directory.
5. Run the skill: `分析 X 用户 @aleabitoreddit`
