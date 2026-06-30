#!/usr/bin/env python3
"""Upload a folder of Markdown files to a Notion database.

Each .md file becomes a page:
  - title  = filename (without extension), or frontmatter `title:` if present
  - Type   = frontmatter `tags:` (list or comma string) -> multi_select

Usage:
  export NOTION_TOKEN=secret_xxx
  export NOTION_DATABASE_ID=xxxxxxxx
  python md_to_notion.py ./my-folder
"""
import os
import sys
import argparse
from pathlib import Path

import frontmatter
from notion_client import Client


def normalize_tags(meta) -> list[str]:
    tags = meta.get("tags") or meta.get("type") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.replace(",", " ").split()]
    return [str(t).strip() for t in tags if str(t).strip()]


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


def upload(folder: Path, token: str, db_id: str):
    notion = Client(auth=token)
    files = sorted(folder.glob("*.md"))
    if not files:
        sys.exit(f"No .md files in {folder}")
    for f in files:
        post = frontmatter.load(f)
        title = post.get("title") or f.stem
        tags = normalize_tags(post.metadata)
        notion.pages.create(
            parent={"database_id": db_id},
            properties={
                "Name": {"title": [{"text": {"content": str(title)}}]},
                "Type": {"multi_select": [{"name": t} for t in tags]},
            },
            children=md_to_blocks(post.content),
        )
        print(f"  uploaded: {f.name}  [{', '.join(tags) or 'no tags'}]")
    print(f"Done. {len(files)} pages created.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Upload Markdown folder to a Notion database.")
    ap.add_argument("folder", type=Path, help="Folder containing .md files")
    ap.add_argument("--token", default=os.environ.get("NOTION_TOKEN"))
    ap.add_argument("--database-id", default=os.environ.get("NOTION_DATABASE_ID"))
    a = ap.parse_args()
    if not a.token or not a.database_id:
        sys.exit("Set NOTION_TOKEN and NOTION_DATABASE_ID (env or flags).")
    upload(a.folder, a.token, a.database_id)
