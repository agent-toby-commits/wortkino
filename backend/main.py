"""Wortkino Backend – dynamisches Rendering und API."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import frontmatter
import markdown

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content" / "woerter"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

H1_LINE_PATTERN = re.compile(r"^# (.+?):?\s*$", re.MULTILINE)

app = FastAPI(title="Wortkino")
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


def split_entry_content(content: str) -> tuple[str, str]:
    match = H1_LINE_PATTERN.search(content)
    if not match:
        return "", content.strip()
    title = match.group(1).strip()
    body = (content[: match.start()] + content[match.end() :]).strip()
    return title, body


def load_entry(slug: str):
    path = CONTENT_DIR / f"{slug}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    post = frontmatter.load(path)
    title, body_md = split_entry_content(post.content)
    if not title:
        title = str(post.get("begriff", slug))
    return post, title, body_md


def list_entries() -> list[dict]:
    entries: list[dict] = []
    for path in CONTENT_DIR.glob("*.md"):
        post = frontmatter.load(path)
        title, body_md = split_entry_content(post.content)
        if not title:
            title = str(post.get("begriff", path.stem))
        entries.append(
            {
                "slug": path.stem,
                "title": title,
                "post": post,
                "body_md": body_md,
            }
        )
    entries.sort(key=lambda e: e["title"].casefold())
    return entries


def render_bild_html(bild: str | None, title: str) -> str:
    if not bild or not (CONTENT_DIR / bild).exists():
        return (
            '<div class="tafel-platzhalter" aria-hidden="true">'
            "<span>Abb. folgt</span>"
            "</div>"
        )
    return (
        f'<figure class="wort-bild">'
        f'<img src="/content/woerter/{bild}" alt="Illustration zu {title}">'
        f'<figcaption>Bild im Kopf, wörtlich genommen.</figcaption>'
        f"</figure>"
    )


def render_entry_block(
    slug: str,
    title: str,
    post,
    body_md: str,
    *,
    title_as_link: bool = False,
    nr: int | None = None,
) -> str:
    text_html = markdown.markdown(body_md, extensions=["extra"])
    bild_html = render_bild_html(post.get("bild"), title)
    if title_as_link:
        title_html = f'<h2 class="wort-titel"><a href="/woerter/{slug}">{title}</a></h2>'
    else:
        title_html = f'<h1 class="wort-titel">{title}</h1>'
    nr_html = f'<span class="wort-nr">Nr. {nr:02d}</span>' if nr is not None else ""

    return f"""<article class="wort-eintrag" id="{slug}">
  <div class="wort-kopf">
    {title_html}
    {nr_html}
  </div>
  <div class="wort-layout">
    {bild_html}
    <div class="wort-text">
      {text_html}
    </div>
  </div>
</article>"""


def render_az_nav(entries: list[dict]) -> str:
    items = "\n".join(
        f'      <li><a href="/woerter/{e["slug"]}">{e["title"]}</a></li>' for e in entries
    )
    return f"""<nav class="wort-az" aria-label="Alphabetische Wortliste">
  <h2>Register A&ndash;Z</h2>
  <ul>
{items}
  </ul>
</nav>"""


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>Wortkino</h1>", status_code=500)

    entries = list_entries()
    az_nav = render_az_nav(entries)
    entry_blocks = [
        render_entry_block(
            e["slug"],
            e["title"],
            e["post"],
            e["body_md"],
            title_as_link=True,
            nr=i,
        )
        for i, e in enumerate(entries, start=1)
    ]
    overview = (
        '<section class="wort-uebersicht" aria-label="Alle Einträge">\n'
        + '\n<hr class="trennregel">\n'.join(entry_blocks)
        + "\n</section>"
    )

    html = index_path.read_text(encoding="utf-8")
    html = html.replace("<!--WORT_AZ-->", az_nav)
    html = html.replace("<!--WORT_UEBERSICHT-->", overview)
    return html


@app.get("/woerter/{slug}", response_class=HTMLResponse)
def wort_detail(slug: str):
    post, title, body_md = load_entry(slug)
    entry_html = render_entry_block(slug, title, post, body_md)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} – Wortwört</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/style.css">
</head>
<body class="seite-eintrag">
  <header><a href="/">Wortwört</a></header>
  <main>
    {entry_html}
  </main>
</body>
</html>"""


app.mount("/content/woerter", StaticFiles(directory=CONTENT_DIR), name="content-woerter")
