# Illustrationsprompts für Gemini (Nano Banana / Nano Banana Pro)

Ablauf: Kontext-Prompt einmal an den Anfang eines Gemini-Chats stellen, danach in **derselben Unterhaltung** pro Begriff den jeweiligen Szenen-Prompt schicken. So bleibt der Stil über alle Bilder konsistent, ohne dass Gemini das Projekt "kennen" muss.

---

## 1. Kontext-Prompt (einmal zu Beginn des Chats einfügen)

```
Ich baue an "Wortkino", einem Lexikon komischer deutscher Wörter. Jeder Eintrag nimmt einen
Begriff wörtlich und malt sich aus, was passieren würde, wenn die wörtliche Bedeutung tatsächlich
einträte – trocken, todernst, ohne Kalauer. Zu jedem Begriff brauche ich eine Illustration, die
genau diese wörtlich genommene Szene zeigt.

Ich schicke dir ab jetzt einzelne Begriffe mit ihrer wörtlichen Szene. Bitte generiere pro Begriff
jeweils 3 alternative Bildversionen (unterschiedliche Kompositionen/Perspektiven, gleicher Stil),
damit ich auswählen kann. Halte dich strikt an folgenden Stil, für alle Bilder identisch:

STIL: Moderne, überzeichnete Illustration im "altbackenen" Look – wie eine Sachbuch-/
Lexikon-Illustration aus einem alten Schulbuch oder Brockhaus der 1950er/60er-Jahre, aber mit
zeitgenössischer, sauberer Vektor-/Flat-Illustration ausgeführt statt originalgetreuem Airbrush.
Konkret:
- Gedeckte, leicht vergilbte Retro-Farbpalette (Ocker, Petrol, Rostrot, Cremeweiß, gebrochenes
  Schwarz) – keine grellen, modernen Farben
- Klare, etwas dicke Konturlinien, flächige Farbflächen, kaum Verläufe/Schatten
  (Siebdruck-/Lehrtafel-Optik)
- Figuren und Szenen leicht karikaturhaft überzeichnet – übertriebene Mimik, Proportionen oder
  Bewegung, um die Situation komisch wirken zu lassen, aber nie albern-cartoonhaft
- Bildkomposition frontal/zentriert wie eine alte Lehrtafel oder ein Vintage-Werbeplakat, mit
  ruhigem, leicht texturiertem Hintergrund (Papier-/Rasterstruktur)
- Kein Text/Beschriftung im Bild
- Format: Querformat, geeignet als Doppelseiten-Illustration (Bildseite | Textseite)

Der Humor entsteht ausschließlich aus der wörtlich genommenen Szene selbst – nicht aus dem
Zeichenstil. Zeige exakt den Moment, den ich dir jeweils beschreibe, nicht mehr.
```

## 2. Szenen-Prompt pro Begriff (Vorlage)

Für jeden neuen Eintrag den Abschnitt "Bild im Kopf" in 2–4 Sätze verdichten und so anhängen:

```
Begriff: {Begriff}
Szene: {verdichtete Bild-im-Kopf-Beschreibung, 2–4 Sätze, konkreter Bildmoment}
Bitte 3 alternative Kompositionen in genau diesem Stil.
```

## 3. Ausgearbeitetes Beispiel: "bezwingen"

Kontext-Prompt (oben) zuerst senden, danach:

```
Begriff: bezwingen
Szene: Ein Fußballspiel wird wörtlich zum Ringkampf. Statt Ball zu spielen, haben sich die
Spieler beider Mannschaften ineinander verkeilt und ringen sich gegenseitig unter Zwang zu
Boden. Der Ball liegt vergessen und unbeachtet auf dem Rasen. Im Vordergrund ringt ein Spieler
im Dortmund-Trikot (schwarz-gelb) am Boden, über ihm steht triumphierend ein Spieler im
Fortuna-Düsseldorf-Trikot (rot-weiß), der ihn niederringt.
Bitte 3 alternative Kompositionen in genau diesem Stil:
1. Frontal, zentriert auf das ringende Spielerpaar im Vordergrund, Stadion unscharf im Hintergrund
2. Weiter Kamerawinkel über das ganze Spielfeld, mehrere ringende Spielerpaare verteilt,
   Schiedsrichter ratlos daneben
3. Tiefe Perspektive von unten/Rasenhöhe, ein bezwungener Spieler regungslos am Boden im
   Vordergrund, der siegreiche Spieler triumphierend darüber
```

## 4. Nach der Generierung

1. Bestes Ergebnis auswählen, als `.webp` exportieren
2. In `content/woerter/{slug}.webp` ablegen
3. Dateiname in der Frontmatter des Eintrags unter `bild:` prüfen/eintragen
4. `python scripts/validate_content.py` laufen lassen
