/* =====================================================================
 * MU-TH-UR // VEILLE AZOTH — interface
 * ---------------------------------------------------------------------
 * Ce fichier tourne dans le navigateur. Il ne lit jamais les flux RSS
 * lui-même (le navigateur l'interdit entre sites : CORS). Il interroge
 * le serveur local veille.py :
 *   GET  /api/feeds[?force=1]  -> articles normalisés + état des sources
 *   GET  /api/crypto           -> cours BTC / XMR / DOGE (CoinGecko)
 *   GET  /api/config           -> sources + état utilisateur
 *   POST /api/state            -> favoris, lus, mots surveillés, dernière visite
 *   POST /api/sources/add|remove|toggle
 *
 * Organisation : 1) état  2) utilitaires  3) règles d'alerte
 *                4) rendu  5) actions  6) effets visuels  7) démarrage
 * ===================================================================== */
'use strict';

/* ---------- 1) ÉTAT -------------------------------------------------- */
const S = {
  items: [],          // tous les articles reçus du serveur
  status: {},         // état de chaque source, indexé par id
  sources: [],        // liste des sources (sources.json)
  fav: {},            // favoris : id -> article complet (survit à la disparition du flux)
  read: new Set(),    // ids des articles lus
  watch: [],          // mots surveillés -> ALERTE (sécurité, matériel pro)
  topics: [],         // mes sujets perso -> badge « POUR TOI »
  prevVisit: 0,       // date de la visite précédente -> détermine les « nouveaux »
  tab: 'Tout',        // onglet actif
  shown: 60,          // pagination simple
  cursor: -1,         // article sélectionné au clavier
  view: [],           // articles actuellement affichés (après filtres)
};

// Onglets, en deux familles. Les catégories des sources (sources.json) doivent
// figurer ici pour avoir leur onglet.
const GROUPS = {
  PRO: ['Alertes', 'Cyber & piratage', 'Systèmes', 'Réseau', 'Homelab', 'Cloud', 'Chiffrement'],
  PERSO: ['Firmwares', 'Maker', 'Musique', 'Photo', 'Rétro & jeux', 'Drones & radio', 'IA', 'Crypto & trading', 'Matos'],
};
const CATS = [...GROUPS.PRO, ...GROUPS.PERSO];

/* ---------- 2) UTILITAIRES ------------------------------------------ */
const $ = s => document.querySelector(s);

/** Échappe le texte venant des flux : on n'injecte jamais du HTML d'un site tiers. */
const esc = s => String(s ?? '').replace(/[&<>"']/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/** N'accepte que des liens http(s) (bloque javascript:, data:, …). */
const safeUrl = u => /^https?:\/\//i.test(u) ? u : '#';

/** Appel JSON au serveur local. */
async function api(path, body) {
  const r = await fetch(path, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || r.statusText);
  return data;
}

/** Met à jour les quatre briques visibles du cockpit. */
async function loadCockpit() {
  try {
    const status = await api('/api/cockpit/status');
    Object.entries(status).forEach(([name, value]) => {
      const el = document.querySelector(`[data-service="${name}"]`);
      if (!el) return;
      el.className = value.online ? 'online' : 'offline';
      const label = value.online ? 'EN LIGNE' : 'EN ATTENTE';
      el.textContent = `${label}${value.mode ? ` · ${value.mode.toUpperCase()}` : ''}`;
      el.title = value.detail || '';
    });
    const trading = $('#tradingModule');
    trading.href = status.trading?.online ? '/quant/' : '#';
    trading.target = status.trading?.online ? '_blank' : '';
    trading.rel = status.trading?.online ? 'noopener noreferrer' : '';
    const ai = $('#aiModule');
    ai.href = status.ai?.workspace_online ? '/ia/' : '#';
    ai.target = status.ai?.workspace_online ? '_blank' : '';
    ai.rel = status.ai?.workspace_online ? 'noopener noreferrer' : '';
  } catch {
    document.querySelectorAll('[data-service]').forEach(el => {
      el.className = 'offline'; el.textContent = 'INDISPONIBLE';
    });
  }
}

/** « il y a 3 h » compact, pour la colonne de gauche. */
function ago(ts) {
  if (!ts) return ['—', ''];
  const m = Math.max(0, (Date.now() / 1000 - ts) / 60);
  if (m < 60) return [`${Math.round(m)}m`, 'minutes'];
  if (m < 1440) return [`${Math.round(m / 60)}h`, 'heures'];
  if (m >= 525600) return [`${Math.floor(m / 525600)}a`, new Date(ts * 1000).getFullYear()];   // plus d'un an
  return [`${Math.round(m / 1440)}j`, new Date(ts * 1000).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })];
}

const fmtEur = n => n == null ? '—' : n.toLocaleString('fr-FR', {
  style: 'currency', currency: 'EUR', maximumFractionDigits: n < 1 ? 4 : n < 100 ? 2 : 0,
});
const pct = n => n == null ? '—' : `${n > 0 ? '▲' : '▼'} ${Math.abs(n).toFixed(2)} %`;

/** Sauvegarde différée de l'état (évite un appel réseau à chaque clic). */
let saveTimer;
function saveState() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => api('/api/state', {
    fav: S.fav, read: [...S.read], watch: S.watch, topics: S.topics,
  }).catch(e => console.warn('sauvegarde', e)), 400);
}

/* ---------- 3) RÈGLES D'ALERTE -------------------------------------- */
// Mots qui signalent un sujet urgent pour un technicien (FR + EN).
// \b = début/fin de mot : sans lui « RCE » se déclencherait dans « source ».
const HOT = /\b(critique|critical|0-?day|zero[- ]?day|exploit(?:é|ée|ed|ation|s)?|activement exploitée?|actively exploited|ransomware|rançongiciel|backdoor|porte dérobée|fuite de données|data breach|wiper|RCE|remote code execution|exécution de code arbitraire|manual intervention|intervention manuelle)\b/i;
// « manual intervention » : les annonces Arch Linux (donc Omarchy) à lire AVANT de mettre à jour.
const CVE = /CVE-\d{4}-\d{4,7}/gi;
const HOT_CATS = new Set(['Alertes', 'Cyber & piratage', 'Systèmes', 'Réseau', 'Homelab', 'Cloud']);
// Vocabulaire « sécurité » : un mot surveillé hors des catégories sécurité ne déclenche
// une alerte que si le titre parle aussi de faille (évite « Proxmox » dans une discussion r/homelab).
const SEC = /\b(vuln\w*|faille|flaw|CVE|patch\w*|correctif|security|sécurité|attaque|attack|hack\w*|pirat\w*|compromi\w*|bypass|exploit\w*)\b/i;
const SEC_CATS = new Set(['Alertes', 'Cyber & piratage']);

/**
 * Cherche un mot-clé comme mot entier (insensible à la casse) :
 * « LoRa » ne doit pas se déclencher dans « Flora », ni « OP-1 » dans « OP-10 ».
 */
const reCache = new Map();
function hasWord(text, word) {
  let re = reCache.get(word);
  if (!re) {
    const w = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    re = new RegExp(`(^|[^\\p{L}\\p{N}])${w}(?=$|[^\\p{L}\\p{N}])`, 'iu');
    reCache.set(word, re);
  }
  return re.test(text);
}

/**
 * Renvoie la raison pour laquelle un article est prioritaire, ou ''.
 *  - toute « alerte » CERT-FR (rares et importantes) ;
 *  - un mot « chaud » dans le titre, pour les catégories techniques ;
 *  - un des mots surveillés, quelle que soit la catégorie.
 */
function alertReason(i) {
  if (i.source === 'CERT-FR Alertes') return 'ALERTE CERT-FR';
  const hay = `${i.title} ${i.summary}`;
  const w = S.watch.find(k => hasWord(hay, k));
  if (w && (SEC_CATS.has(i.cat) || (HOT_CATS.has(i.cat) && SEC.test(i.title)))) return `SURVEILLÉ : ${w}`;
  if (HOT_CATS.has(i.cat) && HOT.test(i.title)) return 'MOT CRITIQUE';
  return '';
}

/** Liste dédoublonnée des CVE citées dans un article. */
const cvesOf = i => [...new Set(`${i.title} ${i.summary}`.match(CVE) || [])].map(c => c.toUpperCase()).slice(0, 6);

const isNew = i => S.prevVisit && i.date > S.prevVisit;

/**
 * Premier de « mes sujets » cité par l'article (titre + résumé), ou undefined. Résultat mémorisé.
 * Les sources dédiées à un sujet (« Forum PJRC (Teensy) », « r/dogecoin »…) sont ignorées pour
 * ce sujet : tout y parle de lui. Le badge sert à repérer ton sujet dans les sources généralistes.
 */
function topicOf(i) {
  if (!('_t' in i)) {
    i._t = S.topics.find(k => !hasWord(i.source, k) && hasWord(`${i.title} ${i.summary}`, k));
  }
  return i._t;
}
/** À appeler quand la liste des sujets change. */
const resetTopics = () => S.items.concat(Object.values(S.fav)).forEach(i => delete i._t);

/* ---------- 4) RENDU ------------------------------------------------- */

/** L'article appartient-il à l'onglet actif ? */
function inTab(i) {
  switch (S.tab) {
    case 'Tout': case 'Favoris': return true;
    case 'Priorité': return !!alertReason(i);
    case 'Pour toi': return !!topicOf(i);
    case 'PRO': case 'PERSO': return GROUPS[S.tab].includes(i.cat);
    default: return i.cat === S.tab;
  }
}

/** Applique onglet + recherche + période + cases à cocher. */
function filtered() {
  const q = $('#q').value.trim().toLowerCase();
  const days = +$('#period').value;
  const since = days ? Date.now() / 1000 - days * 86400 : 0;
  const unread = $('#unread').checked, onlyNew = $('#onlyNew').checked;
  let list = S.tab === 'Favoris' ? Object.values(S.fav).sort((a, b) => b.date - a.date) : S.items;
  return list.filter(i =>
    inTab(i) &&
    (S.tab === 'Favoris' || !since || i.date >= since || !i.date) &&
    (!unread || !S.read.has(i.id)) &&
    (!onlyNew || isNew(i)) &&
    (!q || `${i.title} ${i.summary} ${i.source}`.toLowerCase().includes(q)));
}

/** Onglets sur trois lignes : vues transverses, famille PRO, famille PERSO. Chiffre = non lus. */
function renderTabs() {
  const unread = S.items.filter(i => !S.read.has(i.id));
  const n = f => unread.filter(f).length;
  const btn = (t, c, cls = '') => `<button data-tab="${esc(t)}" class="${cls} ${t === S.tab ? 'on' : ''}">${esc(t)}<b>${c}</b></button>`;
  const row = (label, cats) => `<div class="row"><span class="grp">${label}</span>` +
    btn(label, n(i => GROUPS[label].includes(i.cat)), 'all') + cats.map(c => btn(c, n(i => i.cat === c))).join('') + '</div>';
  $('#tabs').innerHTML = `<div class="row">${btn('Tout', unread.length)}${btn('Priorité', n(alertReason), 'red')}` +
    `${btn('Pour toi', n(topicOf), 'you')}${btn('Favoris', Object.keys(S.fav).length)}</div>` +
    row('PRO', GROUPS.PRO) + row('PERSO', GROUPS.PERSO);
}

/** HTML d'un article de la liste principale. */
function itemHtml(i, idx) {
  const [a, b] = ago(i.date);
  const why = alertReason(i);
  const cves = cvesOf(i);
  const topic = topicOf(i);
  // classe CSS de la couleur : premier mot de la catégorie, sans accent
  const cls = esc(i.cat.split(' ')[0].normalize('NFD').replace(/[^A-Za-z]/g, ''));
  return `<article class="item ${S.read.has(i.id) ? 'read' : ''} ${why ? 'hot' : topic ? 'mine' : ''} ${idx === S.cursor ? 'cur' : ''}" data-id="${esc(i.id)}" data-idx="${idx}">
    <div class="when">${a}<small>${esc(b)}</small></div>
    <div>
      <div class="meta"><span class="tag c-${cls}">${esc(i.cat)}</span><strong>${esc(i.source)}</strong>
        ${isNew(i) ? '<span class="new">NEW</span>' : ''}${why ? `<span class="down">⚠ ${esc(why)}</span>` : ''}${topic ? `<span class="you">◆ POUR TOI : ${esc(topic)}</span>` : ''}</div>
      <h3><a href="${esc(safeUrl(i.link))}" target="_blank" rel="noopener noreferrer" data-open>${esc(i.title)}</a></h3>
      ${i.summary ? `<p>${esc(i.summary)}</p>` : ''}
      ${cves.length ? `<div class="cves">${cves.map(c => `<a class="cve" target="_blank" rel="noopener" href="https://www.cve.org/CVERecord?id=${c}">${c}</a>`).join('')}</div>` : ''}
    </div>
    <div class="act">
      <button data-fav class="${S.fav[i.id] ? 'on' : ''}" title="Favori (F)">${S.fav[i.id] ? '★' : '☆'}</button>
      <button data-read title="Lu / non lu (L)">${S.read.has(i.id) ? '○' : '✓'}</button>
    </div></article>`;
}

function renderFeed() {
  S.view = filtered();
  const part = S.view.slice(0, S.shown);
  $('#feed').innerHTML = part.length ? part.map(itemHtml).join('')
    : `<div class="empty">${S.items.length ? 'AUCUNE DONNÉE CORRESPONDANTE.' : 'INTERROGATION DES FLUX EN COURS…'}</div>`;
  $('#more').hidden = S.view.length <= S.shown;
  $('#count').textContent = `${S.view.length} article${S.view.length > 1 ? 's' : ''}` +
    (S.view.length > S.shown ? ` · ${S.shown} affichés` : '');
}

/** Panneau rouge : articles prioritaires des 7 derniers jours. */
function renderAlerts() {
  const since = Date.now() / 1000 - 7 * 86400;
  const list = S.items.filter(i => i.date >= since && alertReason(i)).slice(0, 12);
  $('#alerts').innerHTML = list.length ? list.map(i =>
    `<a class="al ${S.read.has(i.id) ? 'read' : ''}" href="${esc(safeUrl(i.link))}" target="_blank" rel="noopener noreferrer" data-id="${esc(i.id)}" data-open>
      <small>${esc(ago(i.date)[0])} · ${esc(i.source)} · ${esc(alertReason(i))}</small>${esc(i.title)}</a>`).join('')
    : '<p class="hint">Rien d’urgent sur 7 jours. ✔</p>';
}

/** Cours crypto + carte « état du système ». */
function renderTicker(c) {
  const cards = (c.coins || []).map(k => {
    const sp = k.spark || [];
    let svg = '';
    if (sp.length > 1) {   // mini-courbe 7 jours
      const mn = Math.min(...sp), mx = Math.max(...sp), r = mx - mn || 1;
      const pts = sp.map((v, j) => `${(j / (sp.length - 1) * 100).toFixed(1)},${(40 - (v - mn) / r * 36).toFixed(1)}`).join(' ');
      svg = `<svg viewBox="0 0 100 42" preserveAspectRatio="none" aria-hidden="true"><polyline points="${pts}" fill="none" stroke="${k.ch7 >= 0 ? '#3dff7f' : '#ff3b2f'}" stroke-width="1.4" vector-effect="non-scaling-stroke"/></svg>`;
    }
    return `<div class="coin"><header><span>${esc(k.symbol)} · ${esc(k.name)}</span><span>7 j</span></header>
      <div class="px">${fmtEur(k.price)}</div>
      <div class="ch"><span class="${k.ch24 >= 0 ? 'up' : 'down'}">${pct(k.ch24)}</span> <span style="color:var(--mut)">24 h</span> ·
      <span class="${k.ch7 >= 0 ? 'up' : 'down'}">${pct(k.ch7)}</span></div>${svg}</div>`;
  }).join('') || `<div class="coin"><header><span>CRYPTO</span></header><div class="px">—</div><div class="ch down">${esc(c.error || 'indisponible')}</div></div>`;
  $('#ticker').innerHTML = cards + `<div class="stat" id="sysStat"></div>`;
  renderStat();
}

function renderStat() {
  const el = $('#sysStat'); if (!el) return;
  const st = Object.values(S.status), ok = st.filter(s => s.ok).length;
  const nouveaux = S.items.filter(isNew).length;
  const alerts = S.items.filter(i => alertReason(i) && !S.read.has(i.id) && i.date > Date.now() / 1000 - 7 * 86400).length;
  el.innerHTML = `<p>ÉTAT DU SYSTÈME</p><div class="big">${nouveaux} <span style="font-size:20px">nouveaux</span></div>
    <p><b>${alerts}</b> alertes · <b>${S.items.filter(i => topicOf(i) && !S.read.has(i.id)).length}</b> pour toi · <b>${ok}/${st.length}</b> sources OK</p>
    <p>${S.prevVisit ? 'depuis ta visite du ' + new Date(S.prevVisit * 1000).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : 'première visite'}</p>`;
}

function renderSources() {
  const byCat = {};
  S.sources.forEach(s => (byCat[s.cat] ||= []).push(s));
  $('#sources').innerHTML = Object.entries(byCat).map(([c, l]) => `<div class="cat">${esc(c.toUpperCase())}</div>` + l.map(s => {
    const st = S.status[s.id];
    // rouge = erreur de téléchargement ; orange = le flux marche mais n'a rien publié récemment
    const state = !s.on || !st ? '' : !st.ok ? 'ko' : (!st.count || st.error) ? 'quiet' : '';
    return `<div class="src ${s.on ? '' : 'off'} ${state}" title="${esc(st?.error || s.url)}">
      <i></i><span>${esc(s.name)}</span><em>${s.on ? (st ? st.count : '…') : 'off'}</em>
      <button data-toggle="${esc(s.id)}" title="${s.on ? 'Mettre en pause' : 'Réactiver'}">${s.on ? '⏸' : '▶'}</button>
      <button data-del="${esc(s.id)}" title="Supprimer">×</button></div>`;
  }).join('')).join('');
  const st = Object.values(S.status);
  $('#srcStat').textContent = `${st.filter(s => s.ok && s.count).length}/${S.sources.filter(s => s.on).length} OK`;
  $('#addCat').innerHTML = CATS.map(c => `<option>${esc(c)}</option>`).join('');
}

/** Affiche les deux listes de mots-clés (alertes et sujets perso). */
function renderWatch() {
  const chips = (list, key) => list.map((w, i) =>
    `<span class="chip">${esc(w)}<button data-${key}="${i}" aria-label="Retirer ${esc(w)}">×</button></span>`).join('');
  $('#watch').innerHTML = chips(S.watch, 'unwatch');
  $('#topics').innerHTML = chips(S.topics, 'untopic');
}

/**
 * Panneau « Dernières versions » : pour chaque flux de versions (GitHub / Codeberg),
 * la sortie la plus récente. Vert = moins de 30 jours.
 */
function renderVersions() {
  const rel = S.sources.filter(s => s.on && /(github\.com|codeberg\.org)\//.test(s.url));
  const rows = rel.map(s => {
    const last = S.items.find(i => i.sid === s.id);   // S.items est trié du plus récent au plus ancien
    if (!last) return '';
    const short = s.name.split(' (')[0];
    // « Meshtastic Firmware 2.8.2 » -> « 2.8.2 » : on retire le nom du projet (sans tenir compte des majuscules)
    const ver = last.title.replace(new RegExp(short.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'), '')
      .replace(/^\s*[—-]?\s*/, '').trim() || last.title;
    const fresh = Date.now() / 1000 - last.date < 30 * 86400;
    return `<a class="ver ${fresh ? 'fresh' : ''}" href="${esc(safeUrl(last.link))}" target="_blank" rel="noopener noreferrer" data-id="${esc(last.id)}">
      <span>${esc(short)}</span><b>${esc(ver)}</b><em>${esc(ago(last.date)[0])}</em></a>`;
  }).join('');
  $('#versions').innerHTML = rows || '<p class="hint">Chargement…</p>';
}

function renderAll() { renderTabs(); renderFeed(); renderAlerts(); renderStat(); renderVersions(); }

/* ---------- 5) ACTIONS ---------------------------------------------- */

/** Télécharge les flux. force=true ignore le cache de 15 min du serveur. */
async function loadFeeds(force = false) {
  const hal = $('#hal');
  hal.classList.add('busy');
  setTag(force ? 'INTERROGATION FORCÉE DE TOUTES LES SOURCES…' : 'SYNCHRONISATION…');
  try {
    const d = await api('/api/feeds' + (force ? '?force=1' : ''));
    S.items = d.items;
    S.status = Object.fromEntries(d.status.map(s => [s.id, s]));
    renderAll(); renderSources();
    setTag(`${d.items.length} ARTICLES · ${d.status.filter(s => s.ok).length} SOURCES EN LIGNE · ${new Date().toLocaleTimeString('fr-FR')}`);
  } catch (e) {
    setTag('ERREUR : serveur injoignable. Lance « Lancer-Veille.bat ».');
    $('#feed').innerHTML = `<div class="empty">LIAISON PERDUE AVEC LE SERVEUR LOCAL.<br><small>${esc(e.message)}</small></div>`;
  } finally { hal.classList.remove('busy'); }
  api('/api/crypto').then(renderTicker).catch(() => renderTicker({ error: 'hors ligne' }));
}

/** Effet « terminal » : le texte de la barre de titre s'écrit lettre par lettre. */
let tagTimer;
function setTag(t) {
  clearInterval(tagTimer);
  const el = $('#tagline'); let n = 0;
  tagTimer = setInterval(() => { el.textContent = t.slice(0, ++n) + (n < t.length ? '█' : ''); if (n >= t.length) clearInterval(tagTimer); }, 12);
}

function toggleFav(id) {
  const it = S.items.find(i => i.id === id) || S.fav[id];
  if (!it) return;
  if (S.fav[id]) delete S.fav[id]; else { const { _t, ...clean } = it; S.fav[id] = { ...clean, favAt: Date.now() / 1000 }; }
  saveState(); renderAll();
}

function toggleRead(id, force) {
  const on = force ?? !S.read.has(id);
  on ? S.read.add(id) : S.read.delete(id);
  saveState(); renderAll();
}

/**
 * Synthèse Markdown des favoris : la base de ton compte rendu de veille
 * (dossier professionnel TSSR, réunion d'équipe, fiche hebdo…).
 */
function exportSynthese() {
  const favs = Object.values(S.fav).sort((a, b) => b.date - a.date);
  const d = new Date().toLocaleDateString('fr-FR', { dateStyle: 'full' });
  const week = Date.now() / 1000 - 7 * 86400;
  const alerts = S.items.filter(i => i.date >= week && alertReason(i)).slice(0, 15);
  let md = `# Veille Azoth — synthèse du ${d}\n\n`;
  md += `> ${favs.length} article(s) retenu(s) · ${alerts.length} alerte(s) sur 7 jours · ${Object.keys(S.status).length} sources suivies\n\n`;
  md += `## Alertes de sécurité de la semaine\n\n`;
  md += alerts.length ? alerts.map(i => `- **${i.title}** — ${i.source}, ${new Date(i.date * 1000).toLocaleDateString('fr-FR')} (${alertReason(i)})${cvesOf(i).length ? ' · ' + cvesOf(i).join(', ') : ''}  \n  ${i.link}`).join('\n') + '\n\n' : '_Aucune._\n\n';
  const byCat = {};
  favs.forEach(f => (byCat[f.cat] ||= []).push(f));
  const fw = S.items.filter(i => i.cat === 'Firmwares' && i.date >= week);
  md += `## Nouvelles versions de firmwares et logiciels (7 jours)\n\n`;
  md += fw.length ? fw.map(i => `- ${i.title} — ${new Date(i.date * 1000).toLocaleDateString('fr-FR')}  \n  ${i.link}`).join('\n') + '\n\n' : '_Aucune._\n\n';
  md += `## Articles retenus\n\n`;
  if (!favs.length) md += '_Aucun favori : clique sur ☆ pour retenir un article._\n\n';
  for (const c of CATS.filter(c => byCat[c])) {
    md += `### ${c}\n\n`;
    for (const f of byCat[c]) {
      md += `#### ${f.title}\n\n- Source : ${f.source} — ${f.date ? new Date(f.date * 1000).toLocaleDateString('fr-FR') : 's.d.'}\n- Lien : ${f.link}\n`;
      if (f.summary) md += `- Résumé : ${f.summary}\n`;
      md += `- **Ce que j'en retiens / impact sur mon poste :** \n- **Action :** ☐ tester ☐ documenter ☐ appliquer un correctif ☐ informer l'équipe\n\n`;
    }
  }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([md], { type: 'text/markdown;charset=utf-8' }));
  a.download = `veille-azoth-${new Date().toISOString().slice(0, 10)}.md`;
  a.click(); URL.revokeObjectURL(a.href);
}

/* Clics dans la liste (délégation d'événements : un seul écouteur). */
$('#feed').addEventListener('click', e => {
  const art = e.target.closest('.item'); if (!art) return;
  const id = art.dataset.id;
  if (e.target.closest('[data-fav]')) toggleFav(id);
  else if (e.target.closest('[data-read]')) toggleRead(id);
  else if (e.target.closest('[data-open]')) setTimeout(() => toggleRead(id, true), 50);
  S.cursor = +art.dataset.idx;
});
$('#alerts').addEventListener('click', e => { const a = e.target.closest('[data-id]'); if (a) setTimeout(() => toggleRead(a.dataset.id, true), 50); });
$('#tabs').addEventListener('click', e => {
  const b = e.target.closest('[data-tab]'); if (!b) return;
  S.tab = b.dataset.tab; S.shown = 60; S.cursor = -1; renderTabs(); renderFeed();
});
['#q', '#period', '#unread', '#onlyNew'].forEach(s => $(s).addEventListener('input', () => { S.shown = 60; S.cursor = -1; renderFeed(); }));
$('#more').onclick = () => { S.shown += 60; renderFeed(); };
$('#markAll').onclick = () => { S.view.forEach(i => S.read.add(i.id)); saveState(); renderAll(); };
$('#hal').onclick = () => loadFeeds(true);
$('#btnSynth').onclick = exportSynthese;
$('#modules').addEventListener('click', e => {
  const module = e.target.closest('[data-module]');
  if (!module) return;
  if (module.dataset.module === 'trading' && module.getAttribute('href') !== '#') return;
  if (module.dataset.module === 'ai' && module.getAttribute('href') !== '#') return;
  e.preventDefault();
  const names = { trading: 'Quant Core', ai: 'IA locale', vault: 'Cœur Obsidian' };
  alert(`${names[module.dataset.module]} : l’état est déjà supervisé. L’interface native sera activée à l’étape suivante.`);
});

/** Arrête le serveur local (la veille lancée par l'icône tourne sans fenêtre). */
$('#btnOff').onclick = async () => {
  if (!confirm('Arrêter la veille ? (relance-la avec l’icône du Bureau)')) return;
  await api('/api/shutdown', {}).catch(() => {});
  document.body.innerHTML = '<div id="boot"><pre>&gt; MU-TH-UR 6000 HORS LIGNE.\n\nAU REVOIR AZOTH.\n\n(tu peux fermer cet onglet)</pre></div>';
};

/** Branche un formulaire « ajouter un mot » et sa liste de puces. */
function keywordList(form, input, box, key, list) {
  const changed = () => { resetTopics(); saveState(); renderWatch(); renderAll(); };
  $(form).onsubmit = e => {
    e.preventDefault();
    const v = $(input).value.trim();
    if (v && !S[list].some(w => w.toLowerCase() === v.toLowerCase())) { S[list].push(v); changed(); }
    $(input).value = '';
  };
  $(box).onclick = e => {
    const b = e.target.closest(`[data-${key}]`); if (!b) return;
    S[list].splice(+b.dataset[key], 1); changed();
  };
}
keywordList('#watchForm', '#watchIn', '#watch', 'unwatch', 'watch');
keywordList('#topicForm', '#topicIn', '#topics', 'untopic', 'topics');

$('#sources').onclick = async e => {
  const t = e.target.closest('[data-toggle]'), d = e.target.closest('[data-del]');
  if (d && !confirm('Supprimer cette source ?')) return;
  if (t) await api('/api/sources/toggle', { id: t.dataset.toggle });
  if (d) await api('/api/sources/remove', { id: d.dataset.del });
  if (t || d) { S.sources = (await api('/api/config')).sources; await loadFeeds(); }
};

$('#addForm').onsubmit = async e => {
  e.preventDefault();
  const msg = $('#addMsg'); msg.textContent = 'Test du flux…';
  try {
    const r = await api('/api/sources/add', { name: $('#addName').value, url: $('#addUrl').value, cat: $('#addCat').value });
    msg.textContent = r.test.ok && r.test.count ? `✔ ${r.test.count} articles trouvés.` : `⚠ Ajoutée, mais le flux ne répond pas : ${r.test.error}`;
    e.target.reset();
    S.sources = (await api('/api/config')).sources; await loadFeeds();
  } catch (err) { msg.textContent = '✖ ' + err.message; }
};

/* Raccourcis clavier façon lecteur RSS. */
document.addEventListener('keydown', e => {
  if (e.target.matches('input,select,textarea') || e.ctrlKey || e.metaKey || e.altKey) {
    if (e.key === 'Escape') e.target.blur();
    return;
  }
  const k = e.key.toLowerCase(), cur = S.view[S.cursor];
  if (k === '/') { e.preventDefault(); $('#q').focus(); }
  else if (k === 'r') loadFeeds(true);
  else if (k === 'j' || k === 'k') {
    S.cursor = Math.max(0, Math.min(Math.min(S.view.length, S.shown) - 1, S.cursor + (k === 'j' ? 1 : -1)));
    renderFeed(); document.querySelector('.item.cur')?.scrollIntoView({ block: 'nearest' });
  } else if (cur && k === 'o') { window.open(safeUrl(cur.link), '_blank', 'noopener'); toggleRead(cur.id, true); }
  else if (cur && k === 'f') toggleFav(cur.id);
  else if (cur && k === 'l') toggleRead(cur.id);
});

/* ---------- 6) EFFETS VISUELS --------------------------------------- */

/** Horloge façon Nostromo. */
setInterval(() => { $('#clock').textContent = new Date().toLocaleTimeString('fr-FR'); }, 1000);

/** Pluie de caractères Matrix en fond (désactivable, coupée si « réduire les animations »). */
const rain = (() => {
  const cv = $('#rain'), ctx = cv.getContext('2d');
  const glyphs = 'アイウエオカキクケコサシスセソタチツテトナニヌネノ0123456789ABCDEF$#<>';
  let drops = [], timer = null;
  // clientWidth (et pas innerWidth) : n'inclut pas la barre de défilement -> pas de débordement horizontal.
  const size = () => { cv.width = document.documentElement.clientWidth; cv.height = innerHeight; drops = Array(Math.ceil(cv.width / 16)).fill(0).map(() => Math.random() * -50); };
  const tick = () => {
    ctx.fillStyle = 'rgba(3,6,4,.14)'; ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = '#3dff7f'; ctx.font = '15px monospace';
    drops.forEach((y, x) => {
      ctx.fillText(glyphs[Math.random() * glyphs.length | 0], x * 16, y * 16);
      drops[x] = y * 16 > cv.height && Math.random() > .975 ? 0 : y + 1;
    });
  };
  addEventListener('resize', size);
  return {
    on() { size(); timer ||= setInterval(tick, 60); cv.style.display = ''; },
    off() { clearInterval(timer); timer = null; cv.style.display = 'none'; },
  };
})();
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
let rainOn = !reduced;
try { const v = localStorage.getItem('veille-rain'); if (v !== null) rainOn = v === '1'; } catch { /* stockage indisponible */ }
rainOn ? rain.on() : rain.off();
$('#btnRain').onclick = () => {
  rainOn = !rainOn; rainOn ? rain.on() : rain.off();
  try { localStorage.setItem('veille-rain', rainOn ? '1' : '0'); } catch { /* rien */ }
};

/** Séquence de démarrage façon MU-TH-UR (une fois par session, clic pour passer). */
function boot() {
  const el = $('#boot');
  let seen = false;
  try { seen = sessionStorage.getItem('veille-boot') === '1'; sessionStorage.setItem('veille-boot', '1'); } catch { /* rien */ }
  if (seen || reduced) { el.remove(); return; }
  const lines = ['WEYLAND-YUTANI CORP.  //  MU-TH-UR 6000', '', '> UTILISATEUR : AZOTH', '> INITIALISATION INTERFACE 2037 ........ OK',
    '> CONNEXION RÉSEAU DE VEILLE ............ OK', '> CHARGEMENT DES SOURCES ................ OK',
    '', 'BONJOUR AZOTH. JE SUIS PRÊTE.', '', '« I\'m sorry Dave, I\'m afraid I can\'t do that. »  — HAL 9000'];
  const txt = lines.join('\n'); let n = 0;
  const end = () => { el.classList.add('off'); setTimeout(() => el.remove(), 450); };
  el.onclick = end;
  const t = setInterval(() => { $('#bootText').textContent = txt.slice(0, n += 3) + '█'; if (n >= txt.length) { clearInterval(t); setTimeout(end, 700); } }, 14);
}

/* ---------- 7) DÉMARRAGE -------------------------------------------- */
(async function start() {
  boot();
  loadCockpit();
  renderFeed();
  try {
    const cfg = await api('/api/config');
    S.sources = cfg.sources;
    S.fav = cfg.state.fav || {};
    S.read = new Set(cfg.state.read || []);
    S.watch = cfg.state.watch || [];
    S.topics = cfg.state.topics || [];
    // « Nouveaux » = publiés depuis la visite précédente. Une visite = une session
    // séparée d'au moins 30 min : recharger la page ne remet donc pas le compteur à zéro.
    const now = Date.now() / 1000, last = cfg.state.lastVisit || 0;
    S.prevVisit = now - last > 1800 ? last : (cfg.state.prevVisit || last);
    api('/api/state', { lastVisit: now, prevVisit: S.prevVisit }).catch(() => {});
    renderSources(); renderWatch();
  } catch { /* loadFeeds affichera l'erreur */ }
  await loadFeeds();
  setInterval(loadCockpit, 30 * 1000);
  setInterval(() => loadFeeds(), 15 * 60 * 1000);   // rafraîchissement auto toutes les 15 min
})();
