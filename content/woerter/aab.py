#!/usr/bin/env python3
"""Erstellt zu Markdown-Einträgen Comic-Illustrationen im Unterordner bilder/."""

from __future__ import annotations

import base64
import os
from contextlib import ExitStack
from pathlib import Path

from dotenv import load_dotenv
from openai import BadRequestError, OpenAI


# HIER die Dateinamen deiner drei Beispiel-Illustrationen eintragen.
# Die drei PNG-Dateien müssen im gleichen Ordner wie dieses Skript liegen.
BEISPIELBILD_DATEINAMEN = (
    "achsel.png",
    "brustwarze.png",
    "kakadu.png",
)

BILDMODELL = "gpt-image-2"
BILDGROESSE = "1024x1536"
BILDQUALITAET = "high"

# Nur diese Einträge bebildern (Reihenfolge = Bearbeitung).
QUELL_DATEINAMEN = (
    "chlor.md",
    "freilich.md",
    "inbrunst.md",
    "irre.md",
    "lustmolch.md",
    "penetrieren.md",
    "quetschen.md",
    "schluesselbein.md",
    "um-sich-schiesen.md",
)


def bild_erzeugen(
    client: OpenAI,
    markdown_text: str,
    beispielpfade: list[Path],
) -> bytes:
    """Erzeugt synchron eine neue Illustration und gibt ihre PNG-Daten zurück."""
    if len(beispielpfade) != 3:
        raise ValueError("Es werden genau drei Beispielbilder benötigt")

    auftrag = f"""
Erzeuge eine völlig neue Illustration zum folgenden Markdown-Text.

Die drei mitgeschickten Bilder sind ausschließlich Stilreferenzen. Übernimm
ihren allgemeinen einfachen Comicstil, ihre Flächigkeit und ihre zeichnerische
Anmutung. Reproduziere keine konkreten Figuren, Gegenstände, Bildaufteilungen,
Kompositionen oder sonstigen wiedererkennbaren Elemente aus den Referenzbildern.

Die neue Illustration soll:
- den Inhalt des Markdown-Textes witzig und unmittelbar verständlich darstellen,
- gerne unerwartete Kombinationen oder übertriebene
  Größenverhältnisse verwenden, aber KEINE mehrteiligen Collagen, keine Denklblasen usw
- wie eine eigenständige Bildidee wirken und nicht wie eine Variation eines
  Referenzbildes,
- einen einfachen, flächigen Comicstil mit klaren Konturen verwenden,
- auf fotorealistische Details, komplexe Texturen und 3D-Rendering verzichten,
- keinen sichtbaren Text, keine Beschriftungen und keine Sprechblasen enthalten.

<markdown_text>
{markdown_text}
</markdown_text>
""".strip()

    # images.edit() wartet, bis OpenAI das vollständige Bild zurückgegeben hat.
    with ExitStack() as stack:
        beispielbilder = [
            stack.enter_context(pfad.open("rb")) for pfad in beispielpfade
        ]
        antwort = client.images.edit(
            model=BILDMODELL,
            image=beispielbilder,
            prompt=auftrag,
            size=BILDGROESSE,
            quality=BILDQUALITAET,
            output_format="png",
        )

    eintrag = antwort.data[0] if antwort.data else None
    if eintrag is None:
        raise RuntimeError("OpenAI hat keine Bilddaten zurückgegeben")

    if getattr(eintrag, "b64_json", None):
        return base64.b64decode(eintrag.b64_json)

    if getattr(eintrag, "url", None):
        raise RuntimeError(
            "OpenAI lieferte eine Bild-URL statt Base64; "
            "bitte output_format/b64 nutzen oder URL-Download ergänzen"
        )

    raise RuntimeError("OpenAI hat keine Bilddaten zurückgegeben")


def hauptprogramm() -> None:
    """Erzeugt fehlende Illustrationen für die Whitelist in bilder/."""
    skriptordner = Path(__file__).resolve().parent

    # Die .env liegt genau zwei Ordnerebenen über dem Skriptordner.
    env_pfad = skriptordner.parent.parent / ".env"
    load_dotenv(dotenv_path=env_pfad)

    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(f"OPENAI_API_KEY fehlt in {env_pfad}")

    if len(BEISPIELBILD_DATEINAMEN) != 3:
        raise ValueError("BEISPIELBILD_DATEINAMEN muss genau drei Dateinamen enthalten")

    beispielpfade = [
        skriptordner / dateiname for dateiname in BEISPIELBILD_DATEINAMEN
    ]
    for beispielpfad in beispielpfade:
        if not beispielpfad.is_file():
            raise FileNotFoundError(f"Beispielbild nicht gefunden: {beispielpfad}")
        if beispielpfad.suffix.casefold() != ".png":
            raise ValueError(f"Beispielbild ist keine PNG-Datei: {beispielpfad}")

    quelldateien = []
    for dateiname in QUELL_DATEINAMEN:
        quellpfad = skriptordner / dateiname
        if not quellpfad.is_file():
            raise FileNotFoundError(f"Quelldatei nicht gefunden: {quellpfad}")
        quelldateien.append(quellpfad)

    print(f"Bearbeite {len(quelldateien)} ausgewählte Markdown-Dateien.")

    bilderordner = skriptordner / "bilder"
    bilderordner.mkdir(exist_ok=True)
    client = OpenAI(max_retries=2, timeout=600.0)

    erzeugt = 0
    gesamt = len(quelldateien)

    for nummer, quellpfad in enumerate(quelldateien, start=1):
        zielpfad = bilderordner / f"{quellpfad.stem}.png"
        if zielpfad.exists():
            print(
                f"[{nummer}/{gesamt}] Übersprungen: bilder/{zielpfad.name} existiert"
            )
            continue

        markdown_text = quellpfad.read_text(encoding="utf-8").strip()
        if not markdown_text:
            print(f"[{nummer}/{gesamt}] Übersprungen: {quellpfad.name} ist leer")
            continue

        print(f"[{nummer}/{gesamt}] Erzeuge Bild für {quellpfad.name} ...")
        try:
            bilddaten = bild_erzeugen(client, markdown_text, beispielpfade)
        except BadRequestError as exc:
            print(
                f"    Übersprungen (API/Safety): {quellpfad.name} — {exc}"
            )
            continue
        except Exception as exc:  # noqa: BLE001 — Lauf soll bei Einzelfehlern weitergehen
            print(f"    Fehler bei {quellpfad.name}: {exc}")
            continue

        zielpfad.write_bytes(bilddaten)
        erzeugt += 1
        print(f"    Gespeichert: bilder/{zielpfad.name}")

    print(f"Fertig. Neu erzeugt: {erzeugt}.")


if __name__ == "__main__":
    hauptprogramm()
