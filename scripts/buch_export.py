#!/usr/bin/env python3
"""Exportiert Lexikoneinträge für eine spätere Buchfassung."""

from __future__ import annotations

import re
from pathlib import Path

import frontmatter
import markdown

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content" / "woerter"
OUTPUT_DIR = ROOT / "output" / "buch"

H1_LINE_PATTERN = re.compile(r"^# (.+?):?\s*$", re.MULTILINE)


def split_entry_content(content: str) -> tuple[str, str]:
    match = H1_LINE_PATTERN.search(content)
    if not match:
        return "", content.strip()
    title = match.group(1).strip()
    body = (content[: match.start()] + content[match.end() :]).strip()
    return title, body


def export_markdown_entry(path: Path) -> str:
    post = frontmatter.load(path)
    title, body_md = split_entry_content(post.content)
    if not title:
        title = str(post.get("begriff", path.stem))
    bild = post.get("bild", "")

    lines = [f"# {title}", ""]
    if bild:
        lines.extend(
            [
                "<!-- buch:bildseite -->",
                "",
                f"![Illustration zu {title}]({bild})",
                "",
                "<!-- buch:textseite -->",
                "",
            ]
        )
    lines.append(body_md)
    lines.append("")
    return "\n".join(lines)


def export_html_entries(paths: list[Path]) -> str:
    entries_html: list[str] = []

    for path in paths:
        post = frontmatter.load(path)
        title, body_md = split_entry_content(post.content)
        if not title:
            title = str(post.get("begriff", path.stem))
        bild = post.get("bild", "")
        text_html = markdown.markdown(body_md, extensions=["extra"])

        bild_block = ""
        if bild:
            bild_block = (
                f'<section class="buch-seite buch-bildseite">'
                f'<figure><img src="../../content/woerter/{bild}" alt="Illustration zu {title}"></figure>'
                f"</section>"
            )

        entries_html.append(
            f"""<article class="buch-eintrag">
  <h1 class="buch-titel">{title}</h1>
  <div class="buch-spread">
    {bild_block}
    <section class="buch-seite buch-textseite">
      {text_html}
    </section>
  </div>
</article>"""
        )

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Wortkino – Buchentwurf</title>
  <link rel="stylesheet" href="../../frontend/css/style.css">
</head>
<body class="buch-export">
  <main>
{chr(10).join(entries_html)}
  </main>
</body>
</html>"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(CONTENT_DIR.glob("*.md"))

    md_parts = ["# Wortkino – Buchentwurf", ""]
    for path in paths:
        md_parts.append(export_markdown_entry(path))
        md_parts.append("---")
        md_parts.append("")

    md_file = OUTPUT_DIR / "wortkino-entwurf.md"
    md_file.write_text("\n".join(md_parts), encoding="utf-8")
    print(f"Markdown-Export: {md_file}")

    html_file = OUTPUT_DIR / "wortkino-entwurf.html"
    html_file.write_text(export_html_entries(paths), encoding="utf-8")
    print(f"HTML-Export (Doppelseite): {html_file}")


if __name__ == "__main__":
    main()
