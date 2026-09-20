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
import re, os, base64, shutil, json, copy, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, 'build')
OUT = os.path.join(ROOT, 'site')

LOGO = open(os.path.join(BUILD, 'assets', 'logo.svg')).read().strip()

# ---------------------------------------------------------------------------
# Reichweitenmessung
# CF_TOKEN: Kennung aus Cloudflare Web Analytics (Dashboard > Analytics >
#   Web Analytics > Seite hinzufügen). Solange der Wert leer ist, steht kein
#   Zählskript auf der Seite und die Datenschutzerklärung stimmt trotzdem.
# GSC_TAG: der Inhalt des Bestätigungs-Tags der Google Search Console
#   (Methode "HTML-Tag"). Landet nur auf der deutschen Startseite.
# ---------------------------------------------------------------------------
CF_TOKEN = '52d161530c5040cf802b4d859bafabd1'
GSC_TAG = 'FTQ3ro5cEhTj050kJCkvF6vvBNR89VTQhUp0Cc3ze54'

DOMAIN = 'andreiadacosta.de'
# Kennung von Andreias Google-Unternehmensprofil (Google Maps).
GOOGLE_CID = '14295107461892084681'

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
# Seiten, die es nur in einer einzigen Sprache gibt. Impressum und Datenschutz
# bleiben deutsch; die Seite fuer die portugiesischsprachige Gemeinschaft gibt
# es nur auf Portugiesisch.
NUR_SPRACHE = {'impressum': 'de', 'datenschutz': 'de', 'portugues': 'pt'}


def sprachen_von(slug):
    """In welchen Sprachen es diese Seite gibt."""
    einzeln = NUR_SPRACHE.get(slug)
    return (einzeln,) if einzeln else tuple(SPRACHEN)

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
    seite = slug if slug not in NUR_SPRACHE else 'index'
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
    # Die AGB-Zeile der Vorlage tragt jetzt die Fragenseite — und im
    # Portugiesischen zusaetzlich die Seite fuer die Gemeinschaft.
    zeilen = '<br>\n          <a href="fragen.html">Fragen und Antworten</a>'
    if code == 'pt':
        zeilen += '<br>\n          <a href="portugues.html">Coaching em português</a>'
    f = f.replace('<br>\n          <a href="#kontakt">AGB</a>', zeilen)
    f = f.replace('<a href="#kontakt">{{kontakt.email}}</a>',
                  '<a href="mailto:{{=kontakt.email}}">{{kontakt.email}}</a>')
    f = f.replace('<a href="#kontakt">{{kontakt.telefon_anzeige}}</a>',
                  '<a href="tel:{{=kontakt.telefon_link}}">{{kontakt.telefon_anzeige}}</a>')
    f = f.replace('<a href="#kontakt">Instagram</a>',
                  '<a href="{{=kontakt.instagram}}" rel="noopener">Instagram</a>')
    return f


def alternates(slug):
    """Hinweis an Suchmaschinen, in welchen Sprachen es die Seite gibt."""
    if slug in NUR_SPRACHE:
        return ''
    zeilen = []
    for z in SPRACHEN:
        zeilen.append(f'<link rel="alternate" hreflang="{z}" href="{adresse(slug, z)}">')
    zeilen.append(f'<link rel="alternate" hreflang="x-default" href="{adresse(slug, "de")}">')
    return '\n' + '\n'.join(zeilen)


def adresse(slug, code):
    """Die eine richtige Adresse dieser Seite.

    Die Startseite laeuft unter dem nackten Verzeichnis (/ bzw. /en/), nicht
    unter index.html — sonst kennen Suchmaschinen zwei Adressen fuer dieselbe
    Seite.
    """
    ordner = '' if code == 'de' else code + '/'
    datei = '' if slug == 'index' else slug + '.html'
    return 'https://' + DOMAIN + '/' + ordner + datei


def teilen_html(slug, code, titel, beschreibung):
    """Vorschau beim Teilen — WhatsApp, LinkedIn, Signal, Suchmaschinen."""
    url = adresse(slug, code)
    sprache = {'de': 'de_DE', 'en': 'en_GB', 'pt': 'pt_PT'}[code]
    return f'''
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Andreia da Costa">
<meta property="og:locale" content="{sprache}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{titel}">
<meta property="og:description" content="{beschreibung}">
<meta property="og:image" content="https://{DOMAIN}/assets/teilen.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">'''


def daten_html(slug, code):
    """Strukturierte Angaben für Suchmaschinen und KI-Dienste.

    Bewusst ohne aggregateRating: Google erlaubt selbst ausgespielte
    Bewertungen zum eigenen Betrieb nicht als Rich Snippet.
    """
    if slug != 'index' or code != 'de':
        return ''
    k = INHALTE['kontakt']
    daten = {
        '@context': 'https://schema.org',
        '@type': 'ProfessionalService',
        '@id': 'https://' + DOMAIN + '/#andreia',
        'name': 'Andreia da Costa Jalali — Life & Business Coaching',
        'alternateName': 'Andreia da Costa Coaching',
        'description': ('Life & Business Coaching, hnc (human neuro cybrainetics), '
                        'Finanzcoaching und Retreats in Düsseldorf und online.'),
        'url': 'https://' + DOMAIN + '/',
        'image': 'https://' + DOMAIN + '/assets/hero.jpg',
        'email': k['email'],
        'telephone': k['telefon_anzeige'],
        'address': {'@type': 'PostalAddress', 'streetAddress': k['strasse'],
                    'postalCode': k['ort'].split()[0], 'addressLocality': 'Düsseldorf',
                    'addressRegion': 'NRW', 'addressCountry': 'DE'},
        'areaServed': [{'@type': 'City', 'name': 'Düsseldorf'},
                       {'@type': 'Country', 'name': 'Deutschland'}],
        'availableLanguage': ['de', 'en', 'pt'],
        'sameAs': [k['instagram'], 'https://www.google.com/maps?cid=' + GOOGLE_CID],
        'founder': {'@type': 'Person', 'name': 'Andreia da Costa Jalali',
                    'jobTitle': 'Life & Business Coach', 'url': 'https://' + DOMAIN + '/'},
        'makesOffer': [
            {'@type': 'Offer', 'itemOffered': {'@type': 'Service',
             'name': 'Life & Business Coaching',
             'description': 'Einzelcoaching in Düsseldorf oder online.'}},
            {'@type': 'Offer', 'itemOffered': {'@type': 'Service',
             'name': 'hnc — human neuro cybrainetics',
             'description': 'Manuelle Arbeit am Nervensystem, vor Ort in Düsseldorf.'}},
            {'@type': 'Offer', 'itemOffered': {'@type': 'Service',
             'name': 'Finanzcoaching',
             'description': 'Überblick über die eigenen Finanzen. Keine Anlageberatung.'}},
            {'@type': 'Offer', 'itemOffered': {'@type': 'Service',
             'name': 'Retreats',
             'description': 'Wochenenden in kleiner Gruppe.'}},
        ],
    }
    return ('\n<script type="application/ld+json">'
            + json.dumps(daten, ensure_ascii=False) + '</script>')


def faq_daten(html):
    """FAQPage-Angaben aus der fertigen Fragenseite.

    Wird erst nach dem Uebersetzen und Einsetzen gebaut, damit in den
    Antworten dieselben Preise stehen wie auf der Seite.
    """
    eintraege = []
    for frage, antwort in re.findall(
            r'<div class="f">\s*<h3>(.*?)</h3>\s*<div class="a">(.*?)</div>\s*</div>',
            html, re.S):
        text = re.sub(r'<[^>]+>', ' ', antwort)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        eintraege.append({
            '@type': 'Question',
            'name': re.sub(r'<[^>]+>', '', frage).strip(),
            'acceptedAnswer': {'@type': 'Answer', 'text': text},
        })
    if not eintraege:
        return ''
    daten = {'@context': 'https://schema.org', '@type': 'FAQPage',
             'mainEntity': eintraege}
    return ('<script type="application/ld+json">'
            + json.dumps(daten, ensure_ascii=False) + '</script>')


def messung_html():
    """Cloudflare Web Analytics. Leerer Token = kein Skript auf der Seite."""
    if not CF_TOKEN:
        return ''
    # Genau der Schnipsel, den Cloudflare ausgibt.
    return ('\n<!-- Cloudflare Web Analytics --><script type="module" '
            'src="https://static.cloudflareinsights.com/beacon.min.js" '
            'data-cf-beacon=\'{"token": "' + CF_TOKEN + '"}\'></script>'
            '<!-- End Cloudflare Web Analytics -->')


def gsc_html(slug, code):
    """Bestätigung für die Google Search Console — nur auf der deutschen Startseite."""
    if not GSC_TAG or slug != 'index' or code != 'de':
        return ''
    return '\n<meta name="google-site-verification" content="' + GSC_TAG + '">'


def page(slug, titel, beschreibung, inhalt, code, spr, ziel_ordner):
    from pages import PAGES
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
<meta name="description" content="{beschreibung}">{alternates(slug)}{teilen_html(slug, code, titel, beschreibung)}{gsc_html(slug, code)}{daten_html(slug, code)}
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
</script>{messung_html()}
</body>
</html>
'''
    if 'hnc' not in PAGES:
        # Die hnc-Seite ist (noch) nicht veroeffentlicht — Verweise darauf
        # fuehren dann auf den hnc-Teil der Startseite statt ins Leere.
        html = html.replace('href="hnc.html"', 'href="index.html#angebot"')
    html = html.replace('{{ASSETS}}', assets)
    html = fill(html, inhalte_fuer(spr), tuple(spr.get('zitat', ('„', '"'))))
    if slug == 'fragen':
        html = html.replace('</body>', faq_daten(html) + '\n</body>')
    os.makedirs(ziel_ordner, exist_ok=True)
    open(os.path.join(ziel_ordner, slug + '.html'), 'w', encoding='utf-8').write(html)


def baue_sprache(code):
    from pages import PAGES
    spr = lade_sprache(code)
    ziel = OUT if code == 'de' else os.path.join(OUT, code)

    t = spr.get('seiten', {}).get('index', {})
    page('index',
         t.get('titel', 'Life &amp; Business Coaching in Düsseldorf — Andreia da Costa'),
         t.get('beschreibung', 'Life &amp; Business Coaching in Düsseldorf und online: Einzelcoaching, hnc, Finanzcoaching und Retreats. Erstgespräch kostenlos.'),
         MAIN, code, spr, ziel)

    for slug, (titel, beschreibung, inhalt) in PAGES.items():
        if code not in sprachen_von(slug):
            continue
        t = spr.get('seiten', {}).get(slug, {})
        page(slug, t.get('titel', titel), t.get('beschreibung', beschreibung),
             inhalt, code, spr, ziel)
    return ziel


def schreibe_sitemap():
    """Verzeichnis aller Seiten für Suchmaschinen — mit Sprachverweisen."""
    from pages import PAGES
    slugs = ['index'] + list(PAGES.keys())
    heute = datetime.date.today().isoformat()
    z = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
         'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for slug in slugs:
        sprachen = list(sprachen_von(slug))
        for code in sprachen:
            z.append('  <url>')
            z.append('    <loc>%s</loc>' % adresse(slug, code))
            z.append('    <lastmod>%s</lastmod>' % heute)
            for andere in sprachen:
                z.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>'
                         % (andere, adresse(slug, andere)))
            z.append('  </url>')
    z.append('</urlset>')
    open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(z) + '\n')


def schreibe_robots():
    """Alles freigegeben — auch ausdrücklich für die KI-Dienste."""
    text = """# Alle Suchmaschinen und KI-Dienste dürfen diese Seite lesen.
User-agent: *
Allow: /
Disallow: /admin/

# Ausdrücklich erlaubt, damit Andreia in den Antworten dieser Dienste vorkommt:
User-agent: GPTBot
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: ClaudeBot
User-agent: Claude-SearchBot
User-agent: PerplexityBot
User-agent: Google-Extended
User-agent: Applebot-Extended
User-agent: Bingbot
Allow: /

Sitemap: https://%s/sitemap.xml
""" % DOMAIN
    open(os.path.join(OUT, 'robots.txt'), 'w', encoding='utf-8').write(text)


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

    schreibe_sitemap()
    schreibe_robots()

    for code, offen in sorted(set(FEHLT)):
        print('  ohne Übersetzung (%s): %s' % (code, offen))
    print('gebaut:', sorted(os.listdir(OUT)))
