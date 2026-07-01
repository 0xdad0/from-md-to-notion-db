# md-to-notion

Upload a folder of Markdown files to a Notion database. Filename becomes the
page title; frontmatter keys map to Notion columns (or all fall into `Type`).

## Requirements

- Python 3.10+
- Packages: `pip install -r requirements.txt`
- A Notion integration token and a target database.

## Notion setup (one time)

1. Create an internal integration at <https://www.notion.so/my-integrations>
   and copy the **Internal Integration Secret** (`ntn_...` / `secret_...`).
2. Create (or open) a database with these properties:
   - **Name** — type *Title* (default, already exists)
   - **Type** — type *Multi-select*
3. Open the database → `•••` → **Connections** → add your integration, so it
   has write access.
4. Grab the **database ID** from the database URL:
   `https://www.notion.so/<workspace>/<DATABASE_ID>?v=...`
   (the 32-char hex string before `?v=`).

## Markdown format

```markdown
---
title: Optional Title       # if omitted, the filename is used
platform: android           # can be routed to a column via --map
tags: [recon, web, oauth]   # or:  tags: recon, web, oauth
---

# Heading
Body text, - bullets, and ```code``` fences are converted to Notion blocks.
```

Files without frontmatter work too: title = filename, no properties.

## Mapping frontmatter keys to columns

By default every frontmatter value (except `title`) is dumped into the `Type`
multi-select. Use `--map md_key=notion_col` (repeatable) to route a specific
key to its own column instead:

```bash
python md_to_notion.py ./my-folder --map platform=os --map env=environment
```

With the example above, `platform: android` lands in the **os** column, `tags`
stay in **Type**. The target column must exist in the database and be a
*Multi-select* type.

## Usage

```bash
pip install -r requirements.txt

export NOTION_TOKEN=ntn_xxx
export NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

python md_to_notion.py ./my-folder
```

Or pass them as flags: `--token` and `--database-id`.

## Limits

- The title column must be named **Name**; unmapped values need a **Type**
  multi-select. Mapped columns must exist and be *Multi-select*.
- Body conversion handles headings, bullets, paragraphs, and fenced code only.
  No tables / nested lists / inline formatting. Max 100 blocks per file.
