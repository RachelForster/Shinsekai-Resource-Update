from __future__ import annotations

import csv
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "characters"
JSON_FILE = ROOT / "characters.json"
URL_RE = re.compile(r"https?://\S+")

FIELD_NAMES = {
    "name": ["1.人物名", "人物名", "name"],
    "url": ["2.下载链接", "下载链接", "url"],
    "uploader": ["3.作者", "作者", "uploader"],
    "end_time": ["结束答题时间", "end_time", "结束时间"],
}


def normalize_text(text: Optional[str]) -> str:
    return text.strip() if text else ""


def extract_url(link_text: str) -> str:
    if not link_text:
        return ""
    match = URL_RE.search(link_text)
    if match:
        return match.group(0)
    return link_text.strip()


def parse_time(value: str) -> str:
    value = normalize_text(value)
    if not value:
        return date.today().isoformat()
    try:
        dt = datetime.strptime(value, "%d-%b-%Y %H:%M:%S")
        return dt.date().isoformat()
    except ValueError:
        try:
            dt = datetime.fromisoformat(value)
            return dt.date().isoformat()
        except ValueError:
            return date.today().isoformat()


def get_field(row: Dict[str, str], keys: List[str]) -> str:
    for key in keys:
        if key in row and row[key].strip():
            return row[key].strip()
    for value in row.values():
        if any(key in value for key in keys):
            return value.strip()
    return ""


def read_existing_entries() -> List[Dict[str, Any]]:
    if not JSON_FILE.exists():
        return []
    with JSON_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(entries: List[Dict[str, Any]]) -> None:
    with JSON_FILE.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=4)
        f.write("\n")


def parse_csv_file(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader if any(value.strip() for value in row.values())]


def parse_rows(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    parsed = []
    for row in rows:
        name = normalize_text(get_field(row, FIELD_NAMES["name"]))
        url_raw = get_field(row, FIELD_NAMES["url"]) or ""
        author = normalize_text(get_field(row, FIELD_NAMES["uploader"]))
        end_time = parse_time(get_field(row, FIELD_NAMES["end_time"]))

        if not name or not url_raw:
            continue

        url = extract_url(url_raw)
        if not url:
            continue

        parsed.append(
            {
                "name": name,
                "url": url,
                "uploader": author,
                "time": end_time,
            }
        )
    return parsed


def merge_entries(existing: List[Dict[str, Any]], new_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for entry in existing:
        key = (normalize_text(entry.get("name", "")), normalize_text(entry.get("url", "")))
        merged[key] = entry

    for entry in new_entries:
        key = (entry["name"], entry["url"])
        if key in merged:
            existing_entry = merged[key]
            if not existing_entry.get("uploader") and entry.get("uploader"):
                existing_entry["uploader"] = entry["uploader"]
            if not existing_entry.get("time") and entry.get("time"):
                existing_entry["time"] = entry["time"]
        else:
            merged[key] = entry

    return list(merged.values())


def main() -> None:
    if not DATA_DIR.exists() or not DATA_DIR.is_dir():
        raise SystemExit(f"Missing directory: {DATA_DIR}")

    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found in {DATA_DIR}")

    all_rows: List[Dict[str, str]] = []
    for csv_path in csv_files:
        all_rows.extend(parse_csv_file(csv_path))

    parsed_entries = parse_rows(all_rows)
    existing_entries = read_existing_entries()
    merged_entries = merge_entries(existing_entries, parsed_entries)
    write_json(merged_entries)
    print(f"Updated {JSON_FILE} with {len(parsed_entries)} parsed entries and {len(merged_entries)} total unique records.")


if __name__ == "__main__":
    main()
