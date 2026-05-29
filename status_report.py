#!/usr/bin/env python3
"""
PSP Video Archive Status Report
Generates a human-readable overview of events and their transcription status.

Usage:
    python3 status_report.py                         # output to screen
    python3 status_report.py --summary               # add summary status column
    python3 status_report.py --csv status.csv        # also save to CSV
    python3 status_report.py --csv-only status.csv   # CSV only, no screen output
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


def load_metadata(path: Path = Path("metadata.json")) -> dict:
    """Load metadata.json."""
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_event(event: dict) -> dict:
    """Analyze transcription status for a single event."""
    all_files = [
        f for sub in event["subevents"].values()
        for f in sub.get("files", [])
    ]
    
    if not all_files:
        return {
            "total_files": 0,
            "downloaded": 0,
            "transcribed": 0,
            "download_pct": 0,
            "transcription_pct": 0,
            "status": event.get("status", "unknown"),
        }
    
    downloaded = sum(1 for f in all_files if f.get("downloaded_at"))
    # Count files that have ANY transcription (captions OR our transcription)
    # This matches the logic in sync.py's file_has_transcription()
    transcribed = sum(
        1 for f in all_files
        if f.get("captions_downloaded_at") or f.get("transcription_done_at")
    )
    total = len(all_files)
    
    return {
        "total_files": total,
        "downloaded": downloaded,
        "transcribed": transcribed,
        "download_pct": round(100 * downloaded / total) if total else 0,
        "transcription_pct": round(100 * transcribed / total) if total else 0,
        "status": event.get("status", "unknown"),
    }


def format_date(ts: str | None) -> str:
    """Format timestamp to readable date."""
    if not ts:
        return "—"
    return ts[:10] if len(ts) >= 10 else ts


def summary_status(ev: dict) -> tuple[str, str, str]:
    """Return (symbol, model, schema_version) for the summary column."""
    # Fast path: metadata is up to date
    local = ev.get("summary_local", "")
    if ev.get("summary_done_at") and local and Path(local).exists():
        return "✓", ev.get("summary_model", "?"), ev.get("summary_schema_version", "?")
    # Fallback: scan summaries/json/ by event ID (handles metadata-not-written case)
    matches = sorted(Path("summaries/json").glob(f"summary_{ev['id']}_*.json")) if Path("summaries/json").exists() else []
    if matches:
        try:
            data = json.loads(matches[-1].read_text(encoding="utf-8"))
            return "✓", data.get("model_hint", "?"), data.get("schema_version", "?")
        except Exception:
            return "✓", "?", "?"
    return "—", "", ""


def print_report(meta: dict, show_summary: bool = False) -> list[dict]:
    """Print human-readable report to screen and return data for CSV."""
    events = meta["events"]
    last_sync = meta.get("last_sync", "unknown")

    width = 118 if show_summary else 100
    print(f"\n{'='*width}")
    print(f"PSP Video Archive - Status Report")
    print(f"Last sync: {last_sync}  |  Total events: {len(events)}")
    print(f"{'='*width}\n")

    if show_summary:
        print(f"{'ID':>6}  {'Date':10}  {'Status':12}  {'Files':>5}  {'Down':>5}  {'Trans':>5}  {'Summ':>4}  {'Model':<26}  {'Category':18}  Name")
        print("-" * width)
    else:
        print(f"{'ID':>6}  {'Date':10}  {'Status':12}  {'Files':>5}  {'Down':>5}  {'Trans':>5}  {'Category':20}  Name")
        print("-" * width)

    sorted_events = sorted(events.values(), key=lambda e: e.get("ts") or "")
    csv_data = []

    for ev in sorted_events:
        stats = analyze_event(ev)
        event_id = ev["id"]
        date = format_date(ev.get("ts"))
        status = stats["status"]
        category = (ev.get("category") or "")[:20]
        name = (ev.get("name") or "Unnamed")[:55]

        files_str = "—" if stats["total_files"] == 0 else str(stats["total_files"])
        down_str  = "—" if stats["total_files"] == 0 else f"{stats['download_pct']}%"
        trans_str = "—" if stats["total_files"] == 0 else f"{stats['transcription_pct']}%"

        row = {
            "event_id": event_id, "date": date, "status": status,
            "category": ev.get("category", ""), "name": ev.get("name", ""),
            "total_files": stats["total_files"],
            "files_downloaded": stats["downloaded"],
            "files_transcribed": stats["transcribed"],
            "download_pct": stats["download_pct"],
            "transcription_pct": stats["transcription_pct"],
            "total_start": ev.get("total_start", ""),
            "total_stop": ev.get("total_stop", ""),
        }

        if show_summary:
            summ, model_s, schema_s = summary_status(ev)
            print(f"{event_id:>6}  {date:10}  {status:12}  {files_str:>5}  {down_str:>5}  {trans_str:>5}  {summ:>4}  {model_s:<26}  {category:18}  {name}")
            row.update({"summary": summ, "summary_model": model_s, "summary_schema_version": schema_s,
                        "summary_done_at": ev.get("summary_done_at", "")})
        else:
            print(f"{event_id:>6}  {date:10}  {status:12}  {files_str:>5}  {down_str:>5}  {trans_str:>5}  {category:20}  {name}")

        csv_data.append(row)

    print("-" * width)

    total_events = len(events)
    by_status: dict[str, int] = {}
    for ev in events.values():
        s = ev.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    print(f"\nSummary by status:")
    for s in sorted(by_status):
        count = by_status[s]
        pct = round(100 * count / total_events) if total_events else 0
        print(f"  {s:12}: {count:3} ({pct:2}%)")

    if show_summary:
        summarized = sum(1 for ev in events.values() if summary_status(ev)[0] == "✓")
        print(f"\nSummarized: {summarized}/{total_events}")

    print()
    return csv_data


def save_csv(data: list[dict], path: Path) -> None:
    """Save data to CSV file."""
    if not data:
        print(f"No data to save to {path}", file=sys.stderr)
        return
    
    fieldnames = [
        "event_id", "date", "status", "category", "name",
        "total_files", "files_downloaded", "files_transcribed",
        "download_pct", "transcription_pct",
        "total_start", "total_stop",
        "summary", "summary_model", "summary_schema_version", "summary_done_at",
    ]
    # Only write fields that exist in the data rows
    fieldnames = [f for f in fieldnames if any(f in row for row in data)]
    
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"CSV saved to: {path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate transcription status report from metadata.json"
    )
    parser.add_argument(
        "--csv",
        metavar="FILE",
        help="Save report to CSV file (in addition to screen output)"
    )
    parser.add_argument(
        "--csv-only",
        metavar="FILE",
        help="Save to CSV only, skip screen output"
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Add summary status column (model, schema version)"
    )
    parser.add_argument(
        "--metadata", default="metadata.json",
        help="Path to metadata.json (default: metadata.json)"
    )

    args = parser.parse_args()
    meta = load_metadata(Path(args.metadata))

    if args.csv_only:
        csv_data = print_report(meta, show_summary=args.summary) if False else []
        for ev in meta["events"].values():
            stats = analyze_event(ev)
            row = {
                "event_id": ev["id"], "date": format_date(ev.get("ts")),
                "status": stats["status"], "category": ev.get("category", ""),
                "name": ev.get("name", ""),
                "total_files": stats["total_files"],
                "files_downloaded": stats["downloaded"],
                "files_transcribed": stats["transcribed"],
                "download_pct": stats["download_pct"],
                "transcription_pct": stats["transcription_pct"],
                "total_start": ev.get("total_start", ""),
                "total_stop": ev.get("total_stop", ""),
            }
            if args.summary:
                summ, model_s, schema_s = summary_status(ev)
                row.update({"summary": summ, "summary_model": model_s,
                            "summary_schema_version": schema_s,
                            "summary_done_at": ev.get("summary_done_at", "")})
            csv_data.append(row)
        save_csv(csv_data, Path(args.csv_only))
    else:
        csv_data = print_report(meta, show_summary=args.summary)
        if args.csv:
            save_csv(csv_data, Path(args.csv))


if __name__ == "__main__":
    main()
