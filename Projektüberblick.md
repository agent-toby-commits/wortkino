# Wortkino – Projektüberblick

## Konzept
Lexikon komischer deutscher Wörter: Begriffe, die beim wörtlichen Lesen absurde Bilder erzeugen. Kein Kalauer – konsequentes, trocken-ernsthaftes Wörtlichnehmen der Sprache ("Wortkino nimmt die deutsche Sprache beim Wort"). Ziele: Website (Browsen, Chatbot, User-Vorschläge) und späterer Buch-Export aus demselben Content-Bestand.

## Struktur
- `content/woerter/*.md` – Lexikoneinträge (21 Stück aktuell), je mit passendem `.webp`-Bild
- `content/schema.yaml` – verbindliches Schema für Einträge
- `docs/redaktionsregeln.md` – Redaktionsregeln inkl. Stilvorgaben und Vorlage
- `backend/main.py` – FastAPI-Backend, rendert Einträge dynamisch aus Markdown
- `frontend/` – Web-Oberfläche (HTML/CSS/JS)
- `scripts/validate_content.py` – validiert alle Einträge gegen das Schema
- `scripts/buch_export.py` – exportiert Einträge für die Buchfassung nach `output/buch/`
- `.venv/`, `requirements.txt` – Python-Setup (FastAPI, python-frontmatter, markdown, pyyaml)

## Eintrags-Schema (Pflicht)
Frontmatter: `begriff`, `bild` (Dateiname, .webp/.png, liegt in `content/woerter/`)

Body, in dieser Reihenfolge:
1. `# Begriff` – muss exakt zu `begriff:` passen
2. `## Bedeutung` – max. 1 Satz, kursiv
3. `## Beispiel` – echter Beispielsatz, kursiv
4. `## Bild im Kopf` – 100–200 Wörter

## Stilregeln für "Bild im Kopf"
- Metapher konsequent als Realität behandeln, trocken-sachlicher Ton wie ein linguistisches Gutachten
- Kein Witz-Signalisieren, kein Kalauerfeuerwerk – lieber eine absurde Prämisse todernst zu Ende denken
- Schlüsselbegriff (das Wort selbst) sowie besonders absurde Kernbegriffe: GROSSSCHREIBUNG
- Rest des Texts nüchtern
- Illustration zeigt exakt die im Text beschriebene Szene, nicht mehr

## Neuen Eintrag anlegen
1. `content/woerter/{slug}.md` nach Vorlage (`bezwingen.md`) erstellen
2. Passendes Bild in `content/woerter/` ablegen, in Frontmatter referenzieren
3. `python scripts/validate_content.py` ausführen

## Aktueller Wortbestand (21)
achsel, achtgeben, auf-dem-schirm, bezwingen, brustwarze, buergersteig, ehrgeiz, eichel, entgleisen, etwas-stemmen, haenderingend, kakadu, kehlkopf, lead, leitfaden, penetrieren, po, reissverschluss, schmuck, um-sich-schiesen, unheil

## Sonstiges
- `Wortkino Grundkonzept.pdf/.pages` – ursprüngliches Konzeptdokument
- `Mermaid Flowchart.pdf` – vermutlich Architektur-/Prozessdiagramm
- `.github/workflows/` – vorhanden, Inhalt noch nicht geprüft
