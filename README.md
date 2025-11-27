# Ghost Scraper Empire 🌑

> *Shadows don't bloat. They hunt.*

A raw, async-first Reddit scraper designed for quant traders and data hoarders. Pulls top posts from multiple subreddits simultaneously, runs vectorized sentiment analysis (Bull/Bear/Neutral), checks for Web3 signals (stubbed), and buries the loot in a local SQLite vault.

## ⚡ Features

*   **Async Swarm**: Uses `aiohttp` + `asyncio` semaphores to hit multiple subs without blocking.
*   **Ghost Mode**: Rotating User-Agents and randomized sleep intervals to dodge 429s.
*   **Quant Refinery**: `Pandas` vector operations to flag titles with sentiment scores (-1.0 to 1.0).
*   **Web3 Hooks**: Stubbed Alchemy API integration to merge on-chain gas/volume data with social sentiment.
*   **The Vault**: SQLite storage with hashed IDs to prevent dupes. Indexed for instant SQL queries.
*   **Zero Fluff**: Single-file architecture. No config files. CLI driven.

## 🛠️ Arsenal

*   Python 3.8+
*   `aiohttp`
*   `pandas`

## 💀 Usage

### The Hunt
Scrape subs, analyze sentiment, and save to DB/CSV.

```bash
python3 ghost_scraper_empire.py hunt --subs python,quant,ethereum --depth 20 --ghost 2 --quant --web3
```

*   `--subs`: Comma-separated list of subreddits.
*   `--depth`: How many posts to dig per sub.
*   `--ghost`: Sleep factor (1-5) to avoid detection.
*   `--quant`: Enable sentiment scoring.
*   `--web3`: Enable Web3 data merging.

### The Interrogation
Query your local `shadow_vault.db` directly from the CLI.

```bash
python3 ghost_scraper_empire.py query "SELECT sub, title, sentiment_score FROM posts WHERE sentiment_score > 0.5"
```

### The Easter Egg
Set depth to `42`. The universe might whisper back.

## 📂 Output

*   **shadow_vault.db**: The persistent SQLite database.
*   **empire_feed.csv**: Appended raw feed for your backtesting rigs.

---
*Built in the shadows. Run at your own risk.*
