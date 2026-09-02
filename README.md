# andreiadacosta.de

Website von Andreia da Costa — Life & Business Coaching, hnc und Retreats, Düsseldorf.

## Was hier liegt

| Datei / Ordner | Wofür |
| --- | --- |
| `inhalte.json` | **Alles, was sich regelmäßig ändert**: Preise, Retreat-Termine, Stimmen, Kontaktdaten. Später schreibt die Eingabemaske genau in diese Datei. |
| `build/_index_body.html` | Die Startseite als Vorlage (Texte, Aufbau). Platzhalter in `{{doppelten Klammern}}` werden aus `inhalte.json` gefüllt. |
| `build/assets/` | Stylesheet, Logo, Favicon, Bilder. |
| `pages.py` | Die Unterseiten: Finanzcoaching, Impressum, Datenschutz. |
| `build.py` | Der Generator. Baut aus Vorlage + Inhalten die fertigen Seiten nach `site/`. |
| `site/` | Das fertige Ergebnis. Genau dieser Ordner wird von Cloudflare ausgeliefert. |

## Seite neu bauen

```bash
python3 build.py
```

Braucht nichts außer Python 3 — keine Abhängigkeiten.

## Veröffentlichen

Cloudflare ist mit diesem Repository verbunden: Ein Commit auf `main` wird
automatisch gebaut und veröffentlicht. Die Konfiguration steht in `wrangler.toml`.

## Offen vor dem Livegang

- [ ] `noindex` in `build.py` abschalten (steht aktuell auf jeder Seite)
- [ ] Schriften selbst hosten statt über Google Fonts (DSGVO)
- [ ] Preise, Retreat-Termine und USt-Angabe von Andreia bestätigen lassen
- [ ] Datenschutzerklärung juristisch prüfen lassen
- [ ] Domain andreiadacosta.de auf Cloudflare umziehen
