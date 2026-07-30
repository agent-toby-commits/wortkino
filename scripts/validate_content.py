#!/usr/bin/env python3
"""Validiert Lexikoneinträge in content/woerter/."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import frontmatter
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content" / "woerter"
SCHEMA_PATH = ROOT / "content" / "schema.yaml"

H1_PATTERN = re.compile(r"^# (.+?):?\s*$", re.MULTILINE)
H2_PATTERN = re.compile(r"^## (.+?):?\s*$", re.MULTILINE)


def load_schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_section(name: str) -> str:
    return name.strip().rstrip(":")


def parse_body(content: str) -> tuple[str, list[str]]:
    h1_matches = H1_PATTERN.findall(content)
    h2_sections = [normalize_section(s) for s in H2_PATTERN.findall(content)]
    title = normalize_section(h1_matches[0]) if h1_matches else ""
    return title, h2_sections


def validate_entry(path: Path, schema: dict) -> list[str]:
    errors: list[str] = []
    post = frontmatter.load(path)
    meta = post.metadata

    if not meta:
        errors.append(f"{path.name}: YAML-Frontmatter fehlt")
        return errors

    for field in schema["required_frontmatter"]:
        if field not in meta or not str(meta[field]).strip():
            errors.append(f"{path.name}: Pflichtfeld '{field}' fehlt oder ist leer")

    title, sections = parse_body(post.content)
    h1_count = len(H1_PATTERN.findall(post.content))
    if h1_count != 1:
        errors.append(f"{path.name}: Genau eine Hauptüberschrift '# Begriff' erforderlich (gefunden: {h1_count})")
    elif not title:
        errors.append(f"{path.name}: Hauptüberschrift '# Begriff' ist leer")

    if schema.get("required_title", {}).get("must_match_frontmatter") and meta.get("begriff"):
        if title != str(meta["begriff"]).strip():
            errors.append(
                f"{path.name}: '# {title}' stimmt nicht mit Frontmatter begriff '{meta['begriff']}' überein"
            )

    for section in schema["required_body_sections"]:
        if section not in sections:
            errors.append(f"{path.name}: Abschnitt '## {section}' fehlt")

    if meta.get("bild"):
        bild = str(meta["bild"]).strip()
        allowed = schema.get("image_convention", {}).get("allowed_extensions", ["png"])
        ext = Path(bild).suffix.lstrip(".").lower()
        if ext not in allowed:
            errors.append(f"{path.name}: Bild muss {', '.join('.' + e for e in allowed)} sein ({bild})")
        image_path = CONTENT_DIR / bild
        if not image_path.exists():
            errors.append(f"{path.name}: Bild fehlt ({bild})")

    return errors


def main() -> int:
    schema = load_schema()
    md_files = sorted(CONTENT_DIR.glob("*.md"))
    if not md_files:
        print("Keine .md-Dateien in content/woerter/ gefunden.")
        return 1

    all_errors: list[str] = []
    for path in md_files:
        all_errors.extend(validate_entry(path, schema))

    if all_errors:
        print("Validierung fehlgeschlagen:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"OK: {len(md_files)} Einträge validiert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
