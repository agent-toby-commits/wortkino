#!/usr/bin/env python3
"""Sucht aktuelle DE-Schlagzeilen zu Wortwört-Begriffen über NewsAPI."""

from __future__ import annotations

import html
import json
import os
import re
import ssl
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi
from dotenv import load_dotenv


SUCHWOERTER = [
    "bezwingt",
    "bezwang",
    "bezwungen",
    "bizarr",
    "bizarre",
    "bizarrer",
    "bizarres",
    "erdrosselt",
    "erdrosselte",
    "händeringend",
    "irre",
    "johlende",
    "johlend",
    "Empörung",
    "obszön",
    "Patzer",
    "patzt",
    "Unheil",
    "vlies",
    "Zwickmühle",
    "um sich schoss",
    "schoss um sich",
    "um sich geschossen",
]

ANZAHL_SCHLAGZEILEN = 3
SUCHZEITRAUM_IN_TAGEN = 30
API_ADRESSE = "https://newsapi.org/v2/everything"
CACHE_SEKUNDEN = 60 * 60

_cache: dict = {"geholt_um": 0.0, "schlagzeilen": []}


def suchanfrage_bauen():
    return " OR ".join(f'"{wort}"' for wort in SUCHWOERTER)


def enthaltene_suchwoerter(titel):
    gefundene_woerter = []

    for wort in SUCHWOERTER:
        muster = rf"(?<!\w){re.escape(wort)}(?!\w)"

        if re.search(muster, titel, flags=re.IGNORECASE):
            gefundene_woerter.append(wort)

    return gefundene_woerter


def artikel_abrufen(api_schluessel):
    fruehestes_datum = (
        datetime.now(timezone.utc) - timedelta(days=SUCHZEITRAUM_IN_TAGEN)
    ).date().isoformat()

    parameter = {
        "q": suchanfrage_bauen(),
        "searchIn": "title",
        "language": "de",
        "from": fruehestes_datum,
        "sortBy": "publishedAt",
        "pageSize": 100,
    }

    anfrage = Request(
        f"{API_ADRESSE}?{urlencode(parameter)}",
        headers={
            "X-Api-Key": api_schluessel,
            "User-Agent": "deutsche-schlagzeilen-suche/1.0",
        },
    )

    with urlopen(
        anfrage,
        timeout=20,
        context=ssl.create_default_context(cafile=certifi.where()),
    ) as antwort:
        return json.load(antwort)["articles"]


def passende_schlagzeilen_ermitteln(artikel):
    passende_schlagzeilen = []
    bereits_gesehene_titel = set()

    for einzelner_artikel in artikel:
        titel = (einzelner_artikel.get("title") or "").strip()
        gefundene_woerter = enthaltene_suchwoerter(titel)
        vergleichstitel = titel.casefold()

        if not titel or not gefundene_woerter:
            continue

        if vergleichstitel in bereits_gesehene_titel:
            continue

        bereits_gesehene_titel.add(vergleichstitel)

        passende_schlagzeilen.append(
            {
                "titel": titel,
                "suchwoerter": gefundene_woerter,
                "quelle": einzelner_artikel.get("source", {}).get("name", "Unbekannt"),
                "veroeffentlicht": einzelner_artikel.get("publishedAt", "Unbekannt"),
                "adresse": einzelner_artikel.get("url", ""),
            }
        )

        if len(passende_schlagzeilen) == ANZAHL_SCHLAGZEILEN:
            break

    return passende_schlagzeilen


def titel_mit_markierten_woertern(titel: str, suchwoerter: list[str]) -> str:
    """HTML-escapten Titel mit markant hervorgehobenen Suchwörtern."""
    if not suchwoerter:
        return html.escape(titel)

    muster = "|".join(
        re.escape(wort) for wort in sorted(suchwoerter, key=len, reverse=True)
    )
    teile: list[str] = []
    ende = 0

    for treffer in re.finditer(
        rf"(?<!\w)({muster})(?!\w)", titel, flags=re.IGNORECASE
    ):
        teile.append(html.escape(titel[ende : treffer.start()]))
        teile.append(
            f'<strong class="schlagzeile-wort">'
            f"{html.escape(treffer.group(1))}"
            f"</strong>"
        )
        ende = treffer.end()

    teile.append(html.escape(titel[ende:]))
    return "".join(teile)


def _env_laden() -> None:
    env_pfad = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_pfad)


def schlagzeilen_laden(*, cache_nutzen: bool = True) -> list[dict]:
    """Holt bis zu drei passende Schlagzeilen (mit Stunden-Cache)."""
    jetzt = time.time()
    if (
        cache_nutzen
        and _cache["schlagzeilen"]
        and jetzt - _cache["geholt_um"] < CACHE_SEKUNDEN
    ):
        return list(_cache["schlagzeilen"])

    _env_laden()
    api_schluessel = os.getenv("NEWSAPI_SCHLUESSEL")
    if not api_schluessel:
        return list(_cache["schlagzeilen"])

    try:
        artikel = artikel_abrufen(api_schluessel)
        schlagzeilen = passende_schlagzeilen_ermitteln(artikel)
        _cache["schlagzeilen"] = schlagzeilen
        _cache["geholt_um"] = jetzt
        return list(schlagzeilen)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, KeyError, OSError):
        return list(_cache["schlagzeilen"])


def schlagzeilen_ausgeben(schlagzeilen):
    if not schlagzeilen:
        print(
            f"Keine passende Schlagzeile aus den letzten "
            f"{SUCHZEITRAUM_IN_TAGEN} Tagen gefunden."
        )
        return

    for nummer, schlagzeile in enumerate(schlagzeilen, start=1):
        print(f"{nummer}. {schlagzeile['titel']}")
        print(f"   Treffer: {', '.join(schlagzeile['suchwoerter'])}")
        print(f"   Quelle: {schlagzeile['quelle']}")
        print(f"   Datum: {schlagzeile['veroeffentlicht']}")
        print(f"   Link: {schlagzeile['adresse']}")
        print()

    if len(schlagzeilen) < ANZAHL_SCHLAGZEILEN:
        print(
            f"Es wurden nur {len(schlagzeilen)} statt "
            f"{ANZAHL_SCHLAGZEILEN} passenden Schlagzeilen gefunden."
        )


def hauptprogramm():
    _env_laden()
    api_schluessel = os.getenv("NEWSAPI_SCHLUESSEL")

    if not api_schluessel:
        env_pfad = Path(__file__).resolve().parent.parent / ".env"
        raise SystemExit(
            "Die Umgebungsvariable NEWSAPI_SCHLUESSEL fehlt.\n"
            f"Trage sie in {env_pfad} ein oder setze:\n"
            "export NEWSAPI_SCHLUESSEL='DEIN_API_SCHLUESSEL'"
        )

    try:
        artikel = artikel_abrufen(api_schluessel)
        schlagzeilen = passende_schlagzeilen_ermitteln(artikel)
        schlagzeilen_ausgeben(schlagzeilen)
    except HTTPError as fehler:
        fehlertext = fehler.read().decode("utf-8", errors="replace")
        raise SystemExit(
            f"NewsAPI antwortete mit HTTP {fehler.code}: {fehlertext}"
        ) from fehler
    except URLError as fehler:
        raise SystemExit(f"Die NewsAPI ist nicht erreichbar: {fehler.reason}") from fehler


if __name__ == "__main__":
    hauptprogramm()
