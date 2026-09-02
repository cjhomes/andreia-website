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

  return json({ fehler: 'Unbekannter Aufruf.' }, 404);
}

// ---------------------------------------------------------------- Einstieg

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

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
