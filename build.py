#!/usr/bin/env python3
"""Baut die Website von Andreia da Costa aus Vorlagen + Inhalten."""
import re, os, base64, shutil, json

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, 'build')
OUT = os.path.join(ROOT, 'site')

LOGO = open(os.path.join(BUILD, 'assets', 'logo.svg')).read().strip()

# ---------------------------------------------------------------------------
# Inhalte: alles, was sich regelmäßig ändert, steht in inhalte.json.
# Später schreibt die Eingabemaske genau in diese Datei.
# ---------------------------------------------------------------------------
INHALTE = json.load(open(os.path.join(ROOT, 'inhalte.json'), encoding='utf-8'))


def esc(t):
    return (str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def retreats_html():
    out = []
    for r in INHALTE['retreats']:
        preis = f' <span class="tbd" title="Beispielpreis">{esc(r["preis"])}</span>' if r.get('preis') else ''
        out.append(
            '      <li>\n'
            f'        <span class="when tbd" title="Platzhalter — echter Termin fehlt noch">{esc(r["monat"])}</span>\n'
            f'        <span class="where">{esc(r["ort"])}</span>\n'
            f'        <span class="desc">{esc(r["text"])}{preis}</span>\n'
            '        <a class="dlink" href="#kontakt">Auf die Liste</a>\n'
            '      </li>')
    return '\n'.join(out)


def pakete_html():
    out = []
    for p in INHALTE['pakete']:
        preis = f'<span class="preis">{esc(p["preis"])}</span>' if p.get('preis') else ''
        out.append(
            '      <li>\n'
            f'        <span class="was">{esc(p["name"])}</span>\n'
            f'        <span class="umfang">{esc(p["umfang"])}</span>\n'
            f'        <span class="desc">{esc(p["text"])}</span>\n'
            f'        {preis}\n'
            '      </li>')
    return '\n'.join(out)


def stimmen_klein_html():
    out = []
    for q in INHALTE['stimmen']['klein']:
        out.append(
            '      <div class="quote">\n'
            f'        <p>„{esc(q["zitat"])}"</p>\n'
            f'        <cite>{esc(q["name"])}</cite>\n'
            '      </div>')
    return '\n'.join(out)


ALIAS = {'bewertung': 'stimmen.bewertung', 'anzahl': 'stimmen.anzahl'}


def wert(pfad):
    node = INHALTE
    for teil in ALIAS.get(pfad, pfad).split('.'):
        if not isinstance(node, dict) or teil not in node:
            raise KeyError('inhalte.json kennt "%s" nicht' % pfad)
        node = node[teil]
    return node


def fill(html):
    """Setzt die Werte aus inhalte.json ein.

    {{pfad}}   → <span data-i="pfad">Wert</span>  (zur Laufzeit austauschbar)
    {{=pfad}}  → nackter Wert (steht in einem Attribut)
    """
    html = html.replace('{{RETREATS}}', retreats_html())
    html = html.replace('{{PAKETE}}', pakete_html())
    html = html.replace('{{STIMMEN_KLEIN}}', stimmen_klein_html())
    html = re.sub(r'\{\{=([a-z_]+(?:\.[a-z_]+)*)\}\}',
                  lambda m: esc(wert(m.group(1))), html)
    return re.sub(r'\{\{([a-z_]+(?:\.[a-z_]+)*)\}\}',
                  lambda m: '<span data-i="%s">%s</span>' % (
                      ALIAS.get(m.group(1), m.group(1)), esc(wert(m.group(1)))),
                  html)

body = open(os.path.join(BUILD, '_index_body.html'), encoding='utf-8').read()
# Portraitfoto: liegt vorerst noch auf dem Wix-CDN, bis die Originaldatei da ist.
WIX = 'https://static.wixstatic.com/media/a4ebd9_bc7e6a4cbae74e899b4db8d6202b84c5~mv2.jpg'
HERO_IMG = WIX + '/v1/fill/w_900,h_1125,al_c,q_85/andreia-da-costa.jpg'
ABOUT_IMG = WIX + '/v1/fill/w_760,h_950,al_t,q_85/andreia-da-costa.jpg'
body = body.replace('{{IMG_HERO}}', HERO_IMG).replace('{{IMG_ABOUT}}', ABOUT_IMG)

NAV = re.search(r'(<nav class="site">.*?</nav>)', body, re.S).group(1)
FOOTER = re.search(r'(<footer>.*?</footer>)', body, re.S).group(1)
MAIN = body.split('</nav>', 1)[1].split('<footer>', 1)[0]
# Der Teaser auf der Startseite führt auf die Unterseite, nicht auf sich selbst.
MAIN = MAIN.replace('<a class="more" href="#finanzen">', '<a class="more" href="/finanzcoaching.html">')
# Listen, die die Eingabemaske komplett austauschen darf
MAIN = MAIN.replace('<ul class="dates">', '<ul class="dates" data-i-list="retreats">')
MAIN = MAIN.replace('<ul class="pakete">', '<ul class="pakete" data-i-list="pakete">')
MAIN = MAIN.replace('<div class="quotes-small">', '<div class="quotes-small" data-i-list="stimmen">')


def nav_for(page):
    """Navigation mit absoluten Zielen, damit sie auf Unterseiten funktioniert."""
    n = NAV
    if page != 'index':
        for anchor in ('fuerwen', 'angebot', 'retreats', 'ueber', 'ablauf', 'stimmen', 'kontakt'):
            n = n.replace(f'href="#{anchor}"', f'href="/#{anchor}"')
        n = n.replace('href="#finanzen"', 'href="/finanzcoaching.html"')
        n = n.replace('class="brand" href="#"', 'class="brand" href="/"')
    else:
        n = n.replace('href="#finanzen"', 'href="/finanzcoaching.html"')
    return n


def footer_for(page):
    f = FOOTER
    f = f.replace('<a href="#kontakt">Impressum</a>', '<a href="/impressum.html">Impressum</a>')
    f = f.replace('<a href="#kontakt">Datenschutz</a>', '<a href="/datenschutz.html">Datenschutz</a>')
    f = f.replace('<br>\n          <a href="#kontakt">AGB</a>', '')
    f = f.replace('<a href="#kontakt">{{kontakt.email}}</a>',
                  '<a href="mailto:{{=kontakt.email}}">{{kontakt.email}}</a>')
    f = f.replace('<a href="#kontakt">{{kontakt.telefon_anzeige}}</a>',
                  '<a href="tel:{{=kontakt.telefon_link}}">{{kontakt.telefon_anzeige}}</a>')
    f = f.replace('<a href="#kontakt">Instagram</a>',
                  '<a href="{{=kontakt.instagram}}" rel="noopener">Instagram</a>')
    if page != 'index':
        f = f.replace('src="assets/', 'src="/assets/')
    return f


def page(slug, title, description, content, noindex=True):
    robots = '\n<meta name="robots" content="noindex, nofollow">' if noindex else ''
    assets = 'assets' if slug == 'index' else '/assets'
    nav = nav_for(slug)
    if slug != 'index':
        nav = nav.replace('src="assets/', 'src="/assets/')
    html = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">{robots}
<link rel="icon" href="{assets}/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,200;0,6..72,300;0,6..72,400;1,6..72,300&family=Instrument+Sans:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{assets}/style.css?v=2">
</head>
<body>
<div class="draftbar">
  <div class="wrap">
    <span><strong>Entwurf</strong> — so könnte deine neue Seite aussehen.</span>
    <span>Termine und Preise sind Beispielwerte.</span>
  </div>
</div>
{nav}
{content}
{footer_for(slug)}
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
    html = fill(html)
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, slug + '.html'), 'w', encoding='utf-8').write(html)
    return html


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

    from pages import PAGES
    page('index', 'Andreia da Costa — Authentisch leben, klar handeln',
         'Life &amp; Business Coaching, hnc und Retreats in Düsseldorf. Ein Raum, in dem du gesehen wirst.',
         MAIN)
    for slug, (title, desc, content) in PAGES.items():
        page(slug, title, desc, content)
    print('gebaut:', sorted(os.listdir(OUT)))
