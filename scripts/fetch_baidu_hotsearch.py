"""Fetch Baidu Hot Search board and save results as JSON files.

This script scrapes the Baidu realtime hot search board and stores
structured information for downstream processing. The script is intended
for scheduled execution inside a GitHub Actions workflow.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup


# URL that hosts the realtime hot search board.
HOT_SEARCH_URL = "https://top.baidu.com/board?tab=realtime"
# Directory inside the repository where we persist scraped data.
DATA_DIR = Path("data")


@dataclass
class HotSearchItem:
    """Represents a single hot search entry returned by Baidu."""

    rank: int
    title: str
    summary: str
    hot_score: str
    detail_url: str


def fetch_hot_search_html(url: str = HOT_SEARCH_URL) -> str:
    """Retrieve the HTML page that contains the hot search board.

    Parameters
    ----------
    url: str
        The URL to request. Defaults to ``HOT_SEARCH_URL``.

    Returns
    -------
    str
        Raw HTML content of the page.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.text


def parse_hot_search(html: str) -> List[HotSearchItem]:
    """Parse the realtime hot search page.

    The HTML structure contains multiple ``div`` blocks with the class
    ``category-wrap"". Each block corresponds to a ranked hot search entry.
    """

    soup = BeautifulSoup(html, "html.parser")
    items: List[HotSearchItem] = []

    for card in soup.select("div.category-wrap_iQLoo"):
        try:
            rank = int(card.select_one("div.index_1Ew5p").text.strip())
        except (AttributeError, ValueError):
            # Skip malformed cards that do not contain the expected rank.
            continue

        title_tag = card.select_one("div.c-single-text-ellipsis")
        summary_tag = card.select_one("div.hot-desc_1m_jR")
        hot_score_tag = card.select_one("div.hot-index_1Bl1a")
        detail_link_tag = card.select_one("a.c-single-text-ellipsis")

        item = HotSearchItem(
            rank=rank,
            title=title_tag.text.strip() if title_tag else "",
            summary=(summary_tag.text.strip() if summary_tag else ""),
            hot_score=hot_score_tag.text.strip() if hot_score_tag else "",
            detail_url=(
                detail_link_tag["href"].strip()
                if detail_link_tag and detail_link_tag.has_attr("href")
                else ""
            ),
        )
        items.append(item)

    # Ensure the list is sorted by rank because the DOM order might not
    # be reliable when ads or other content are injected.
    items.sort(key=lambda item: item.rank)
    return items


def save_results(items: List[HotSearchItem]) -> Path:
    """Persist the parsed items to a date-based JSON file.

    The function writes two files:

    * ``data/baidu-hotsearch-YYYYMMDD.json``: a snapshot for the day.
    * ``data/latest.json``: the latest snapshot for convenience.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone(timedelta(hours=8)))
    payload = {
        "generated_at": timestamp.isoformat(),
        "items": [asdict(item) for item in items],
    }

    date_suffix = timestamp.strftime("%Y%m%d")
    daily_path = DATA_DIR / f"baidu-hotsearch-{date_suffix}.json"
    latest_path = DATA_DIR / "latest.json"

    with daily_path.open("w", encoding="utf-8") as daily_file:
        json.dump(payload, daily_file, ensure_ascii=False, indent=2)

    with latest_path.open("w", encoding="utf-8") as latest_file:
        json.dump(payload, latest_file, ensure_ascii=False, indent=2)

    return daily_path


def main() -> int:
    """Entry point used by GitHub Actions and manual runs."""

    try:
        html = fetch_hot_search_html()
        items = parse_hot_search(html)
        if not items:
            print("No hot search items were found.", file=sys.stderr)
            return 1

        daily_file = save_results(items)
        print(f"Saved {len(items)} hot search items to {daily_file}")
        return 0
    except Exception as exc:  # pragma: no cover - defensive guard for CI
        print(f"Error while fetching Baidu hot search: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
