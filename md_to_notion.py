#!/usr/bin/env python3
"""Upload a folder of Markdown files to a Notion database.

Each .md file becomes a page:
  - title  = filename (without extension), or frontmatter `title:` if present
  - mapped frontmatter keys -> their Notion column (--map md_key=notion_col)
  - every other frontmatter value -> the `Type` multi_select

Usage:
  export NOTION_TOKEN=secret_xxx
  export NOTION_DATABASE_ID=xxxxxxxx
  python md_to_notion.py ./my-folder --map platform=os --map env=environment
"""
import os
import sys
import argparse
from pathlib import Path

import frontmatter
from notion_client import Client


def to_values(v) -> list[str]:
    """Any frontmatter value -> list of clean strings."""
    if v is None:
        return []
    if isinstance(v, str):
        v = v.replace(",", " ").split()
    elif not isinstance(v, (list, tuple)):
        v = [v]
    return [str(x).strip() for x in v if str(x).strip()]


def build_properties(meta: dict, title, mapping: dict[str, str]) -> dict:
    """title -> Name; mapped keys -> their column; the rest -> Type.
    ponytail: all routed columns are multi_select. If a target column is a
    `select`/`rich_text` type, adjust the payload here.
    """
    columns: dict[str, list[str]] = {}
    for key, val in meta.items():
        if key == "title":
            continue
        col = mapping.get(key, "Type")
        columns.setdefault(col, []).extend(to_values(val))
    props = {"Name": {"title": [{"text": {"content": str(title)}}]}}
    for col, vals in columns.items():
        props[col] = {"multi_select": [{"name": v} for v in dict.fromkeys(vals)]}
    return props


def md_to_blocks(text: str) -> list[dict]:
    """Line-based Markdown -> Notion blocks.
    ponytail: handles headings, bullets, fenced code, paragraphs only.
    Upgrade to `martian`-style full parser if tables/nested lists matter.
    """
    def rich(s: str) -> list[dict]:
        return [{"type": "text", "text": {"content": s[:2000]}}]

    blocks, in_code, code_buf = [], False, []
    for line in text.splitlines():
        if line.startswith("```"):
            if in_code:
                blocks.append({"type": "code", "code": {
                    "rich_text": rich("\n".join(code_buf)), "language": "plain text"}})
                code_buf, in_code = [], False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue
        s = line.rstrip()
        if not s:
            continue
        if s.startswith("### "):
            blocks.append({"type": "heading_3", "heading_3": {"rich_text": rich(s[4:])}})
        elif s.startswith("## "):
            blocks.append({"type": "heading_2", "heading_2": {"rich_text": rich(s[3:])}})
        elif s.startswith("# "):
            blocks.append({"type": "heading_1", "heading_1": {"rich_text": rich(s[2:])}})
        elif s.lstrip().startswith(("- ", "* ")):
            blocks.append({"type": "bulleted_list_item",
                           "bulleted_list_item": {"rich_text": rich(s.lstrip()[2:])}})
        else:
            blocks.append({"type": "paragraph", "paragraph": {"rich_text": rich(s)}})
    if in_code:  # unterminated fence
        blocks.append({"type": "code", "code": {
            "rich_text": rich("\n".join(code_buf)), "language": "plain text"}})
    return blocks[:100]  # ponytail: Notion caps 100 blocks/create; chunk if files are huge


def upload(folder: Path, token: str, db_id: str, mapping: dict[str, str]):
    notion = Client(auth=token)
    files = sorted(folder.glob("*.md"))
    if not files:
        sys.exit(f"No .md files in {folder}")
    for f in files:
        post = frontmatter.load(f)
        title = post.get("title") or f.stem
        props = build_properties(post.metadata, title, mapping)
        notion.pages.create(
            parent={"database_id": db_id},
            properties=props,
            children=md_to_blocks(post.content),
        )
        cols = ", ".join(k for k in props if k != "Name") or "no props"
        print(f"  uploaded: {f.name}  [{cols}]")
    print(f"Done. {len(files)} pages created.")


def parse_map(pairs: list[str]) -> dict[str, str]:
    out = {}
    for p in pairs or []:
        if "=" not in p:
            sys.exit(f"--map expects md_key=notion_col, got: {p}")
        k, col = p.split("=", 1)
        out[k.strip()] = col.strip()
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Upload Markdown folder to a Notion database.")
    ap.add_argument("folder", type=Path, help="Folder containing .md files")
    ap.add_argument("--token", default=os.environ.get("NOTION_TOKEN"))
    ap.add_argument("--database-id", default=os.environ.get("NOTION_DATABASE_ID"))
    ap.add_argument("--map", action="append", metavar="MD_KEY=NOTION_COL",
                    help="Route a frontmatter key to a Notion column (repeatable). "
                         "Unmapped values go to Type.")
    a = ap.parse_args()
    if not a.token or not a.database_id:
        sys.exit("Set NOTION_TOKEN and NOTION_DATABASE_ID (env or flags).")
    upload(a.folder, a.token, a.database_id, parse_map(a.map))
