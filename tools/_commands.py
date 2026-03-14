"""
_commands.py — Subcommand implementations: analyze, sort, organize, search.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from _helpers import (
    REPO_ROOT,
    _all_assets,
    _all_notes,
    _asset_meta,
    _parse_note,
    _relative,
    pending_inbox_files,
)


# ---------------------------------------------------------------------------
# Subcommand: analyze
# ---------------------------------------------------------------------------


def cmd_analyze(args: argparse.Namespace) -> None:
    """Print a detailed analysis of one note or all notes."""
    if args.file:
        target = Path(args.file)
        if not target.is_absolute():
            target = REPO_ROOT / target
        if not target.exists():
            sys.exit(f"File not found: {args.file}")
        notes = [target]
    else:
        notes = _all_notes()

    for path in notes:
        meta = _parse_note(path)
        print(f"\n{'='*60}")
        print(f"  📄 {meta['relative']}")
        print("=" * 60)
        print(f"  Title    : {meta['title']}")
        print(f"  Folder   : {meta['folder']}")
        print(f"  Words    : {meta['words']}")
        print(f"  Modified : {meta['modified'].strftime('%Y-%m-%d %H:%M')}")
        if meta["headings"]:
            print("  Headings :")
            for level, heading in meta["headings"]:
                print(f"    {'  ' * (level - 1)}{'#' * level} {heading}")
        if meta["open_items"]:
            print(f"  Open action items ({len(meta['open_items'])}):")
            for item in meta["open_items"][:5]:
                print(f"    {item}")
            if len(meta["open_items"]) > 5:
                print(f"    … and {len(meta['open_items']) - 5} more")
        if meta["done_items"]:
            print(
                f"  Completed items : {len(meta['done_items'])}"
            )
        if meta["dates_in_text"]:
            print(f"  Dates found  : {', '.join(meta['dates_in_text'])}")
    print()


# ---------------------------------------------------------------------------
# Subcommand: sort
# ---------------------------------------------------------------------------


def cmd_sort(args: argparse.Namespace) -> None:
    """List notes sorted by the chosen criterion."""

    # Assets are handled separately: all file types, file-size instead of words
    if args.folder == "assets":
        assets_meta = [_asset_meta(p) for p in _all_assets()]
        if not assets_meta:
            print("\nNo files found in assets/.\n")
            return

        by = args.by
        if by == "date":
            assets_meta.sort(key=lambda m: m["modified"], reverse=True)
            col_header = "Modified"
            col_fn = lambda m: m["modified"].strftime("%Y-%m-%d %H:%M")
        elif by == "size":
            assets_meta.sort(key=lambda m: m["size_bytes"], reverse=True)
            col_header = "Size"
            col_fn = lambda m: m["size_display"]
        else:  # name
            assets_meta.sort(key=lambda m: m["relative"])
            col_header = "Type"
            col_fn = lambda m: m["kind"]

        col_w = max(len(col_fn(m)) for m in assets_meta) if assets_meta else 10
        col_w = max(col_w, len(col_header))
        path_w = max(len(m["relative"]) for m in assets_meta) if assets_meta else 20

        header = f"{'Path':<{path_w}}  {col_header:<{col_w}}"
        print(f"\n{header}")
        print("-" * len(header))
        for m in assets_meta:
            print(f"{m['relative']:<{path_w}}  {col_fn(m):<{col_w}}")
        print(f"\n{len(assets_meta)} asset(s) found.\n")
        return

    notes_meta = [_parse_note(p) for p in _all_notes()]

    if args.folder:
        notes_meta = [m for m in notes_meta if m["folder"] == args.folder]
        if not notes_meta:
            sys.exit(
                f"No notes found in folder '{args.folder}'. "
                f"Available folders: {sorted({m['folder'] for m in [_parse_note(p) for p in _all_notes()]})}"
            )

    by = args.by
    if by == "date":
        notes_meta.sort(key=lambda m: m["modified"], reverse=True)
        col_header = "Modified"
        col_fn = lambda m: m["modified"].strftime("%Y-%m-%d %H:%M")
    elif by == "size":
        notes_meta.sort(key=lambda m: m["words"], reverse=True)
        col_header = "Words"
        col_fn = lambda m: str(m["words"])
    else:  # name
        notes_meta.sort(key=lambda m: m["relative"])
        col_header = "Folder"
        col_fn = lambda m: m["folder"]

    col_w = max(len(col_fn(m)) for m in notes_meta) if notes_meta else 10
    col_w = max(col_w, len(col_header))
    path_w = max(len(m["relative"]) for m in notes_meta) if notes_meta else 20

    header = f"{'Path':<{path_w}}  {col_header:<{col_w}}"
    print(f"\n{header}")
    print("-" * len(header))
    for m in notes_meta:
        print(f"{m['relative']:<{path_w}}  {col_fn(m):<{col_w}}")
    print(f"\n{len(notes_meta)} note(s) found.\n")


# ---------------------------------------------------------------------------
# Subcommand: organize
# ---------------------------------------------------------------------------


def cmd_organize(args: argparse.Namespace) -> None:
    """Generate (or refresh) a master index of all notes.

    If ``args.check_inbox`` is True, all pending inbox files are moved into
    the repository first (same behaviour as ``process-inbox --organize``),
    so the generated index always reflects an up-to-date state.
    """
    # --- Optional inbox processing -------------------------------------------
    if args.check_inbox:
        pending = pending_inbox_files()
        if pending:
            print(f"📬 {len(pending)} file(s) found in inbox/ — processing now…\n")
            # Lazy import avoids a circular dependency at module load time
            # (_importer imports cmd_organize from this module).
            from _importer import cmd_process_inbox  # noqa: PLC0415
            inbox_args = argparse.Namespace(dry_run=False, force=False, organize=False)
            cmd_process_inbox(inbox_args)
        else:
            print("📭 inbox/ is empty — nothing to process.\n")

    notes_meta = [_parse_note(p) for p in _all_notes()]

    # Group by top-level folder
    folders: dict[str, list[dict]] = {}
    for m in notes_meta:
        folders.setdefault(m["folder"], []).append(m)

    lines = [
        "# 📋 Master Notes Index",
        "",
        "> Auto-generated by `tools/notes_helper.py organize`  ",
        f"> Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    # Summary table
    lines += [
        "## Summary",
        "",
        "| Folder | Notes | Total Words |",
        "|--------|-------|-------------|",
    ]
    for folder in sorted(folders):
        folder_notes = folders[folder]
        total_words = sum(m["words"] for m in folder_notes)
        lines.append(
            f"| {folder} | {len(folder_notes)} | {total_words:,} |"
        )
    lines += [""]

    # Per-folder detail
    lines.append("## Notes by Folder")
    lines.append("")
    for folder in sorted(folders):
        lines.append(f"### {folder}")
        lines.append("")
        folder_notes = sorted(folders[folder], key=lambda m: m["relative"])
        for m in folder_notes:
            rel = m["relative"]
            # Build a relative link from the index file location
            link = f"../{rel}" if args.output else rel
            open_count = len(m["open_items"])
            badge = f" ✅ {len(m['done_items'])} done" if m["done_items"] else ""
            badge += f" 🔲 {open_count} open" if open_count else ""
            lines.append(
                f"- [{m['title']}]({link}) — {m['words']} words{badge}"
            )
        lines.append("")

    # Open action items summary
    all_open = [
        (m["relative"], item)
        for m in notes_meta
        for item in m["open_items"]
    ]
    if all_open:
        lines += [
            "## Open Action Items",
            "",
        ]
        current_file = None
        for rel, item in sorted(all_open, key=lambda x: x[0]):
            if rel != current_file:
                lines.append(f"**{rel}**")
                current_file = rel
            lines.append(f"  {item}")
        lines.append("")

    # Inbox status — always show so the index reflects what's waiting
    inbox_pending = pending_inbox_files()
    if inbox_pending:
        lines += [
            "## 📬 Inbox — Pending Files",
            "",
            "> The following file(s) are in `inbox/` and have not yet been imported.",
            "> Run `python3 tools/notes_helper.py process-inbox --organize` to move them.",
            "",
            "| File | Size |",
            "|------|------|",
        ]
        for p in inbox_pending:
            stat = p.stat()
            size = f"{stat.st_size / 1024:.1f} KB" if stat.st_size >= 1024 else f"{stat.st_size} B"
            lines.append(f"| {p.name} | {size} |")
        lines.append("")

    # Assets inventory
    all_assets = [_asset_meta(p) for p in _all_assets()]
    if all_assets:
        lines += [
            "## Assets",
            "",
        ]
        by_subfolder: dict[str, list[dict]] = {}
        for a in all_assets:
            by_subfolder.setdefault(a["subfolder"], []).append(a)
        for subfolder in sorted(by_subfolder):
            lines.append(f"### assets/{subfolder}" if subfolder != "(root)" else "### assets")
            lines.append("")
            lines.append("| File | Type | Size | Modified |")
            lines.append("|------|------|------|----------|")
            for a in sorted(by_subfolder[subfolder], key=lambda x: x["name"]):
                rel = a["relative"]
                link = f"../{rel}" if args.output else rel
                lines.append(
                    f"| [{a['name']}]({link}) | {a['kind']} | {a['size_display']} | {a['modified'].strftime('%Y-%m-%d')} |"
                )
            lines.append("")

    content = "\n".join(lines)

    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"Master index written to: {_relative(out_path)}")
    else:
        print(content)


# ---------------------------------------------------------------------------
# Subcommand: search
# ---------------------------------------------------------------------------


def cmd_search(args: argparse.Namespace) -> None:
    """Search all notes for a keyword and print matching lines with context."""
    keyword = args.keyword
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    context = args.context

    notes = _all_notes()
    if args.folder:
        notes = [p for p in notes if p.parts[len(REPO_ROOT.parts)] == args.folder]

    total_matches = 0
    for path in notes:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        matches = [
            (i + 1, line)
            for i, line in enumerate(lines)
            if pattern.search(line)
        ]
        if not matches:
            continue

        print(f"\n{'─'*60}")
        print(f"  📄 {_relative(path)}  ({len(matches)} match(es))")
        print(f"{'─'*60}")
        shown_lines: set[int] = set()
        for lineno, _ in matches:
            start = max(0, lineno - 1 - context)
            end = min(len(lines), lineno + context)
            for i in range(start, end):
                if i not in shown_lines:
                    marker = ">>>" if (i + 1) == lineno else "   "
                    snippet = lines[i]
                    # Highlight the keyword
                    snippet = pattern.sub(
                        lambda m: f"\033[1;33m{m.group()}\033[0m", snippet
                    )
                    print(f"  {marker} {i+1:4d} | {snippet}")
                    shown_lines.add(i)
        total_matches += len(matches)

    if total_matches == 0:
        print(f'\nNo matches found for "{keyword}".\n')
    else:
        print(f'\n{total_matches} match(es) for "{keyword}" across {len(notes)} file(s).\n')
