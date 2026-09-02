# andreiadacosta.de

Website von Andreia da Costa — Life & Business Coaching, hnc und Retreats, Düsseldorf.

Entwurf: https://andreia-da-costa.plain-heart-bc55.workers.dev
Eingabemaske: https://andreia-da-costa.plain-heart-bc55.workers.dev/admin

## Was hier liegt

| Datei / Ordner | Wofür |
| --- | --- |
| `inhalte.json` | Der **Ausgangsstand** von allem, was sich regelmäßig ändert: Preise, Retreat-Termine, Stimmen, Kontaktdaten. Gilt, solange über die Eingabemaske nichts gespeichert wurde. |
| `build/_index_body.html` | Die Startseite als Vorlage (Texte, Aufbau). Platzhalter in `{{doppelten Klammern}}` werden aus `inhalte.json` gefüllt. |
| `build/admin.html` | Die Eingabemaske, mit der Andreia die Inhalte pflegt. |
| `build/assets/` | Stylesheet, Logo, Favicon, Bilder. |
| `pages.py` | Die Unterseiten: Finanzcoaching, Impressum, Datenschutz. |
| `build.py` | Der Generator. Baut aus Vorlage + Inhalten die fertigen Seiten nach `site/`. |
| `src/index.js` | Der Worker: liefert die Seiten aus, setzt die gespeicherten Werte ein und bedient die Eingabemaske. |
| `site/` | Das fertige Ergebnis. Genau dieser Ordner wird von Cloudflare ausgeliefert. |

## Wie die Inhalte auf die Seite kommen

Beim Bauen schreibt `build.py` jeden veränderlichen Wert als
`<span data-i="preise.coaching">120 €</span>` in die Seite. Beim Ausliefern
schaut der Worker nach, ob im Speicher (Workers KV) ein neuerer Wert liegt, und
tauscht ihn aus. Liegt dort nichts, bleibt der gebaute Wert stehen.

Das heißt: Die Seite funktioniert auch dann vollständig, wenn Speicher oder
Worker ausfallen — sie zeigt dann einfach den Stand aus `inhalte.json`.

## Seite neu bauen

```bash
python3 build.py
```

Braucht nichts außer Python 3 — keine Abhängigkeiten.

Örtliche Vorschau samt Eingabemaske (Zugangscode in einer Datei `.dev.vars`
als `ADMIN_CODE = "…"` hinterlegen):

```bash
npm install
npm run vorschau
```

## Veröffentlichen

Cloudflare ist mit diesem Repository verbunden: Ein Commit auf `main` wird
automatisch gebaut und veröffentlicht. Die Konfiguration steht in `wrangler.toml`.

## Einstellungen in Cloudflare

- KV-Namespace `andreia_inhalte`, im Worker gebunden als `INHALTE`
- Secret `ADMIN_CODE` — der Zugangscode für die Eingabemaske

## Offen vor dem Livegang

- [ ] `noindex` in `build.py` abschalten (steht aktuell auf jeder Seite)
- [ ] Schriften selbst hosten statt über Google Fonts (DSGVO)
- [ ] Preise, Retreat-Termine und USt-Angabe von Andreia bestätigen lassen
- [ ] Datenschutzerklärung juristisch prüfen lassen
- [ ] Domain andreiadacosta.de auf Cloudflare umziehen — danach die Eingabemaske
      zusätzlich über Cloudflare Access absichern (Anmeldung per E-Mail-Code)
