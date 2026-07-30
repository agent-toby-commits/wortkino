"""Wortkino Backend – dynamisches Rendering und API."""

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


def render_bild_html(bild: str | None, title: str) -> str:
    if not bild:
        return ""
    return (
        f'<figure class="wort-bild">'
        f'<img src="/content/woerter/{bild}" alt="Illustration zu {title}">'
        f"</figure>"
    )


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<h1>Wortkino</h1>"


@app.get("/woerter/{slug}", response_class=HTMLResponse)
def wort_detail(slug: str):
    post, title, body_md = load_entry(slug)
    text_html = markdown.markdown(body_md, extensions=["extra"])
    bild_html = render_bild_html(post.get("bild"), title)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} – Wortkino</title>
  <link rel="stylesheet" href="/css/style.css">
</head>
<body class="seite-eintrag">
  <header><a href="/">Wortkino</a></header>
  <main class="wort-eintrag">
    <h1 class="wort-titel">{title}</h1>
    <div class="wort-layout">
      {bild_html}
      <div class="wort-text">
        {text_html}
      </div>
    </div>
  </main>
</body>
</html>"""


app.mount("/content/woerter", StaticFiles(directory=CONTENT_DIR), name="content-woerter")
