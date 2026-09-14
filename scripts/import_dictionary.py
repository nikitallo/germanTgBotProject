#!/usr/bin/env python3
"""Import a word list from a web page into data/dictionary.json.

Targets Blogspot-style pages (div.post-body.entry-content) where each line
is "term - translation" separated by <br> tags. Safe to rerun: already
imported entries are never duplicated or removed, so the same script can
later import a different language (--lang en) into the same file.
"""
import argparse
import html
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "data" / "dictionary.json"

# Non-greedy capture of the term (at most 60 chars) up to the first " - ",
# the rest is the translation. This keeps long non-vocabulary paragraphs out
# of the dictionary even if they happen to contain " - " further in.
ENTRY_RE = re.compile(r"^(.{1,60}?)\s-\s(.+)$")
BRACKET_RE = re.compile(r"\s*\[[^\]]*\]")


def fetch_lines(url: str) -> list[str]:
    response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    content = soup.select_one("div.post-body.entry-content")
    if content is None:
        raise SystemExit("Could not find div.post-body.entry-content on the page")

    for br in content.find_all("br"):
        br.replace_with("\n")

    text = html.unescape(content.get_text())
    return text.split("\n")


def parse_entries(lines: list[str], lang: str, source: str) -> list[dict]:
    seen = set()
    entries = []
    for raw_line in lines:
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue

        match = ENTRY_RE.match(line)
        if not match:
            continue

        term = BRACKET_RE.sub("", match.group(1)).strip()
        translation = match.group(2).strip()
        if not term or not translation:
            continue

        key = (term, translation)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"lang": lang, "term": term, "translation": translation, "source": source})

    return entries


def merge(existing: list[dict], new_entries: list[dict], lang: str) -> tuple[list[dict], int]:
    existing_keys = {(e["lang"], e["term"], e["translation"]) for e in existing}
    next_index = 1 + sum(1 for e in existing if e["id"].startswith(f"{lang}-"))

    added = 0
    for entry in new_entries:
        key = (entry["lang"], entry["term"], entry["translation"])
        if key in existing_keys:
            continue
        entry["id"] = f"{lang}-{next_index:04d}"
        next_index += 1
        existing.append(entry)
        existing_keys.add(key)
        added += 1

    return existing, added


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="URL of the page with the word list")
    parser.add_argument("--lang", default="de", help="Language code for the new entries (default: de)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to dictionary.json")
    args = parser.parse_args()

    lines = fetch_lines(args.url)
    new_entries = parse_entries(lines, args.lang, args.url)
    if not new_entries:
        raise SystemExit("Could not parse any entries from the page")

    existing: list[dict] = []
    if args.output.exists():
        with args.output.open("r", encoding="utf-8") as f:
            existing = json.load(f)

    merged, added = merge(existing, new_entries, args.lang)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"Entries parsed from the page: {len(new_entries)}")
    print(f"New entries added: {added}")
    print(f"Total entries in dictionary: {len(merged)}")


if __name__ == "__main__":
    main()
