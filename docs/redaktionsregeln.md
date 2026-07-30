# Redaktionsregeln

## Festes Muster

Jeder Lexikoneintrag besteht aus **YAML-Frontmatter** und **vier Markdown-Angaben**:

**Frontmatter (Pflicht):**

| Feld | Inhalt |
|---|---|
| `begriff` | Der Begriff (wie in der Hauptüberschrift) |
| `bild` | Dateiname der Illustration (z. B. `bezwingen.webp`) |

**Body:**

| Nr. | Markdown | Inhalt |
|---|---|---|
| 1 | `# Begriff` | Der Begriff als Seitenüberschrift (muss zu `begriff:` passen) |
| 2 | `## Bedeutung` | Erklärung der üblichen Bedeutung |
| 3 | `## Beispiel` | Typisches Zitat oder Beispielsatz |
| 4 | `## Bild im Kopf` | Den Begriff wörtlich nehmen und die Szene ausmalen |

Jeder Eintrag hat **immer ein zugehöriges Bild** — referenziert im Frontmatter, abgelegt in `content/woerter/`.

## Neue Einträge anlegen

1. Datei `content/woerter/{slug}.md` erstellen
2. Illustration in `content/woerter/` ablegen und in Frontmatter als `bild:` eintragen
3. Validierung: `python scripts/validate_content.py`

## Vorlage (Muster: `bezwingen.md`)

```markdown
---
begriff: bezwingen
bild: bezwingen.webp
---

# bezwingen

## Bedeutung

*Kurze Erklärung der üblichen Bedeutung.*

## Beispiel

*„Authentisches Zitat oder Beispielsatz.“*

## Bild im Kopf

Die wörtlich genommene Szene — humorvoll, bildhaft, übertrieben.
```

## Layout (Web & Buch)

- **Überschrift** (`# Begriff`) steht immer allein oben
- **Desktop / Buch:** Illustration neben dem Text (Buch: Doppelseite — Bildseite | Textseite)
- **Mobile:** Illustration unter der Überschrift, vor dem Fließtext

## Formatierung

| Effekt | Syntax |
|---|---|
| Kursiv | `*Text*` |
| Fett | `**Text**` |
| Hauptüberschrift | `# Begriff` |
| Unterüberschrift | `## Bedeutung` / `## Beispiel` / `## Bild im Kopf` |

## Stil

- Humor entsteht durch wörtliches Hinschauen
- „Bild im Kopf“ konsequent wörtlich ausmalen
- Illustration und Text zeigen dieselbe wörtliche Szene
Bedeutung: maximal ein Satz.
Beispielverwendung: ein echter deutscher Beispielsatz.
Bild im Kopf: 100–200 Wörter, in denen die Metapher konsequent als Realität behandelt wird.
Kein Kalauerfeuerwerk. Lieber eine absurde Prämisse mit todernster Logik zu Ende denken.
Die Illustration zeigt genau den Moment, den der Text beschreibt – nicht mehr und nicht weniger.Die "Bild im Kopf"-Texte sollten so wirken, als würden sie von jemandem stammen, der Redewendungen völlig wörtlich nimmt und sich ernsthaft darüber wundert. Der Erzähler macht sich nicht über das Wort lustig, sondern behandelt dessen wörtliche Bedeutung mit der Selbstverständlichkeit eines Sprachwissenschaftlers. Genau diese trockene Ernsthaftigkeit macht den Witz aus.

Wort, um das sich der Eintrag dreht: immer GROSS.
Besonders absurde Schlüsselbegriffe: ebenfalls GROSS.
Der restliche Text bleibt nüchtern und sachlich.

Dadurch bekommen die Seiten einen ganz eigenen Wiedererkennungswert – fast wie kleine linguistische Gutachten über Wörter, die sich bei näherem Hinsehen als erstaunlich gewalttätig, körperlich oder schlicht absurd entpuppen. Ich glaube, das passt hervorragend zu deinem Konzept.
