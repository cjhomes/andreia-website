/**
 * Worker für andreiadacosta.de
 *
 * Zwei Aufgaben:
 *  1. Die fertigen Seiten ausliefern und dabei die Werte einsetzen, die Andreia
 *     zuletzt über die Eingabemaske gespeichert hat. Ist nichts gespeichert,
 *     bleiben die Werte stehen, die beim Bauen aus inhalte.json kamen.
 *  2. Die Eingabemaske bedienen: anmelden, lesen, speichern, alte Stände zurückholen.
 */

const COOKIE = 'ada_session';
const SCHLUESSEL = 'inhalte';      // aktueller Stand im KV
const VERLAUF = 'verlauf';         // die letzten zehn Stände
const MAX_VERLAUF = 10;
const TAGE_ANGEMELDET = 30;
const ANFRAGEN = 'anfragen';       // eingegangene Kontaktanfragen
const MAX_ANFRAGEN = 300;
const ANFRAGEN_PRO_STUNDE = 5;     // je Absender-IP

// ---------------------------------------------------------------- Hilfsmittel

const esc = (t) => String(t)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function wert(daten, pfad) {
  let node = daten;
  for (const teil of pfad.split('.')) {
    if (node == null || typeof node !== 'object') return undefined;
    node = node[teil];
  }
  return typeof node === 'string' || typeof node === 'number' ? String(node) : undefined;
}

const json = (obj, status = 200, headers = {}) => new Response(
  JSON.stringify(obj),
  { status, headers: { 'content-type': 'application/json; charset=utf-8', ...headers } },
);

// ---------------------------------------------------------------- Inhalte holen

async function gespeicherteInhalte(env) {
  if (!env.INHALTE) return null;
  try {
    const roh = await env.INHALTE.get(SCHLUESSEL);
    return roh ? JSON.parse(roh) : null;
  } catch {
    return null;
  }
}

async function ausgangsstand(env, request) {
  const res = await env.ASSETS.fetch(new URL('/_inhalte.json', request.url));
  return res.ok ? res.json() : null;
}

// ---------------------------------------------------------------- Seiten füllen

class TextSetzer {
  constructor(daten) { this.daten = daten; }
  element(el) {
    const v = wert(this.daten, el.getAttribute('data-i'));
    if (v !== undefined) el.setInnerContent(v);
  }
}

class ListenSetzer {
  constructor(daten) { this.daten = daten; }
  element(el) {
    const art = el.getAttribute('data-i-list');
    if (art === 'retreats' && Array.isArray(this.daten.retreats)) {
      el.setInnerContent(this.daten.retreats.map((r) => {
        const preis = r.preis
          ? ` <span class="tbd" title="Beispielpreis">${esc(r.preis)}</span>` : '';
        return `<li>`
          + `<span class="when tbd" title="Platzhalter — echter Termin fehlt noch">${esc(r.monat)}</span>`
          + `<span class="where">${esc(r.ort)}</span>`
          + `<span class="desc">${esc(r.text)}${preis}</span>`
          + `<a class="dlink" href="#kontakt">Auf die Liste</a>`
          + `</li>`;
      }).join(''), { html: true });
    }
    if (art === 'stimmen' && Array.isArray(this.daten?.stimmen?.klein)) {
      el.setInnerContent(this.daten.stimmen.klein.map((q) => `<div class="quote">`
        + `<p>„${esc(q.zitat)}“</p><cite>${esc(q.name)}</cite></div>`).join(''), { html: true });
    }
  }
}

class LinkSetzer {
  constructor(daten) { this.daten = daten; }
  element(el) {
    const href = el.getAttribute('href') || '';
    const k = this.daten.kontakt || {};
    if (href.startsWith('mailto:') && k.email) {
      const rest = href.includes('?') ? href.slice(href.indexOf('?')) : '';
      el.setAttribute('href', `mailto:${k.email}${rest}`);
    } else if (href.startsWith('tel:') && k.telefon_link) {
      el.setAttribute('href', `tel:${k.telefon_link}`);
    } else if (href.includes('wa.me/') && k.telefon_link) {
      el.setAttribute('href', `https://wa.me/${k.telefon_link.replace(/[^0-9]/g, '')}`);
    } else if (href.includes('instagram.com') && k.instagram) {
      el.setAttribute('href', k.instagram);
    } else if (href.includes('google.com/search') && this.daten?.stimmen?.google_link) {
      el.setAttribute('href', this.daten.stimmen.google_link);
    }
  }
}

// ---------------------------------------------------------------- Anmeldung

const b64url = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf)))
  .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

async function signieren(env, text) {
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(env.ADMIN_CODE),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'],
  );
  return b64url(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(text)));
}

async function tokenBauen(env) {
  const ablauf = Date.now() + TAGE_ANGEMELDET * 86400_000;
  return `${ablauf}.${await signieren(env, String(ablauf))}`;
}

async function angemeldet(request, env) {
  if (!env.ADMIN_CODE) return false;
  const treffer = (request.headers.get('cookie') || '')
    .match(new RegExp(`(?:^|;\\s*)${COOKIE}=([^;]+)`));
  if (!treffer) return false;
  const [ablauf, sig] = decodeURIComponent(treffer[1]).split('.');
  if (!ablauf || !sig || Number(ablauf) < Date.now()) return false;
  return gleich(sig, await signieren(env, ablauf));
}

/** Vergleich ohne Zeitunterschied, damit sich nichts erraten lässt. */
function gleich(a, b) {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

/** Bremst wiederholte Fehlversuche aus. */
async function zuVieleVersuche(env, request) {
  if (!env.INHALTE) return false;
  const ip = request.headers.get('cf-connecting-ip') || 'unbekannt';
  const n = Number(await env.INHALTE.get(`versuche:${ip}`) || 0);
  return n >= 10;
}

async function versuchZaehlen(env, request) {
  if (!env.INHALTE) return;
  const ip = request.headers.get('cf-connecting-ip') || 'unbekannt';
  const n = Number(await env.INHALTE.get(`versuche:${ip}`) || 0) + 1;
  await env.INHALTE.put(`versuche:${ip}`, String(n), { expirationTtl: 900 });
}

// ---------------------------------------------------------------- Prüfung

const TEXT_MAX = 400;
const sauber = (v) => typeof v === 'string' && v.length <= TEXT_MAX;

/** Nimmt nur an, was die Seite auch verwendet — alles andere fliegt raus. */
function pruefen(eingabe) {
  if (!eingabe || typeof eingabe !== 'object') return { fehler: 'Kein gültiger Inhalt.' };
  const p = eingabe.preise || {};
  const k = eingabe.kontakt || {};
  const s = eingabe.stimmen || {};
  const felder = [
    ...Object.values(p), ...Object.values(k),
    s.bewertung, s.anzahl, s.google_link, s?.gross?.zitat, s?.gross?.name,
    eingabe?.impressum?.umsatzsteuer,
  ].filter((v) => v !== undefined);
  if (!felder.every(sauber)) return { fehler: 'Ein Feld ist leer oder zu lang.' };

  const retreats = Array.isArray(eingabe.retreats) ? eingabe.retreats : [];
  if (retreats.length > 12) return { fehler: 'Höchstens zwölf Retreats.' };
  for (const r of retreats) {
    if (![r.monat, r.ort, r.text].every(sauber) || (r.preis && !sauber(r.preis))) {
      return { fehler: 'Ein Retreat-Feld ist leer oder zu lang.' };
    }
  }
  const klein = Array.isArray(s.klein) ? s.klein : [];
  if (klein.length > 8) return { fehler: 'Höchstens acht kurze Stimmen.' };
  for (const q of klein) {
    if (![q.zitat, q.name].every(sauber)) return { fehler: 'Eine Stimme ist leer oder zu lang.' };
  }
  return { ok: true };
}

// ---------------------------------------------------------------- Kontaktanfragen

const MAIL_MUSTER = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

async function anfragenListe(env) {
  try { return JSON.parse((await env.INHALTE?.get(ANFRAGEN)) || '[]'); } catch { return []; }
}

/** Nimmt das Formular von der Startseite entgegen. */
async function anfrageAnnehmen(request, env) {
  if (!env.INHALTE) return json({ fehler: 'Der Speicher ist gerade nicht erreichbar.' }, 503);

  const ip = request.headers.get('cf-connecting-ip') || 'unbekannt';
  const zaehler = `kontakt:${ip}`;
  const bisher = Number((await env.INHALTE.get(zaehler)) || 0);
  if (bisher >= ANFRAGEN_PRO_STUNDE) {
    return json({ fehler: 'Von hier kamen gerade schon einige Anfragen. Bitte später noch einmal probieren.' }, 429);
  }

  const d = await request.json().catch(() => null);
  if (!d || typeof d !== 'object') return json({ fehler: 'Da fehlt etwas.' }, 400);
  // Falle für automatische Einträge: Menschen füllen dieses Feld nie aus.
  if (typeof d.webseite === 'string' && d.webseite.trim()) return json({ ok: true });

  const name = String(d.name || '').trim();
  const email = String(d.email || '').trim();
  const nachricht = String(d.nachricht || '').trim();
  if (name.length < 2 || name.length > 120) return json({ fehler: 'Bitte trag deinen Namen ein.' }, 400);
  if (!MAIL_MUSTER.test(email) || email.length > 200) return json({ fehler: 'Bitte eine gültige E-Mail-Adresse angeben.' }, 400);
  if (nachricht.length < 5 || nachricht.length > 3000) return json({ fehler: 'Bitte schreib ein paar Sätze zu deinem Anliegen.' }, 400);
  if (d.einverstanden !== true) return json({ fehler: 'Ohne dein Einverständnis kann ich die Anfrage nicht speichern.' }, 400);

  const liste = await anfragenListe(env);
  liste.unshift({ id: crypto.randomUUID(), zeit: new Date().toISOString(), name, email, nachricht });
  await env.INHALTE.put(ANFRAGEN, JSON.stringify(liste.slice(0, MAX_ANFRAGEN)));
  await env.INHALTE.put(zaehler, String(bisher + 1), { expirationTtl: 3600 });
  return json({ ok: true });
}

function zeitpunkt(iso) {
  try {
    return new Date(iso).toLocaleString('de-DE', {
      timeZone: 'Europe/Berlin', day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}

/** Posteingang unter /admin/anfragen. */
function anfragenSeite(liste) {
  const eintraege = liste.length ? liste.map((a) => `
    <article class="anfrage" data-id="${esc(a.id)}">
      <div class="kopf"><b>${esc(a.name)}</b><time>${esc(zeitpunkt(a.zeit))}</time></div>
      <p class="mail"><a href="mailto:${esc(a.email)}?subject=Deine%20Anfrage">${esc(a.email)}</a></p>
      <p class="text">${esc(a.nachricht).replace(/\n/g, '<br>')}</p>
      <button type="button" class="weg">Löschen</button>
    </article>`).join('') : '<p class="leer">Noch keine Anfragen.</p>';

  return `<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Anfragen — Andreia da Costa</title>
<style>
  :root{--ground:#FBF7F4;--surface:#FDFAF8;--ink:#4A3A34;--ink-soft:#71605A;--ink-mute:#A2918A;--line:#E7D9D1;--aussen:#A3512B;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--ground);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;}
  .wrap{max-width:760px;margin:0 auto;padding:0 22px;}
  header{border-bottom:1px solid var(--line);background:var(--surface);padding:26px 0;}
  header .wrap{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;}
  h1{font-size:1.3rem;font-weight:600;margin:0;}
  header p{margin:0;color:var(--ink-mute);font-size:.9rem;}
  header .rechts{margin-left:auto;display:flex;gap:14px;}
  a{color:var(--aussen);}
  main{padding:34px 0 80px;}
  .anfrage{background:var(--surface);border:1px solid var(--line);padding:20px 22px;margin-bottom:16px;}
  .kopf{display:flex;justify-content:space-between;gap:14px;align-items:baseline;}
  .kopf b{font-size:1.05rem;}
  time{color:var(--ink-mute);font-size:.84rem;white-space:nowrap;}
  .mail{margin:.3rem 0 .9rem;font-size:.92rem;}
  .text{margin:0;white-space:normal;color:var(--ink-soft);}
  .weg{margin-top:16px;background:none;border:1px solid var(--line);color:var(--ink-mute);font:inherit;font-size:.84rem;padding:7px 14px;cursor:pointer;}
  .weg:hover{border-color:var(--aussen);color:var(--aussen);}
  .leer{color:var(--ink-mute);}
</style>
</head>
<body>
<header><div class="wrap">
  <h1>Anfragen</h1>
  <p>${liste.length} gespeichert</p>
  <span class="rechts"><a href="/admin/">Inhalte pflegen</a><a href="/">Zur Website</a></span>
</div></header>
<main class="wrap">${eintraege}</main>
<script>
document.addEventListener('click', function (e) {
  var k = e.target.closest('.weg');
  if (!k) return;
  var karte = k.closest('.anfrage');
  if (!confirm('Diese Anfrage endgültig löschen?')) return;
  k.disabled = true;
  fetch('/admin/api/anfrage-weg', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ id: karte.dataset.id })
  }).then(function (r) { return r.json(); }).then(function (r) {
    if (r && r.ok) karte.remove(); else { k.disabled = false; alert((r && r.fehler) || 'Hat nicht geklappt.'); }
  }).catch(function () { k.disabled = false; alert('Hat nicht geklappt.'); });
});
</script>
</body>
</html>`;
}

// ---------------------------------------------------------------- API

async function api(request, env, url) {
  const pfad = url.pathname.replace(/^\/admin\/api\/?/, '');
  const post = request.method === 'POST';

  if (pfad === 'anmelden' && post) {
    if (!env.ADMIN_CODE) return json({ fehler: 'Es ist noch kein Zugangscode hinterlegt.' }, 503);
    if (await zuVieleVersuche(env, request)) {
      return json({ fehler: 'Zu viele Versuche. Bitte in einer Viertelstunde erneut probieren.' }, 429);
    }
    const { code } = await request.json().catch(() => ({}));
    if (typeof code !== 'string' || !gleich(code, env.ADMIN_CODE)) {
      await versuchZaehlen(env, request);
      return json({ fehler: 'Der Code stimmt nicht.' }, 401);
    }
    const token = await tokenBauen(env);
    return json({ ok: true }, 200, {
      'set-cookie': `${COOKIE}=${encodeURIComponent(token)}; Path=/; HttpOnly; Secure; `
        + `SameSite=Strict; Max-Age=${TAGE_ANGEMELDET * 86400}`,
    });
  }

  if (pfad === 'abmelden' && post) {
    return json({ ok: true }, 200, {
      'set-cookie': `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0`,
    });
  }

  if (!(await angemeldet(request, env))) return json({ fehler: 'Nicht angemeldet.' }, 401);

  if (pfad === 'inhalte' && request.method === 'GET') {
    const daten = (await gespeicherteInhalte(env)) || (await ausgangsstand(env, request));
    return json({ inhalte: daten, gespeichert: !!(await gespeicherteInhalte(env)) });
  }

  if (pfad === 'inhalte' && post) {
    if (!env.INHALTE) return json({ fehler: 'Der Speicher ist noch nicht verbunden.' }, 503);
    const eingabe = await request.json().catch(() => null);
    const p = pruefen(eingabe);
    if (p.fehler) return json({ fehler: p.fehler }, 400);

    const vorher = (await gespeicherteInhalte(env)) || (await ausgangsstand(env, request));
    if (vorher) {
      let verlauf = [];
      try { verlauf = JSON.parse(await env.INHALTE.get(VERLAUF) || '[]'); } catch { /* leer */ }
      verlauf.unshift({ zeit: new Date().toISOString(), inhalte: vorher });
      await env.INHALTE.put(VERLAUF, JSON.stringify(verlauf.slice(0, MAX_VERLAUF)));
    }
    await env.INHALTE.put(SCHLUESSEL, JSON.stringify(eingabe));
    return json({ ok: true });
  }

  if (pfad === 'verlauf' && request.method === 'GET') {
    let verlauf = [];
    try { verlauf = JSON.parse(await env.INHALTE?.get(VERLAUF) || '[]'); } catch { /* leer */ }
    return json({ verlauf: verlauf.map((v, i) => ({ nr: i, zeit: v.zeit })) });
  }

  if (pfad === 'zurueck' && post) {
    const { nr } = await request.json().catch(() => ({}));
    let verlauf = [];
    try { verlauf = JSON.parse(await env.INHALTE?.get(VERLAUF) || '[]'); } catch { /* leer */ }
    const stand = verlauf[nr];
    if (!stand) return json({ fehler: 'Diesen Stand gibt es nicht mehr.' }, 404);
    const vorher = (await gespeicherteInhalte(env)) || (await ausgangsstand(env, request));
    verlauf.unshift({ zeit: new Date().toISOString(), inhalte: vorher });
    await env.INHALTE.put(VERLAUF, JSON.stringify(verlauf.slice(0, MAX_VERLAUF)));
    await env.INHALTE.put(SCHLUESSEL, JSON.stringify(stand.inhalte));
    return json({ ok: true, inhalte: stand.inhalte });
  }

  if (pfad === 'anfrage-weg' && post) {
    const { id } = await request.json().catch(() => ({}));
    const liste = await anfragenListe(env);
    const rest = liste.filter((a) => a.id !== id);
    if (rest.length === liste.length) return json({ fehler: 'Diese Anfrage gibt es nicht mehr.' }, 404);
    await env.INHALTE.put(ANFRAGEN, JSON.stringify(rest));
    return json({ ok: true });
  }

  return json({ fehler: 'Unbekannter Aufruf.' }, 404);
}

// ---------------------------------------------------------------- Einstieg

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/kontakt' && request.method === 'POST') {
      return anfrageAnnehmen(request, env)
        .catch(() => json({ fehler: 'Da ist etwas schiefgelaufen.' }, 500));
    }

    if (url.pathname === '/admin/anfragen' || url.pathname === '/admin/anfragen/') {
      if (!(await angemeldet(request, env))) {
        return Response.redirect(new URL('/admin/', url).toString(), 302);
      }
      return new Response(anfragenSeite(await anfragenListe(env)), {
        headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' },
      });
    }

    if (url.pathname.startsWith('/admin/api')) {
      return api(request, env, url).catch(() => json({ fehler: 'Da ist etwas schiefgelaufen.' }, 500));
    }

    const antwort = await env.ASSETS.fetch(request);
    if (!(antwort.headers.get('content-type') || '').includes('text/html')) return antwort;

    const daten = await gespeicherteInhalte(env);
    if (!daten) return antwort;   // nichts gespeichert: Seite bleibt, wie sie gebaut wurde

    return new HTMLRewriter()
      .on('[data-i]', new TextSetzer(daten))
      .on('[data-i-list]', new ListenSetzer(daten))
      .on('a[href]', new LinkSetzer(daten))
      .transform(antwort);
  },
};
