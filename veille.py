#!/usr/bin/env python3
"""Veille Azoth - serveur local (Python 3.9+, bibliotheque standard uniquement).

Lance :  python veille.py        puis ouvre http://127.0.0.1:8765
Options :
    --port 8765          port d'ecoute
    --host 0.0.0.0       ecouter sur le reseau (Raspberry Pi, acces depuis le telephone)
    --password MOTDEPASSE  protege l'acces (sinon variable d'environnement VEILLE_PASSWORD)
    --no-browser         ne pas ouvrir le navigateur au demarrage

Pourquoi un serveur ?
    Un navigateur refuse qu'une page lise un flux RSS d'un autre site (CORS).
    Ce script fait donc l'intermediaire : il telecharge les flux, les
    convertit en JSON propre et sert l'interface du dossier dist/.

Fonctionnement :
    1. sources.json liste les flux (nom, URL, categorie, actif ou non, et
       en option "ttl" = secondes entre deux telechargements, "max" =
       nombre d'articles gardes).
    2. refresh() telecharge en parallele les flux dont le cache est
       perime. Les flux d'un meme site passent l'un apres l'autre
       (Reddit bloque les rafales). Analyse RSS 2.0, RSS 1.0 et Atom ;
       au plus 40 articles de moins de 45 jours par source.
    3. Le resultat est garde en memoire et dans data/cache.json : au
       redemarrage, l'affichage est immediat.
    4. data/state.json garde favoris, articles lus et mots surveilles.
    5. crypto() interroge l'API publique CoinGecko (cache 5 min).

Securite :
    - par defaut, ecoute uniquement sur 127.0.0.1 (invisible depuis le
      reseau) ; avec --host, un mot de passe est fortement conseille ;
    - les ecritures (POST) venant d'un autre site sont refusees ;
    - impossible de lire un fichier hors de dist/ ;
    - le texte des flux est nettoye ici, puis echappe par l'interface.
"""
import base64
import concurrent.futures as cf
import email.utils
import hmac
import os
import hashlib
import html
import json
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "dist"
DATA = ROOT / "data"
SOURCES_FILE = ROOT / "sources.json"
STATE_FILE = DATA / "state.json"
CACHE_FILE = DATA / "cache.json"

FEED_TTL = 15 * 60          # secondes avant de re-telecharger un flux
CRYPTO_TTL = 5 * 60
MAX_PER_SOURCE = 40
MAX_AGE_DAYS = 45
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VeilleAzoth/3.0"
COINS = "bitcoin,monero,dogecoin"   # identifiants CoinGecko, separes par des virgules
SLOW_HOSTS = {"www.reddit.com": 3.0}  # site -> pause (s) entre deux flux du meme site
PASSWORD = ""                         # rempli par --password ou VEILLE_PASSWORD

lock = threading.RLock()
DATA.mkdir(exist_ok=True)

# Lance par pythonw.exe (raccourci du Bureau), il n'y a pas de console :
# sys.stdout / sys.stderr valent None. On redirige alors tout vers data/veille.log.
if sys.stdout is None or sys.stderr is None:
    _log = open(DATA / "veille.log", "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = _log


# ---------------------------------------------------------------- stockage
def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_json(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def default_state():
    """Etat initial. "watch" = mots qui declenchent une ALERTE (securite pro) ;
    "topics" = tes sujets perso, simplement mis en avant (badge POUR TOI)."""
    return {"fav": {}, "read": [], "lastVisit": 0, "prevVisit": 0,
            "watch": ["Windows Server", "Active Directory", "Fortinet", "Proxmox",
                      "VMware", "Cisco", "OpenSSH", "pfSense", "OPNsense", "Veeam", "TrueNAS"],
            "topics": ["Teensy", "EP-133", "KO II", "K.O. II", "OP-1", "Teenage Engineering",
                       "E-M5", "OM System", "Olympus", "M.Zuiko", "Magic Lantern", "darktable",
                       "Meshtastic", "LoRa", "ExpressLRS", "ESP32", "RP2040", "Raspberry Pi",
                       "Amiga", "Game Boy", "LSDJ", "Godot", "Strudel", "Dexed", "Freqtrade",
                       "Monero", "Dogecoin", "chiptune", "groovebox",
                       "Omarchy", "Pop!_OS", "COSMIC", "Hyprland"]}


sources = load_json(SOURCES_FILE, [])
state = {**default_state(), **load_json(STATE_FILE, {})}
cache = load_json(CACHE_FILE, {})        # id_source -> {fetched, ok, error, items}
crypto_cache = {"t": 0, "data": None}


def sid(url):
    return hashlib.sha1(url.encode()).hexdigest()[:10]


for s in sources:
    s.setdefault("id", sid(s["url"]))
    s.setdefault("on", True)


# ---------------------------------------------------------------- parsing
class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)


def strip_html(s, limit=320):
    if not s:
        return ""
    p = _Text()
    try:
        p.feed(s)
        txt = "".join(p.out)
    except Exception:
        txt = re.sub(r"<[^>]+>", " ", s)
    txt = re.sub(r"\s+", " ", html.unescape(txt)).strip()
    return txt if len(txt) <= limit else txt[:limit].rsplit(" ", 1)[0] + "…"


def parse_date(s):
    if not s:
        return 0
    s = s.strip()
    try:
        return email.utils.parsedate_to_datetime(s).timestamp()
    except (TypeError, ValueError, IndexError):
        pass
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.timestamp()
    except ValueError:
        return 0


def local(tag):
    return tag.rsplit("}", 1)[-1].lower()


def child(el, *names):
    for c in el:
        if local(c.tag) in names:
            return c
    return None


def text_of(el, *names):
    c = child(el, *names)
    return (c.text or "").strip() if c is not None and c.text else ""


def parse_feed(raw):
    """Renvoie une liste de dict {title, link, date, summary}. RSS 2.0, RSS 1.0, Atom."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return parse_feed_lenient(raw.decode("utf-8", "replace"))
    out = []
    for el in root.iter():
        name = local(el.tag)
        if name not in ("item", "entry"):
            continue
        title = strip_html(text_of(el, "title"), 220)
        link = ""
        for c in el:
            if local(c.tag) == "link":
                href = c.get("href")
                if href and c.get("rel", "alternate") == "alternate":
                    link = href
                    break
                if href and not link:
                    link = href
                elif c.text and c.text.strip():
                    link = c.text.strip()
                    break
        if not link:
            link = text_of(el, "guid", "id")
        date = parse_date(text_of(el, "pubdate", "published", "updated", "date", "issued"))
        summary = ""
        for n in ("description", "summary", "encoded", "content"):
            c = child(el, n)
            if c is not None:
                summary = c.text or "".join(c.itertext())
                if summary.strip():
                    break
        if title and link.startswith(("http://", "https://")):
            out.append({"title": title, "link": link, "date": date, "summary": strip_html(summary)})
    return out


def parse_feed_lenient(txt):
    out = []
    for block in re.findall(r"<(?:item|entry)\b.*?</(?:item|entry)>", txt, re.S | re.I):
        def grab(tag):
            m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", block, re.S | re.I)
            v = m.group(1) if m else ""
            return re.sub(r"^<!\[CDATA\[|\]\]>$", "", v.strip())
        link = grab("link")
        if not link:
            m = re.search(r'<link[^>]+href="([^"]+)"', block)
            link = m.group(1) if m else ""
        title = strip_html(grab("title"), 220)
        if title and link.startswith("http"):
            out.append({"title": title, "link": html.unescape(link), "summary": strip_html(grab("description") or grab("summary")),
                        "date": parse_date(grab("pubDate") or grab("published") or grab("updated"))})
    return out


# ---------------------------------------------------------------- collecte
def http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(5_000_000)


def fetch_source(src):
    entry = {"fetched": time.time(), "ok": False, "error": "", "items": []}
    try:
        parsed = parse_feed(http_get(src["url"]))
        # On ignore les articles trop vieux : la veille porte sur l'actualite.
        # Exception : les flux de versions (GitHub, Codeberg). Un firmware peut
        # rester des annees sans sortie : on garde ses 5 dernieres versions, quel que soit leur age.
        release = bool(re.search(r"(github\.com|codeberg\.org)/", src["url"]))
        days = src.get("days", 3650 if release else MAX_AGE_DAYS)
        keep = src.get("max", 5 if release else MAX_PER_SOURCE)
        limit = time.time() - days * 86400
        items = [i for i in parsed if not i["date"] or i["date"] > limit]
        if release:   # les versions de test publiees chaque nuit ne sont que du bruit
            items = [i for i in items if not re.search(r"nightly", i["title"], re.I)]
        items.sort(key=lambda i: i["date"], reverse=True)
        # Versions GitHub / Codeberg : le titre n'est souvent que "v2.6.0".
        # On le prefixe avec le nom de la source pour qu'il reste lisible.
        if release:
            short = src["name"].split(" (")[0]
            for i in items:
                if short.lower() not in i["title"].lower():
                    i["title"] = f"{short} — {i['title']}"
        for i in items[:keep]:
            i["id"] = hashlib.sha1(i["link"].encode()).hexdigest()[:14]
            i["source"] = src["name"]
            i["sid"] = src["id"]
            i["cat"] = src["cat"]
            entry["items"].append(i)
        entry["ok"] = True
        if not parsed:
            entry["error"] = "flux vide ou illisible"
        elif not items:
            entry["error"] = f"rien de neuf depuis {days} jours"
    except Exception as e:  # noqa: BLE001 - on veut tout remonter a l'interface
        entry["error"] = f"{type(e).__name__}: {str(e)[:120]}"
        old = cache.get(src["id"])
        if old:
            entry["items"] = old.get("items", [])  # on garde les anciens articles
    return src["id"], entry


def fetch_host_group(group):
    """Telecharge, l'un apres l'autre, les flux d'un meme site (politesse anti-blocage)."""
    out = []
    for n, src in enumerate(group):
        if n:
            time.sleep(SLOW_HOSTS.get(urllib.parse.urlparse(src["url"]).netloc, 0))
        out.append(fetch_source(src))
    return out


refresh_lock = threading.Lock()   # evite deux collectes simultanees


def refresh(force=False):
    """Met a jour les flux perimes puis renvoie tous les articles, du plus recent au plus ancien.
    force=True ignore le cache, sauf pour les sites lents (Reddit) rafraichis il y a moins de 5 min."""
    with lock:
        active = [s for s in sources if s.get("on", True)]
    with refresh_lock:
        now = time.time()

        def stale(s):
            age = now - cache.get(s["id"], {}).get("fetched", 0)
            if force:
                slow = urllib.parse.urlparse(s["url"]).netloc in SLOW_HOSTS
                return age > (300 if slow else 0)
            return age > s.get("ttl", FEED_TTL)

        todo = [s for s in active if stale(s)]
        if todo:
            groups = {}
            for s in todo:   # un groupe par site
                groups.setdefault(urllib.parse.urlparse(s["url"]).netloc, []).append(s)
            with cf.ThreadPoolExecutor(max_workers=16) as ex:
                for results in ex.map(fetch_host_group, groups.values()):
                    for k, entry in results:
                        cache[k] = entry
            with lock:
                save_json(CACHE_FILE, cache)
    items, status = [], []
    for s in active:
        c = cache.get(s["id"], {})
        for i in c.get("items", []):
            # nom et categorie viennent toujours de sources.json (le cache peut etre ancien)
            i["source"], i["cat"] = s["name"], s["cat"]
            items.append(i)
        status.append({"id": s["id"], "ok": c.get("ok", False), "error": c.get("error", ""),
                       "count": len(c.get("items", [])), "fetched": c.get("fetched", 0)})
    seen, uniq = set(), []
    for i in sorted(items, key=lambda i: i["date"], reverse=True):
        if i["id"] not in seen:
            seen.add(i["id"])
            uniq.append(i)
    return {"items": uniq, "status": status, "now": now}


def crypto():
    if crypto_cache["data"] and time.time() - crypto_cache["t"] < CRYPTO_TTL:
        return crypto_cache["data"]
    url = ("https://api.coingecko.com/api/v3/coins/markets?vs_currency=eur&ids=" + COINS +
           "&sparkline=true&price_change_percentage=24h,7d")
    try:
        rows = json.loads(http_get(url))
        data = [{"id": r["id"], "symbol": r["symbol"].upper(), "name": r["name"],
                 "price": r["current_price"], "ch24": r.get("price_change_percentage_24h_in_currency"),
                 "ch7": r.get("price_change_percentage_7d_in_currency"), "cap": r.get("market_cap"),
                 "spark": (r.get("sparkline_in_7d") or {}).get("price", [])[::4]} for r in rows]
        crypto_cache.update(t=time.time(), data={"ok": True, "coins": data, "t": time.time()})
    except Exception as e:  # noqa: BLE001
        if crypto_cache["data"]:
            return {**crypto_cache["data"], "stale": True}
        return {"ok": False, "error": str(e)[:120], "coins": []}
    return crypto_cache["data"]


def opml():
    """Export des sources au format OPML (import dans Feedly, Inoreader, FreshRSS…)."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<opml version="2.0">',
             '<head><title>Veille Azoth</title></head>', '<body>']
    cats = {}
    for s in sources:
        cats.setdefault(s["cat"], []).append(s)
    for cat, lst in cats.items():
        lines.append(f'<outline text="{html.escape(cat)}" title="{html.escape(cat)}">')
        for s in lst:
            n = html.escape(s["name"])
            lines.append(f'  <outline type="rss" text="{n}" title="{n}" xmlUrl="{html.escape(s["url"])}"/>')
        lines.append("</outline>")
    lines += ["</body>", "</opml>"]
    return "\n".join(lines)


# ---------------------------------------------------------------- HTTP
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png",
        ".ico": "image/x-icon", ".json": "application/json"}


class Handler(BaseHTTPRequestHandler):
    """Sert l'interface (dist/) et l'API JSON (/api/...)."""
    server_version = "VeilleAzoth/3.0"

    def authorized(self):
        """Authentification HTTP Basic, active seulement si un mot de passe est defini.
        Le navigateur affiche sa fenetre de connexion ; n'importe quel identifiant convient."""
        if not PASSWORD:
            return True
        h = self.headers.get("Authorization", "")
        if h.startswith("Basic "):
            try:
                given = base64.b64decode(h[6:]).decode("utf-8").split(":", 1)[-1]
            except (ValueError, UnicodeDecodeError):
                return False
            return hmac.compare_digest(given.encode(), PASSWORD.encode())
        return False

    def deny(self):
        self.send(401, {"error": "mot de passe requis"},
                  extra={"WWW-Authenticate": 'Basic realm="Veille Azoth", charset="UTF-8"'})

    def log_message(self, fmt, *args):  # console plus calme
        if "/api/" in (args[0] if args else "") and " 200 " not in fmt % args:
            sys.stderr.write("%s\n" % (fmt % args))

    def send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        if not isinstance(body, (bytes, str)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 2_000_000:
            raise ValueError("requete trop grosse")
        return json.loads(self.rfile.read(n) or b"{}")

    def same_origin(self):
        # Protege l'API locale contre les requetes envoyees par d'autres sites.
        origin = self.headers.get("Origin")
        return origin is None or origin == f"http://{self.headers.get('Host')}"

    def do_GET(self):
        if not self.authorized():
            return self.deny()
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        if u.path == "/api/feeds":
            return self.send(200, refresh(force=q.get("force") == ["1"]))
        if u.path == "/api/crypto":
            return self.send(200, crypto())
        if u.path == "/api/config":
            with lock:
                return self.send(200, {"sources": sources, "state": state})
        if u.path == "/api/opml":
            return self.send(200, opml(), "text/x-opml; charset=utf-8",
                             {"Content-Disposition": 'attachment; filename="veille-tssr.opml"'})
        path = "index.html" if u.path in ("", "/") else u.path.lstrip("/")
        f = (WEB / path).resolve()
        if WEB not in f.parents or not f.is_file():
            return self.send(404, {"error": "introuvable"})
        return self.send(200, f.read_bytes(), MIME.get(f.suffix, "application/octet-stream"))

    def do_POST(self):
        if not self.authorized():
            return self.deny()
        if not self.same_origin():
            return self.send(403, {"error": "origine refusee"})
        try:
            data = self.body()
        except ValueError as e:
            return self.send(400, {"error": str(e)})
        path = urllib.parse.urlparse(self.path).path
        with lock:
            if path == "/api/state":
                for k in ("fav", "read", "lastVisit", "prevVisit", "watch", "topics"):
                    if k in data:
                        state[k] = data[k]
                state["read"] = state["read"][-8000:]
                save_json(STATE_FILE, state)
                return self.send(200, {"ok": True})
            if path == "/api/sources/add":
                name, url, cat = (str(data.get(k, "")).strip() for k in ("name", "url", "cat"))
                if not name or not url.startswith(("http://", "https://")) or not cat:
                    return self.send(400, {"error": "nom, URL http(s) et categorie requis"})
                if any(s["url"] == url for s in sources):
                    return self.send(409, {"error": "source deja suivie"})
                src = {"id": sid(url), "name": name[:60], "url": url, "cat": cat[:40], "on": True}
                sources.append(src)
                save_json(SOURCES_FILE, sources)
                _, entry = fetch_source(src)
                cache[src["id"]] = entry
                return self.send(200, {"ok": True, "source": src, "test": {"ok": entry["ok"], "error": entry["error"], "count": len(entry["items"])}})
            if path == "/api/sources/remove":
                sources[:] = [s for s in sources if s["id"] != data.get("id")]
                cache.pop(data.get("id"), None)
                save_json(SOURCES_FILE, sources)
                return self.send(200, {"ok": True})
            if path == "/api/shutdown":
                # bouton ⏻ de l'interface : utile quand la veille tourne sans fenetre
                self.send(200, {"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return None
            if path == "/api/sources/toggle":
                for s in sources:
                    if s["id"] == data.get("id"):
                        s["on"] = not s.get("on", True)
                save_json(SOURCES_FILE, sources)
                return self.send(200, {"ok": True})
        return self.send(404, {"error": "route inconnue"})


def arg(name, default=None):
    """Lit une option de ligne de commande : --name valeur."""
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def lan_ip():
    """Adresse IP locale (pour afficher l'URL a ouvrir depuis le telephone)."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 80))   # aucune donnee n'est envoyee
            return s.getsockname()[0]
    except OSError:
        return "IP-DU-PI"


def background_refresh():
    """Sur un serveur allume en permanence (Pi), les flux restent a jour meme sans visiteur."""
    while True:
        try:
            refresh()
        except Exception as e:  # noqa: BLE001
            print("collecte :", e)
        time.sleep(FEED_TTL)


def main():
    global PASSWORD
    port = int(arg("--port", 8765))
    host = arg("--host", "127.0.0.1")
    PASSWORD = arg("--password", os.environ.get("VEILLE_PASSWORD", ""))
    url = f"http://127.0.0.1:{port}/"
    try:
        srv = ThreadingHTTPServer((host, port), Handler)
    except OSError:
        print(f"Le port {port} est deja utilise : la veille tourne surement deja. Ouverture de {url}")
        webbrowser.open(url)
        return
    print("=" * 56)
    print("  MU-TH-UR // VEILLE AZOTH  en ligne")
    print(f"  Sur cette machine : {url}")
    if host != "127.0.0.1":
        print(f"  Depuis le reseau  : http://{lan_ip()}:{port}/")
        print("  Mot de passe      : " + ("actif" if PASSWORD else "AUCUN  (conseille : --password ...)"))
    print("  Ferme cette fenetre (ou Ctrl+C) pour arreter.")
    print("=" * 56)
    threading.Thread(target=background_refresh, daemon=True).start()
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, webbrowser.open, args=(url,)).start()
    print(time.strftime("%d/%m/%Y %H:%M:%S"), "demarrage")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    print(time.strftime("%d/%m/%Y %H:%M:%S"), "arret")


if __name__ == "__main__":
    main()
