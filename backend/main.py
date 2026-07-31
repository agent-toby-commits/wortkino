"""Wortkino Backend – dynamisches Rendering und API."""

from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
import frontmatter
import markdown

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content" / "woerter"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

SITE_URL = os.environ.get("SITE_URL", "https://wortwoert.de").rstrip("/")
SITE_NAME = "Wortwört"
SITE_TAGLINE = "Lexikon der merkwürdigen Begriffe"
SITE_DESCRIPTION = (
    "Wortwört ist das Lexikon der merkwürdigen Begriffe: "
    "deutsche Wörter, die wörtlich genommen überraschende Bilder erzeugen."
)

H1_LINE_PATTERN = re.compile(r"^# (.+?):?\s*$", re.MULTILINE)
BEDEUTUNG_PATTERN = re.compile(
    r"^## Bedeutung\s*\n+(.+?)(?=\n## |\Z)",
    re.MULTILINE | re.DOTALL,
)

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


def neighbors(slug: str) -> tuple[dict | None, dict | None]:
    entries = list_entries()
    for i, entry in enumerate(entries):
        if entry["slug"] == slug:
            prev_entry = entries[i - 1] if i > 0 else None
            next_entry = entries[i + 1] if i < len(entries) - 1 else None
            return prev_entry, next_entry
    return None, None


def extract_bedeutung(body_md: str) -> str:
    match = BEDEUTUNG_PATTERN.search(body_md)
    if not match:
        return SITE_DESCRIPTION
    text = match.group(1)
    text = re.sub(r"[*_`]+", "", text)
    text = re.sub(r"\s+", " ", text).strip().strip("„\"»«")
    if len(text) > 155:
        text = text[:152].rsplit(" ", 1)[0] + "…"
    return text or SITE_DESCRIPTION


def extract_bedeutung_md(body_md: str) -> str:
    match = BEDEUTUNG_PATTERN.search(body_md)
    if not match:
        return ""
    return match.group(1).strip()


def absolute_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{SITE_URL}{path if path.startswith('/') else '/' + path}"


def render_head(
    *,
    title: str,
    description: str,
    canonical_path: str,
    og_type: str = "website",
    image_path: str | None = None,
    json_ld: dict | list | None = None,
) -> str:
    canonical = absolute_url(canonical_path)
    desc = html.escape(description, quote=True)
    title_esc = html.escape(title, quote=True)
    image = absolute_url(image_path) if image_path else None

    parts = [
        '  <meta charset="UTF-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"  <title>{title_esc}</title>",
        f'  <meta name="description" content="{desc}">',
        f'  <link rel="canonical" href="{html.escape(canonical, quote=True)}">',
        f'  <meta property="og:title" content="{title_esc}">',
        f'  <meta property="og:description" content="{desc}">',
        f'  <meta property="og:url" content="{html.escape(canonical, quote=True)}">',
        f'  <meta property="og:type" content="{html.escape(og_type, quote=True)}">',
        f'  <meta property="og:site_name" content="{html.escape(SITE_NAME, quote=True)}">',
        f'  <meta property="og:locale" content="de_DE">',
        f'  <meta name="twitter:card" content="{"summary_large_image" if image else "summary"}">',
        f'  <meta name="twitter:title" content="{title_esc}">',
        f'  <meta name="twitter:description" content="{desc}">',
    ]
    if image:
        img_esc = html.escape(image, quote=True)
        parts.append(f'  <meta property="og:image" content="{img_esc}">')
        parts.append(f'  <meta name="twitter:image" content="{img_esc}">')
    if json_ld is not None:
        ld = json.dumps(json_ld, ensure_ascii=False, separators=(",", ":"))
        parts.append(
            f'  <script type="application/ld+json">{ld}</script>'
        )
    parts.extend(
        [
            '  <link rel="preconnect" href="https://fonts.googleapis.com">',
            '  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">',
            '  <link rel="stylesheet" href="/css/style.css">',
        ]
    )
    return "\n".join(parts)


def render_bild_html(bild: str | None, title: str) -> str:
    if not bild or not (CONTENT_DIR / bild).exists():
        return (
            '<div class="tafel-platzhalter" aria-hidden="true">'
            "<span>Abb. folgt</span>"
            "</div>"
        )
    return (
        f'<figure class="wort-bild">'
        f'<img src="/content/woerter/{bild}" alt="Illustration zu {html.escape(title, quote=True)}">'
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
    title_esc = html.escape(title)
    if title_as_link:
        title_html = (
            f'<h2 class="wort-titel">'
            f'<a href="/woerter/{html.escape(slug, quote=True)}">{title_esc}</a></h2>'
        )
    else:
        title_html = f'<h1 class="wort-titel">{title_esc}</h1>'
    nr_html = f'<span class="wort-nr">Nr. {nr:02d}</span>' if nr is not None else ""

    return f"""<article class="wort-eintrag" id="{html.escape(slug, quote=True)}">
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


def render_teaser_block(
    slug: str,
    title: str,
    post,
    body_md: str,
    *,
    nr: int | None = None,
) -> str:
    bedeutung_md = extract_bedeutung_md(body_md)
    bedeutung_html = (
        markdown.markdown(bedeutung_md, extensions=["extra"])
        if bedeutung_md
        else "<p></p>"
    )
    bild_html = render_bild_html(post.get("bild"), title)
    title_esc = html.escape(title)
    slug_esc = html.escape(slug, quote=True)
    nr_html = f'<span class="wort-nr">Nr. {nr:02d}</span>' if nr is not None else ""

    return f"""<article class="wort-eintrag wort-teaser" id="{slug_esc}">
  <div class="wort-kopf">
    <h2 class="wort-titel"><a href="/woerter/{slug_esc}">{title_esc}</a></h2>
    {nr_html}
  </div>
  <div class="wort-layout">
    {bild_html}
    <div class="wort-text">
      <h3>Bedeutung</h3>
      {bedeutung_html}
      <p class="wort-teaser-link"><a href="/woerter/{slug_esc}">Zum Eintrag →</a></p>
    </div>
  </div>
</article>"""


def render_nav_side(entry: dict | None, *, direction: str) -> str:
    if direction == "prev":
        label = "Vorheriger Wortwört-Eintrag"
        arrow = "←"
        css = "wort-nav-prev"
    else:
        label = "Nächster Wortwört-Eintrag"
        arrow = "→"
        css = "wort-nav-next"

    if entry is None:
        return (
            f'<span class="{css} is-disabled" aria-disabled="true">'
            f'<span class="wort-nav-label">{label}</span>'
            f'<span class="wort-nav-begriff">—</span>'
            f"</span>"
        )

    begriff = html.escape(entry["title"])
    slug = html.escape(entry["slug"], quote=True)
    if direction == "prev":
        begriff_line = f"{arrow} {begriff}"
    else:
        begriff_line = f"{begriff} {arrow}"

    return (
        f'<a class="{css}" href="/woerter/{slug}">'
        f'<span class="wort-nav-label">{label}</span>'
        f'<span class="wort-nav-begriff">{begriff_line}</span>'
        f"</a>"
    )


def render_nav(prev: dict | None, next_entry: dict | None) -> str:
    return f"""<nav class="wort-nav" aria-label="Eintragsnavigation">
  <a class="wort-nav-index" href="/">Zurück zum Inhaltsverzeichnis</a>
  <div class="wort-nav-neighbors">
    {render_nav_side(prev, direction="prev")}
    {render_nav_side(next_entry, direction="next")}
  </div>
</nav>"""


def render_az_nav(entries: list[dict]) -> str:
    items = "\n".join(
        f'      <li><a href="/woerter/{html.escape(e["slug"], quote=True)}">'
        f'{html.escape(e["title"])}</a></li>'
        for e in entries
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
        render_teaser_block(
            e["slug"],
            e["title"],
            e["post"],
            e["body_md"],
            nr=i,
        )
        for i, e in enumerate(entries, start=1)
    ]
    overview = (
        '<section class="wort-uebersicht" aria-label="Alle Einträge">\n'
        + '\n<hr class="trennregel">\n'.join(entry_blocks)
        + "\n</section>"
    )

    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": SITE_URL,
        "description": SITE_DESCRIPTION,
        "inLanguage": "de",
        "publisher": {"@type": "Organization", "name": SITE_NAME},
    }

    head = render_head(
        title=f"{SITE_NAME} – {SITE_TAGLINE}",
        description=SITE_DESCRIPTION,
        canonical_path="/",
        og_type="website",
        json_ld=json_ld,
    )

    html = index_path.read_text(encoding="utf-8")
    html = html.replace("<!--SEO_HEAD-->", head)
    html = html.replace("<!--WORT_AZ-->", az_nav)
    html = html.replace("<!--WORT_UEBERSICHT-->", overview)
    return html


@app.get("/woerter/{slug}", response_class=HTMLResponse)
def wort_detail(slug: str):
    post, title, body_md = load_entry(slug)
    entry_html = render_entry_block(slug, title, post, body_md)
    prev_entry, next_entry = neighbors(slug)
    nav = render_nav(prev_entry, next_entry)

    bedeutung = extract_bedeutung(body_md)
    description = f"{title}: {bedeutung}"
    if len(description) > 155:
        description = bedeutung

    bild = post.get("bild")
    image_path = None
    if bild and (CONTENT_DIR / str(bild)).exists():
        image_path = f"/content/woerter/{bild}"

    json_ld = {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "name": title,
        "description": bedeutung,
        "inDefinedTermSet": absolute_url("/"),
        "url": absolute_url(f"/woerter/{slug}"),
    }
    if image_path:
        json_ld["image"] = absolute_url(image_path)

    head = render_head(
        title=f"{title} – {SITE_NAME} | {SITE_TAGLINE}",
        description=description,
        canonical_path=f"/woerter/{slug}",
        og_type="article",
        image_path=image_path,
        json_ld=json_ld,
    )

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
{head}
</head>
<body class="seite-eintrag">
  <header><a href="/">{html.escape(SITE_NAME)}</a></header>
  <main>
    {nav}
    {entry_html}
    {nav}
  </main>
</body>
</html>"""


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )


@app.get("/sitemap.xml")
def sitemap_xml():
    entries = list_entries()
    urls = [
        f"  <url><loc>{xml_escape(absolute_url('/'))}</loc><changefreq>weekly</changefreq></url>"
    ]
    for entry in entries:
        loc = absolute_url(f"/woerter/{entry['slug']}")
        urls.append(
            f"  <url><loc>{xml_escape(loc)}</loc><changefreq>monthly</changefreq></url>"
        )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return Response(content=body, media_type="application/xml")


app.mount("/content/woerter", StaticFiles(directory=CONTENT_DIR), name="content-woerter")
