#!/usr/bin/env python3
"""Baut die Website von Andreia da Costa aus Vorlagen + Inhalten.

Die Seite gibt es in drei Sprachen:
  site/            deutsch  (Ausgangssprache, enthält auch Impressum und Datenschutz)
  site/en/         englisch
  site/pt/         portugiesisch

Deutsch ist die Quelle. Für Englisch und Portugiesisch liegen in
build/sprache-en.json und build/sprache-pt.json zwei Wörterbücher:
"texte" ersetzt Stellen in den Vorlagen, "werte" ersetzt
die Angaben aus inhalte.json. Was dort nicht steht, bleibt deutsch — deshalb
meldet der Bau am Ende, wenn eine Übersetzung fehlt.
"""
import re, os, base64, shutil, json, copy

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, 'build')
OUT = os.path.join(ROOT, 'site')

LOGO = open(os.path.join(BUILD, 'assets', 'logo.svg')).read().strip()

# ---------------------------------------------------------------------------
# Inhalte: alles, was sich regelmäßig ändert, steht in inhalte.json.
# Später schreibt die Eingabemaske genau in diese Datei.
# ---------------------------------------------------------------------------
INHALTE = json.load(open(os.path.join(ROOT, 'inhalte.json'), encoding='utf-8'))

# ---------------------------------------------------------------------------
# Sprachen
# ---------------------------------------------------------------------------
SPRACHEN = ['de', 'en', 'pt']
KUERZEL = {'de': 'DE', 'en': 'EN', 'pt': 'PT'}
# Unterseiten, die es nur auf Deutsch gibt (Impressum und Datenschutz bleiben
# in der Sprache, in der sie rechtlich gelten).
NUR_DEUTSCH = ('impressum', 'datenschutz')

FEHLT = []


def lade_sprache(code):
    if code == 'de':
        return {'code': 'de', 'name': 'Deutsch', 'texte': {}, 'werte': {}, 'seiten': {}}
    return json.load(open(os.path.join(BUILD, 'sprache-' + code + '.json'), encoding='utf-8'))


def uebersetze(text, spr):
    """Ersetzt die deutschen Stellen durch die Übersetzungen der Sprache."""
    if not spr['texte']:
        return text
    for de in sorted(spr['texte'], key=len, reverse=True):
        text = text.replace(de, spr['texte'][de])
    return text


def inhalte_fuer(spr):
    """inhalte.json in der jeweiligen Sprache."""
    if not spr['werte']:
        return INHALTE
    karte = spr['werte']

    def um(o):
        if isinstance(o, dict):
            return {k: um(v) for k, v in o.items()}
        if isinstance(o, list):
            return [um(v) for v in o]
        if isinstance(o, str):
            if o in karte:
                return karte[o]
            if re.search(r'[A-Za-zÄÖÜäöüß]{4,}', o) and not o.startswith('http'):
                FEHLT.append((spr['code'], o[:70]))
            return o
        return o

    return um(copy.deepcopy(INHALTE))


def esc(t):
    return (str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def retreats_html(inhalte):
    out = []
    for r in inhalte['retreats']:
        preis = f' <span class="tbd" title="Beispielpreis">{esc(r["preis"])}</span>' if r.get('preis') else ''
        out.append(
            '      <li>\n'
            f'        <span class="when tbd" title="Platzhalter — echter Termin fehlt noch">{esc(r["monat"])}</span>\n'
            f'        <span class="where">{esc(r["ort"])}</span>\n'
            f'        <span class="desc">{esc(r["text"])}{preis}</span>\n'
            '        <a class="dlink" href="#kontakt">Auf die Liste</a>\n'
            '      </li>')
    return '\n'.join(out)


def pakete_html(inhalte):
    out = []
    for p in inhalte['pakete']:
        preis = f'<span class="preis">{esc(p["preis"])}</span>' if p.get('preis') else ''
        out.append(
            '      <li>\n'
            f'        <span class="was">{esc(p["name"])}</span>\n'
            f'        <span class="umfang">{esc(p["umfang"])}</span>\n'
            f'        <span class="desc">{esc(p["text"])}</span>\n'
            f'        {preis}\n'
            '      </li>')
    return '\n'.join(out)


def stimmen_klein_html(inhalte, zitat=('„', '"')):
    auf, zu = zitat
    out = []
    for q in inhalte['stimmen']['klein']:
        out.append(
            '      <div class="quote">\n'
            f'        <p>{auf}{esc(q["zitat"])}{zu}</p>\n'
            f'        <cite>{esc(q["name"])}</cite>\n'
            '      </div>')
    return '\n'.join(out)


ALIAS = {'bewertung': 'stimmen.bewertung', 'anzahl': 'stimmen.anzahl'}


def wert(pfad, inhalte):
    node = inhalte
    for teil in ALIAS.get(pfad, pfad).split('.'):
        if not isinstance(node, dict) or teil not in node:
            raise KeyError('inhalte.json kennt "%s" nicht' % pfad)
        node = node[teil]
    return node


def fill(html, inhalte, zitat=('„', '"')):
    """Setzt die Werte aus inhalte.json ein.

    {{pfad}}   → <span data-i="pfad">Wert</span>  (zur Laufzeit austauschbar)
    {{=pfad}}  → nackter Wert (steht in einem Attribut)
    """
    html = html.replace('{{RETREATS}}', retreats_html(inhalte))
    html = html.replace('{{PAKETE}}', pakete_html(inhalte))
    html = html.replace('{{STIMMEN_KLEIN}}', stimmen_klein_html(inhalte, zitat))
    html = re.sub(r'\{\{=([a-z_]+(?:\.[a-z_]+)*)\}\}',
                  lambda m: esc(wert(m.group(1), inhalte)), html)
    return re.sub(r'\{\{([a-z_]+(?:\.[a-z_]+)*)\}\}',
                  lambda m: '<span data-i="%s">%s</span>' % (
                      ALIAS.get(m.group(1), m.group(1)), esc(wert(m.group(1), inhalte))),
                  html)


body = open(os.path.join(BUILD, '_index_body.html'), encoding='utf-8').read()
# Portraitfotos liegen jetzt im Repo (build/assets), nicht mehr auf dem Wix-CDN.
HERO_IMG = '{{ASSETS}}/hero.jpg'
ABOUT_IMG = '{{ASSETS}}/about.jpg'
body = body.replace('{{IMG_HERO}}', HERO_IMG).replace('{{IMG_ABOUT}}', ABOUT_IMG)

NAV = re.search(r'(<nav class="site">.*?</nav>)', body, re.S).group(1)
FOOTER = re.search(r'(<footer>.*?</footer>)', body, re.S).group(1)
MAIN = body.split('</nav>', 1)[1].split('<footer>', 1)[0]
# Der Teaser auf der Startseite führt auf die Unterseite, nicht auf sich selbst.
MAIN = MAIN.replace('<a class="more" href="#finanzen">', '<a class="more" href="finanzcoaching.html">')
# Listen, die die Eingabemaske komplett austauschen darf
MAIN = MAIN.replace('<ul class="pakete">', '<ul class="pakete" data-i-list="pakete">')
MAIN = MAIN.replace('<div class="quotes-small">', '<div class="quotes-small" data-i-list="stimmen">')

# Die Sprachwahl in der Vorlage ist nur ein Platzhalter und wird je Seite neu
# gebaut. Hier merken wir uns, wie sie in der Vorlage aussieht.
LANGS_ALT = re.search(r'<span class="langs".*?</span>\s*</span>', NAV, re.S).group(0)


def langs_html(code, slug):
    """Sprachwahl für eine bestimmte Seite in einer bestimmten Sprache."""
    # Impressum und Datenschutz gibt es nur deutsch; von dort führt der
    # Sprachwechsel auf die Startseite der anderen Sprache.
    seite = slug if slug not in NUR_DEUTSCH else 'index'
    teile = []
    for z in SPRACHEN:
        if z == code:
            teile.append(f'<a class="on" aria-current="true">{KUERZEL[z]}</a>')
            continue
        if code == 'de':
            ziel = f'{z}/{seite}.html'
        elif z == 'de':
            ziel = f'../{seite}.html'
        else:
            ziel = f'../{z}/{seite}.html'
        teile.append(f'<a href="{ziel}" hreflang="{z}">{KUERZEL[z]}</a>')
    return '<span class="langs">' + ''.join(teile) + '</span>'


def nav_for(slug, code):
    """Navigation mit relativen Zielen — alle Seiten liegen nebeneinander.

    Relativ statt absolut, damit die Seite unter jeder Adresse funktioniert:
    eigene Domain, Testadresse in einem Unterordner, örtliche Vorschau.
    """
    n = NAV
    if slug != 'index':
        for anchor in ('fuerwen', 'angebot', 'retreats', 'ueber', 'ablauf', 'stimmen', 'kontakt'):
            n = n.replace(f'href="#{anchor}"', f'href="index.html#{anchor}"')
        n = n.replace('href="#finanzen"', 'href="finanzcoaching.html"')
        n = n.replace('class="brand" href="#"', 'class="brand" href="index.html"')
    else:
        n = n.replace('href="#finanzen"', 'href="finanzcoaching.html"')
    return n.replace(LANGS_ALT, langs_html(code, slug))


def footer_for(code):
    f = FOOTER
    # Impressum und Datenschutz liegen immer im deutschen Hauptverzeichnis.
    hoch = '' if code == 'de' else '../'
    f = f.replace('<a href="#kontakt">Impressum</a>', f'<a href="{hoch}impressum.html">Impressum</a>')
    f = f.replace('<a href="#kontakt">Datenschutz</a>', f'<a href="{hoch}datenschutz.html">Datenschutz</a>')
    f = f.replace('<br>\n          <a href="#kontakt">AGB</a>', '')
    f = f.replace('<a href="#kontakt">{{kontakt.email}}</a>',
                  '<a href="mailto:{{=kontakt.email}}">{{kontakt.email}}</a>')
    f = f.replace('<a href="#kontakt">{{kontakt.telefon_anzeige}}</a>',
                  '<a href="tel:{{=kontakt.telefon_link}}">{{kontakt.telefon_anzeige}}</a>')
    f = f.replace('<a href="#kontakt">Instagram</a>',
                  '<a href="{{=kontakt.instagram}}" rel="noopener">Instagram</a>')
    return f


def alternates(slug):
    """Hinweis an Suchmaschinen, in welchen Sprachen es die Seite gibt."""
    if slug in NUR_DEUTSCH:
        return ''
    zeilen = []
    for z in SPRACHEN:
        pfad = f'{slug}.html' if z == 'de' else f'{z}/{slug}.html'
        zeilen.append(f'<link rel="alternate" hreflang="{z}" href="https://andreiadacosta.de/{pfad}">')
    zeilen.append(f'<link rel="alternate" hreflang="x-default" href="https://andreiadacosta.de/{slug}.html">')
    return '\n' + '\n'.join(zeilen)


def page(slug, titel, beschreibung, inhalt, code, spr, ziel_ordner):
    assets = 'assets' if code == 'de' else '../assets'
    nav = uebersetze(nav_for(slug, code), spr)
    if code != 'de':
        # Der Hinweis im Kontaktformular führt auf die deutsche Datenschutzseite.
        inhalt = inhalt.replace('href="datenschutz.html"', 'href="../datenschutz.html"')
    inhalt = uebersetze(inhalt, spr)
    fuss = uebersetze(footer_for(code), spr)
    html = f'''<!doctype html>
<html lang="{code}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titel}</title>
<meta name="description" content="{beschreibung}">{alternates(slug)}
<link rel="icon" href="{assets}/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{assets}/fonts/newsreader-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{assets}/fonts/instrument-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{assets}/style.css?v=4">
</head>
<body>
{nav}
{inhalt}
{fuss}
<script>
(function(){{
  var els = document.querySelectorAll('.reveal');
  if(!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches){{
    els.forEach(function(e){{e.classList.add('in');}}); return;
  }}
  var io = new IntersectionObserver(function(es){{
    es.forEach(function(e){{ if(e.isIntersecting){{ e.target.classList.add('in'); io.unobserve(e.target); }} }});
  }},{{threshold:0.12}});
  els.forEach(function(e){{io.observe(e);}});
}})();
</script>
</body>
</html>
'''
    html = html.replace('{{ASSETS}}', assets)
    html = fill(html, inhalte_fuer(spr), tuple(spr.get('zitat', ('„', '"'))))
    os.makedirs(ziel_ordner, exist_ok=True)
    open(os.path.join(ziel_ordner, slug + '.html'), 'w', encoding='utf-8').write(html)


def baue_sprache(code):
    from pages import PAGES
    spr = lade_sprache(code)
    ziel = OUT if code == 'de' else os.path.join(OUT, code)

    t = spr.get('seiten', {}).get('index', {})
    page('index',
         t.get('titel', 'Andreia da Costa — Authentisch leben, klar handeln'),
         t.get('beschreibung', 'Life &amp; Business Coaching, hnc und Retreats in Düsseldorf. Ein Raum, in dem du gesehen wirst.'),
         MAIN, code, spr, ziel)

    for slug, (titel, beschreibung, inhalt) in PAGES.items():
        if code != 'de' and slug in NUR_DEUTSCH:
            continue
        t = spr.get('seiten', {}).get(slug, {})
        page(slug, t.get('titel', titel), t.get('beschreibung', beschreibung),
             inhalt, code, spr, ziel)
    return ziel


if __name__ == '__main__':
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(BUILD, 'assets'), os.path.join(OUT, 'assets'))

    # Ausgangsstand für die Eingabemaske: greift, solange nichts gespeichert wurde
    shutil.copyfile(os.path.join(ROOT, 'inhalte.json'),
                    os.path.join(OUT, '_inhalte.json'))
    # Eingabemaske unter /admin
    os.makedirs(os.path.join(OUT, 'admin'))
    shutil.copyfile(os.path.join(BUILD, 'admin.html'),
                    os.path.join(OUT, 'admin', 'index.html'))

    for code in SPRACHEN:
        baue_sprache(code)

    for code, offen in sorted(set(FEHLT)):
        print('  ohne Übersetzung (%s): %s' % (code, offen))
    print('gebaut:', sorted(os.listdir(OUT)))
