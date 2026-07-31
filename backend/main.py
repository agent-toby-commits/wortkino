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
CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"

SITE_URL = os.environ.get("SITE_URL", "https://wortwoert.de").rstrip("/")
SITE_NAME = "Wortwört"
SITE_TAGLINE = "Lexikon der merkwürdigen Begriffe"
SITE_DESCRIPTION = (
    "Wortwört ist das Lexikon der merkwürdigen Begriffe: "
    "deutsche Wörter, die wörtlich genommen überraschende Bilder erzeugen."
)
AUTHOR_NAME = "Tobias Lampe"
AUTHOR_CITY = "Berlin"
AUTHOR_PORTRAIT_NAME = "autor-portrait.png"
BOOK_COVER_NAME = "buch-wortwoertlich.png"


def resolve_asset(filename: str) -> Path | None:
    """Finde Asset case-insensitive (macOS lokal vs. Linux in Produktion)."""
    target = ASSETS_DIR / filename
    if target.exists():
        return target
    wanted = filename.casefold()
    if not ASSETS_DIR.is_dir():
        return None
    for path in ASSETS_DIR.iterdir():
        if path.is_file() and path.name.casefold() == wanted:
            return path
    return None

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


def render_site_header(*, link_home: bool = False) -> str:
    """Gemeinsamer Lexikon-Header (Marke, Untertitel, Doppelregel, Meta-Nav)."""
    name = html.escape(SITE_NAME)
    tagline = html.escape(SITE_TAGLINE)
    if link_home:
        title_html = f'<h1><a href="/">{name}</a></h1>'
    else:
        title_html = f"<h1>{name}</h1>"
    return f"""  <header class="site-header">
    {title_html}
    <p>{tagline}</p>
    <div class="doppelregel" aria-hidden="true"></div>
    <nav class="site-meta-nav" aria-label="Über Wortwört">
      <a href="/ueber">Über den Autor · Das Buch</a>
    </nav>
  </header>"""


def parse_h2_sections(md: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"^## (.+)$", re.MULTILINE)
    matches = list(pattern.finditer(md))
    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        sections.append((title, md[start:end].strip()))
    return sections


def asset_url(path: Path) -> str:
    return f"/assets/{path.name}"


def render_autor_portrait() -> str:
    caption = html.escape(f"{AUTHOR_NAME}, {AUTHOR_CITY}")
    portrait = resolve_asset(AUTHOR_PORTRAIT_NAME)
    if portrait is not None:
        src = html.escape(asset_url(portrait), quote=True)
        return (
            f'<figure class="autor-portrait">'
            f'<img src="{src}" '
            f'alt="Porträtfoto von {html.escape(AUTHOR_NAME)} aus {html.escape(AUTHOR_CITY)}" '
            f'width="480" height="640" loading="eager">'
            f"<figcaption>{caption}</figcaption>"
            f"</figure>"
        )
    return (
        '<figure class="autor-portrait is-placeholder">'
        '<div class="autor-portrait-platzhalter" aria-hidden="true">'
        "<span>Porträt folgt</span>"
        "</div>"
        f"<figcaption>{caption}</figcaption>"
        "</figure>"
    )


def render_buch_cover(*, as_backdrop: bool = False) -> str:
    alt = (
        "Fotorealistische Abbildung des Lexikons "
        "wortwörtlich – das Lexikon der wundersamen Wörter"
    )
    classes = "buch-cover buch-cover--backdrop" if as_backdrop else "buch-cover"
    aria = ' aria-hidden="true"' if as_backdrop else ""
    cover = resolve_asset(BOOK_COVER_NAME)
    if cover is not None:
        src = html.escape(asset_url(cover), quote=True)
        caption = (
            ""
            if as_backdrop
            else "<figcaption>wortwörtlich – das Lexikon der wundersamen Wörter</figcaption>"
        )
        return (
            f'<figure class="{classes}"{aria}>'
            f'<img src="{src}" '
            f'alt="{html.escape(alt, quote=True)}" '
            f'width="900" height="1200" loading="lazy">'
            f"{caption}"
            f"</figure>"
        )
    return (
        f'<figure class="{classes} is-placeholder"{aria}>'
        '<div class="buch-cover-platzhalter" aria-hidden="true">'
        "<span>Buchabbildung folgt</span>"
        "</div>"
        "</figure>"
    )


def render_rezensionen_html(body_md: str) -> str:
    """Render Rezensionen als separate blockquotes (Markdown merged sie sonst)."""
    blocks = re.split(r"\n(?:[ \t]*\n)+", body_md.strip())
    parts: list[str] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        parts.append(markdown.markdown(block, extensions=["extra"]))
    return "\n".join(parts)


def render_ueber_body(content_md: str) -> str:
    blocks: list[str] = []
    for title, body_md in parse_h2_sections(content_md):
        title_esc = html.escape(title)
        if title.casefold().startswith("über den autor"):
            body_html = markdown.markdown(body_md, extensions=["extra"])
            blocks.append(
                f'<section class="ueber-autor" aria-labelledby="ueber-autor-heading">'
                f'<h2 id="ueber-autor-heading">{title_esc}</h2>'
                f'<div class="autor-layout">'
                f"{render_autor_portrait()}"
                f'<div class="autor-text">{body_html}</div>'
                f"</div>"
                f"</section>"
            )
        elif "wortwörtlich" in title.casefold():
            rezensionen_html = render_rezensionen_html(body_md)
            blocks.append(
                f'<section class="ueber-buch" aria-labelledby="ueber-buch-heading">'
                f'<h2 id="ueber-buch-heading">{title_esc}</h2>'
                f'<div class="buch-rezensionen-stage">'
                f"{render_buch_cover(as_backdrop=True)}"
                f'<div class="buch-rezensionen">{rezensionen_html}</div>'
                f"</div>"
                f"</section>"
            )
        else:
            body_html = markdown.markdown(body_md, extensions=["extra"])
            blocks.append(
                f"<section>"
                f"<h2>{title_esc}</h2>"
                f"{body_html}"
                f"</section>"
            )
    return "\n".join(blocks)


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

    page = index_path.read_text(encoding="utf-8")
    page = page.replace("<!--SEO_HEAD-->", head)
    page = page.replace("<!--SITE_HEADER-->", render_site_header(link_home=False))
    page = page.replace("<!--WORT_AZ-->", az_nav)
    page = page.replace("<!--WORT_UEBERSICHT-->", overview)
    return page


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
{render_site_header(link_home=True)}
  <main>
    {nav}
    {entry_html}
    {nav}
  </main>
  <footer class="site-footer">
    <a href="/ueber">Über den Autor · Das Buch</a>
  </footer>
</body>
</html>"""


@app.get("/ueber", response_class=HTMLResponse)
def ueber():
    path = CONTENT_ROOT / "ueber.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")

    post = frontmatter.load(path)
    default_title = f"{AUTHOR_NAME} {AUTHOR_CITY} – Autor von {SITE_NAME}"
    default_description = (
        f"{AUTHOR_NAME} aus {AUTHOR_CITY} ist Autor von {SITE_NAME}, "
        f"dem {SITE_TAGLINE.lower()}, und des Buchprojekts "
        "wortwörtlich – das Lexikon der wundersamen Wörter."
    )
    page_title = str(post.get("title", default_title))
    description = str(post.get("description", default_description))
    body_html = render_ueber_body(post.content)

    person: dict = {
        "@type": "Person",
        "name": AUTHOR_NAME,
        "jobTitle": "Autor",
        "url": absolute_url("/ueber"),
        "address": {
            "@type": "PostalAddress",
            "addressLocality": AUTHOR_CITY,
            "addressCountry": "DE",
        },
        "knowsAbout": [
            "deutsche Sprache",
            "Lexikon",
            "Wortwört",
            "Humor",
        ],
        "author": {
            "@type": "CreativeWork",
            "name": "wortwörtlich – das Lexikon der wundersamen Wörter",
        },
    }
    portrait = resolve_asset(AUTHOR_PORTRAIT_NAME)
    cover = resolve_asset(BOOK_COVER_NAME)

    if portrait is not None:
        person["image"] = absolute_url(asset_url(portrait))

    book_image = absolute_url(asset_url(cover)) if cover is not None else None
    book_ld: dict = {
        "@type": "Book",
        "name": "wortwörtlich – das Lexikon der wundersamen Wörter",
        "author": {"@type": "Person", "name": AUTHOR_NAME},
        "inLanguage": "de",
        "description": (
            "Das Buch zum Lexikon Wortwört: merkwürdige Begriffe, "
            "wörtlich genommen."
        ),
    }
    if book_image:
        book_ld["image"] = book_image

    json_ld = [
        {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "name": page_title,
            "url": absolute_url("/ueber"),
            "description": description,
            "inLanguage": "de",
            "isPartOf": {
                "@type": "WebSite",
                "name": SITE_NAME,
                "url": SITE_URL,
            },
            "mainEntity": person,
            "about": [
                {"@type": "Person", "name": AUTHOR_NAME},
                {"@type": "Place", "name": AUTHOR_CITY},
            ],
        },
        {"@context": "https://schema.org", **book_ld},
    ]

    if portrait is not None:
        og_image = asset_url(portrait)
    elif cover is not None:
        og_image = asset_url(cover)
    else:
        og_image = None

    head = render_head(
        title=f"{page_title} | {SITE_NAME}",
        description=description,
        canonical_path="/ueber",
        og_type="profile",
        image_path=og_image,
        json_ld=json_ld,
    )
    # Extra local SEO hints for Tobias Lampe Berlin
    head += (
        f'\n  <meta name="author" content="{html.escape(AUTHOR_NAME, quote=True)}">'
        f'\n  <meta name="geo.placename" content="{html.escape(AUTHOR_CITY, quote=True)}">'
        f'\n  <meta name="geo.region" content="DE-BE">'
    )

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
{head}
</head>
<body class="seite-ueber">
{render_site_header(link_home=True)}
  <main class="ueber-inhalt">
    {body_html}
    <p class="ueber-cta"><a href="/">Zum Register A–Z</a></p>
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
        f"  <url><loc>{xml_escape(absolute_url('/'))}</loc><changefreq>weekly</changefreq></url>",
        f"  <url><loc>{xml_escape(absolute_url('/ueber'))}</loc><changefreq>monthly</changefreq></url>",
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
