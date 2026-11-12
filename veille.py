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
import http.client
import json
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
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
RACK_FILE = ROOT / "config" / "rack.json"

FEED_TTL = 15 * 60          # secondes avant de re-telecharger un flux
CRYPTO_TTL = 5 * 60
MAX_PER_SOURCE = 40
MAX_AGE_DAYS = 45
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VeilleAzoth/3.0"
COINS = "bitcoin,monero,dogecoin"   # identifiants CoinGecko, separes par des virgules
SLOW_HOSTS = {"www.reddit.com": 3.0}  # site -> pause (s) entre deux flux du meme site
SLOW_FORCE_TTL = 3600              # un rafraichissement force ne contourne pas le TTL lent
PASSWORD = ""                         # rempli par --password ou VEILLE_PASSWORD
QUANT_PROXY_URL = os.environ.get("QUANT_PROXY_URL", "http://127.0.0.1:3000").rstrip("/")
SUPERIA_PROXY_URL = os.environ.get("SUPERIA_PROXY_URL", "http://127.0.0.1:3210").rstrip("/")

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


def load_rack():
    """Charge le registre public du rack et vérifie sa structure minimale."""
    rack = json.loads(RACK_FILE.read_text(encoding="utf-8"))
    if not isinstance(rack, dict) or rack.get("schema_version") != 1:
        raise ValueError("version de manifeste du rack invalide")
    if not isinstance(rack.get("system"), dict) or not isinstance(rack.get("modules"), list):
        raise ValueError("manifeste du rack incomplet")
    for module in rack["modules"]:
        if not isinstance(module, dict) or not all(isinstance(module.get(key), str) for key in ("id", "name", "status")):
            raise ValueError("entrée de module invalide dans le rack")
        if not isinstance(module.get("capabilities"), list) or not all(isinstance(value, str) for value in module["capabilities"]):
            raise ValueError("capacités invalides dans le rack")
        if not isinstance(module.get("notes", []), list):
            raise ValueError("notes invalides dans le rack")
    return rack


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


def probe(url, expected_key=None):
    """Sonde un service local connu sans transmettre de secret."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=1.5) as response:
            payload = json.loads(response.read(64_000) or b"{}")
        return {"online": response.status < 400,
                "detail": payload.get(expected_key) if expected_key else None}
    except (OSError, ValueError, urllib.error.URLError):
        return {"online": False, "detail": None}


def cockpit_status():
    """État minimal des briques du cockpit, toutes sondées côté serveur."""
    ollama = probe("http://127.0.0.1:11434/api/version", "version")
    superia_url = os.environ.get("SUPERIA_WEB_URL", "http://127.0.0.1:3210").rstrip("/")
    superia = probe(f"{superia_url}/healthz")
    trading_url = os.environ.get("QUANT_CORE_URL", "http://127.0.0.1:3000").rstrip("/")
    trading = probe(f"{trading_url}/api/health")
    vault_value = os.environ.get("AZOTH_VAULT_PATH", "").strip()
    vault = Path(vault_value).expanduser() if vault_value else None
    return {
        "watch": {"online": True, "detail": f"{len(sources)} sources"},
        "trading": {**trading, "mode": "dry-run"},
        "ai": {**ollama, "workspace_online": superia["online"]},
        "vault": {"online": bool(vault and vault.is_dir()),
                  "detail": "coffre monté" if vault and vault.is_dir() else "miroir local non monté"},
    }


def rack_with_runtime(rack, status):
    """Ajoute au manifeste les sondes locales sans publier de chemins privés."""
    observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    checks = {
        "inference.ollama": (status["ai"]["online"], "API Ollama"),
        "workspace.superia": (status["ai"]["workspace_online"], "API Super IA"),
        "trading.freqtrade": (status["trading"]["online"], "API Quant Core"),
        "knowledge.obsidian": (status["vault"]["online"], "Montage Obsidian"),
        "watch.veille": (True, "Serveur Veille Azoth"),
    }
    payload = {**rack, "runtime": {"observed_at": observed_at}}
    payload["modules"] = []
    for module in rack["modules"]:
        entry = dict(module)
        check = checks.get(module["id"])
        if check:
            online, label = check
            detail = label
            if module["id"] == "inference.ollama" and status["ai"].get("detail"):
                detail = f"{label} · version {status['ai']['detail']}"
            entry["runtime"] = {
                "status": "online" if online else "offline",
                "label": "EN LIGNE" if online else "HORS LIGNE",
                "detail": detail,
            }
        else:
            entry["runtime"] = {
                "status": "not_probed", "label": "NON SONDE",
                "detail": "Aucune sonde runtime n’est configurée pour ce module.",
            }
        payload["modules"].append(entry)
    return payload


class CapabilityInputError(ValueError):
    """Entrée d'appel invalide, distincte d'une panne du service amont."""


CAPABILITY_SPECS = {
    "ai.models.list": {
        "description": "Lister les modèles présents dans le catalogue Ollama local.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    "watch.articles.search": {
        "description": "Rechercher dans les articles déjà mis en cache par la veille.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 2, "maxLength": 120},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            "required": ["query"], "additionalProperties": False,
        },
    },
    "trading.status.read": {
        "description": "Lire l'état de santé de Quant Core et son mode déclaré.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}


def rack_capabilities(rack):
    """Expose les capacités déclarées et indique lesquelles ont un adaptateur sûr."""
    items = []
    for module in rack["modules"]:
        for capability in module["capabilities"]:
            spec = CAPABILITY_SPECS.get(capability)
            items.append({
                "id": capability,
                "module": module["id"],
                "description": spec["description"] if spec else "Capacité déclarée, adaptateur non raccordé.",
                "state": "callable" if spec and capability in CAPABILITY_HANDLERS else "declared",
                "permission": "read_only" if spec and capability in CAPABILITY_HANDLERS else "not_granted",
                "side_effects": [],
                "input_schema": spec["input_schema"] if spec else None,
            })
    return {"capabilities": items}


def search_cached_articles(query, limit=10):
    """Recherche locale bornée; ne rafraîchit pas les flux et ne suit aucun lien."""
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 120:
        raise CapabilityInputError("query doit contenir entre 2 et 120 caractères")
    if type(limit) is not int or not 1 <= limit <= 20:
        raise CapabilityInputError("limit doit être un entier entre 1 et 20")
    terms = query.casefold().split()
    if len(terms) > 10:
        raise CapabilityInputError("query contient trop de termes")
    with lock:
        entries = list(cache.values())
    matches = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("items"), list):
            continue
        for item in entry["items"]:
            if not isinstance(item, dict):
                continue
            article_id = item.get("id")
            link = item.get("link", "")
            if not isinstance(article_id, str) or not article_id or article_id in seen or not isinstance(link, str) or not link.startswith(("https://", "http://")):
                continue
            haystack = " ".join(str(item.get(key, "")) for key in ("title", "summary", "source", "cat")).casefold()
            if all(term in haystack for term in terms):
                seen.add(article_id)
                matches.append({key: item.get(key) for key in ("id", "title", "summary", "link", "source", "cat", "date")})
    matches.sort(key=lambda item: item.get("date") or 0, reverse=True)
    return {"query": query.strip(), "count": len(matches), "returned": min(len(matches), limit), "items": matches[:limit], "cached_only": True}


def list_ollama_models():
    req = urllib.request.Request("http://127.0.0.1:11434/api/tags", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=3) as response:
        payload = json.loads(response.read(256_000) or b"{}")
    models = payload.get("models")
    if not isinstance(models, list):
        raise ValueError("catalogue Ollama invalide")
    items = []
    for model in models[:100]:
        if not isinstance(model, dict) or not isinstance(model.get("name"), str):
            continue
        details = model.get("details") if isinstance(model.get("details"), dict) else {}
        items.append({
            "name": model["name"],
            "family": details.get("family"),
            "parameter_size": details.get("parameter_size"),
            "quantization": details.get("quantization_level"),
        })
    return {"models": items}


def read_trading_status():
    base = os.environ.get("QUANT_CORE_URL", "http://127.0.0.1:3000").rstrip("/")
    status = probe(f"{base}/api/health")
    return {"online": status["online"], "declared_mode": "dry-run", "detail": "API Quant Core"}


def _call_models(arguments):
    if arguments:
        raise CapabilityInputError("aucun paramètre accepté")
    return list_ollama_models()


def _call_article_search(arguments):
    return search_cached_articles(arguments["query"], arguments.get("limit", 10))


def _call_trading_status(arguments):
    if arguments:
        raise CapabilityInputError("aucun paramètre accepté")
    return read_trading_status()


CAPABILITY_HANDLERS = {
    "ai.models.list": _call_models,
    "watch.articles.search": _call_article_search,
    "trading.status.read": _call_trading_status,
}


def validate_capability_input(capability, arguments):
    if not isinstance(arguments, dict):
        raise CapabilityInputError("input doit être un objet JSON")
    schema = CAPABILITY_SPECS[capability]["input_schema"]
    properties = schema["properties"]
    if not schema.get("additionalProperties", True) and set(arguments) - set(properties):
        raise CapabilityInputError("paramètre inconnu")
    if set(schema.get("required", [])) - set(arguments):
        raise CapabilityInputError("paramètre requis manquant")
    for key, value in arguments.items():
        field = properties.get(key)
        if field is None:
            continue
        expected = field["type"]
        valid_type = (isinstance(value, str) if expected == "string" else
                      type(value) is int if expected == "integer" else
                      isinstance(value, dict) if expected == "object" else False)
        if not valid_type:
            raise CapabilityInputError(f"{key} doit être de type {expected}")
        if expected == "string" and not field.get("minLength", 0) <= len(value) <= field.get("maxLength", len(value)):
            raise CapabilityInputError(f"{key} a une longueur invalide")
        if expected == "integer" and not field.get("minimum", value) <= value <= field.get("maximum", value):
            raise CapabilityInputError(f"{key} est hors limites")


def call_rack_capability(capability, arguments):
    """Exécute uniquement les adaptateurs déclarés ici; aucun nom de fonction dynamique."""
    started = time.monotonic()
    def failure(code, status, message):
        return status, {
            "capability": capability if isinstance(capability, str) else None,
            "status": "error", "data": None,
            "error": {"code": code, "message": message},
            "duration_ms": round((time.monotonic() - started) * 1000),
        }

    if not isinstance(capability, str) or not capability:
        return failure("invalid_capability", 400, "Identifiant de capacité requis.")
    try:
        declared = {item["id"] for item in rack_capabilities(load_rack())["capabilities"]}
    except (OSError, ValueError, KeyError):
        return failure("registry_unavailable", 503, "Registre des capacités indisponible.")
    if capability not in declared:
        return failure("unknown_capability", 404, "Capacité inconnue.")
    handler = CAPABILITY_HANDLERS.get(capability)
    if capability not in CAPABILITY_SPECS or handler is None:
        return failure("not_connected", 409, "Cette capacité est déclarée, mais son adaptateur n'est pas raccordé.")
    try:
        validate_capability_input(capability, arguments)
        result = handler(arguments)
    except CapabilityInputError as error:
        return failure("invalid_input", 400, str(error))
    except (OSError, urllib.error.URLError, ValueError):
        return failure("upstream_unavailable", 503, "Le service requis ne répond pas.")
    return 200, {
        "capability": capability, "status": "ok", "data": result,
        "error": None, "duration_ms": round((time.monotonic() - started) * 1000),
    }


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
    force=True ignore le cache, sauf pour les sites lents avant leur TTL configure (au moins 1 h)."""
    with lock:
        active = [s for s in sources if s.get("on", True)]
    with refresh_lock:
        now = time.time()

        def stale(s):
            age = now - cache.get(s["id"], {}).get("fetched", 0)
            if force:
                slow = urllib.parse.urlparse(s["url"]).netloc in SLOW_HOSTS
                return age > (max(SLOW_FORCE_TTL, s.get("ttl", FEED_TTL)) if slow else 0)
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
        """Basic Auth pour les routes publiques; exception loopback sur le pont RACK en lecture."""
        if self.is_internal_rack_caller():
            return True
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

    def is_internal_rack_caller(self):
        """Autorise le pont Super IA uniquement en loopback, sans en-têtes de proxy/web."""
        if urllib.parse.urlparse(self.path).path != "/api/rack/internal/call":
            return False
        address = self.client_address[0]
        return (address in {"127.0.0.1", "::1"}
                and not self.headers.get("Origin")
                and not self.headers.get("Forwarded")
                and not self.headers.get("X-Forwarded-For"))

    def deny(self):
        self.send(401, {"error": "mot de passe requis"},
                  extra={"WWW-Authenticate": 'Basic realm="Veille Azoth", charset="UTF-8"'})

    def log_message(self, fmt, *args):  # console plus calme
        message = fmt % args
        request_line = str(args[0]) if args else ""
        if "/api/" in request_line and " 200 " not in message:
            sys.stderr.write("%s\n" % message)

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

    def body(self, max_bytes=2_000_000):
        n = int(self.headers.get("Content-Length") or 0)
        if n < 0 or n > max_bytes:
            raise ValueError("requete trop grosse")
        return json.loads(self.rfile.read(n) or b"{}")

    def same_origin(self):
        # Protege l'API locale contre les requetes envoyees par d'autres sites.
        origin = self.headers.get("Origin")
        return origin is None or origin == f"http://{self.headers.get('Host')}"

    @staticmethod
    def inject_assistant_overlay(payload):
        """Ajoute le client partagé sans dépendre du framework de la page."""
        marker = b'<script src="/assistant-overlay.js" defer></script>'
        if marker in payload:
            return payload
        lowered = payload.lower()
        index = lowered.rfind(b"</body>")
        return payload[:index] + marker + payload[index:] if index >= 0 else payload + marker

    def proxy_quant(self):
        """Passe Quant Core derrière l'authentification unique du cockpit."""
        target = urllib.parse.urlparse(QUANT_PROXY_URL)
        length = int(self.headers.get("Content-Length") or 0)
        if length > 2_000_000:
            return self.send(413, {"error": "requête trop grosse"})
        body = self.rfile.read(length) if length else None
        forwarded = {}
        for key, value in self.headers.items():
            if key.lower() not in {"authorization", "connection", "host", "content-length", "transfer-encoding"}:
                forwarded[key] = value
        forwarded["Host"] = target.netloc
        forwarded["X-Forwarded-Host"] = self.headers.get("Host", "")
        forwarded["X-Forwarded-Proto"] = "http"
        connection = http.client.HTTPConnection(target.hostname, target.port or 80, timeout=15)
        try:
            connection.request(self.command, self.path, body=body, headers=forwarded)
            upstream = connection.getresponse()
            payload = upstream.read()
            content_type = upstream.getheader("Content-Type", "")
            if "text/html" in content_type:
                payload = self.inject_assistant_overlay(payload)
            self.send_response(upstream.status)
            for key, value in upstream.getheaders():
                if key.lower() not in {"connection", "content-length", "transfer-encoding"}:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)
        except OSError:
            self.send(502, {"error": "Quant Core indisponible"})
        finally:
            connection.close()

    def proxy_superia(self):
        """Expose Super IA sous /ia/ après l'unique contrôle d'accès du cockpit."""
        target = urllib.parse.urlparse(SUPERIA_PROXY_URL)
        length = int(self.headers.get("Content-Length") or 0)
        if length > 2_000_000:
            return self.send(413, {"error": "requête trop grosse"})
        body = self.rfile.read(length) if length else None
        upstream_path = self.path[3:] or "/"
        forwarded = {}
        for key, value in self.headers.items():
            if key.lower() not in {"authorization", "connection", "host", "content-length", "transfer-encoding"}:
                forwarded[key] = value
        forwarded["Host"] = target.netloc
        # Les modèles locaux peuvent prendre plus d'une minute sur le premier
        # chargement. Le serveur Super IA borne lui-même les appels à 120 s.
        connection = http.client.HTTPConnection(target.hostname, target.port or 80, timeout=130)
        try:
            connection.request(self.command, upstream_path, body=body, headers=forwarded)
            upstream = connection.getresponse()
            content_type = upstream.getheader("Content-Type", "")
            if "text/event-stream" in content_type:
                self.send_response(upstream.status)
                for key, value in upstream.getheaders():
                    if key.lower() not in {"connection", "content-length", "transfer-encoding", "content-encoding"}:
                        self.send_header(key, value)
                self.send_header("Cache-Control", "no-cache, no-transform")
                self.send_header("X-Accel-Buffering", "no")
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                if self.command != "HEAD":
                    while True:
                        chunk = upstream.read1(4096)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                return
            payload = upstream.read()
            if "text/html" in content_type:
                page = payload.decode("utf-8")
                page = page.replace("'/api", "'/ia/api").replace("\"/api", "\"/ia/api")
                page = page.replace('action="/logout"', 'action="/ia/logout"')
                page = page.replace('action="/session"', 'action="/ia/session"')
                page = page.replace("'/login'", "'/ia/login'")
                payload = self.inject_assistant_overlay(page.encode("utf-8"))
            self.send_response(upstream.status)
            for key, value in upstream.getheaders():
                lowered = key.lower()
                if lowered in {"connection", "content-length", "transfer-encoding"}:
                    continue
                if lowered == "location" and value.startswith("/"):
                    value = "/ia" + value
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)
        except OSError:
            if self.command == "GET" and upstream_path == "/":
                page = """<!doctype html><html lang=\"fr\"><head><meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>Super IA indisponible</title><style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#030604;color:#c9f5d6;font:14px/1.6 ui-monospace,monospace}
main{max-width:660px;margin:24px;padding:28px;border:1px solid #143521;background:#07100a}
h1{color:#ffb53d;font-size:28px}code{color:#3dff7f}a{color:#3dff7f}
</style></head><body><main><h1>SUPER IA // HORS LIGNE</h1>
<p>Le module est bien installé, mais son service local ne répond pas sur le port 3210.</p>
<p>Sur la machine Azoth : <code>systemctl --user restart superia-web.service</code></p>
<p>Puis contrôler : <code>curl -fsS http://127.0.0.1:3210/healthz</code></p>
<p><a href=\"/\">← Retour au cockpit</a></p></main></body></html>""".encode("utf-8")
                self.send_response(502)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)
            else:
                self.send(502, {"error": "Super IA indisponible"})
        finally:
            connection.close()

    def do_GET(self):
        if not self.authorized():
            return self.deny()
        u = urllib.parse.urlparse(self.path)
        if u.path == "/quant":
            self.send_response(308)
            self.send_header("Location", "/quant/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if u.path.startswith("/quant/"):
            return self.proxy_quant()
        if u.path == "/ia":
            self.send_response(308)
            self.send_header("Location", "/ia/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if u.path.startswith("/ia/"):
            return self.proxy_superia()
        q = urllib.parse.parse_qs(u.query)
        if u.path == "/api/rack":
            try:
                rack = load_rack()
                return self.send(200, rack_with_runtime(rack, cockpit_status()))
            except (OSError, ValueError, KeyError) as e:
                sys.stderr.write(f"registre du rack indisponible: {type(e).__name__}\n")
                return self.send(503, {"error": "registre du rack indisponible"})
        if u.path == "/api/rack/capabilities":
            try:
                return self.send(200, rack_capabilities(load_rack()))
            except (OSError, ValueError, KeyError):
                return self.send(503, {"error": "registre des capacités indisponible"})
        if u.path == "/api/feeds":
            return self.send(200, refresh(force=q.get("force") == ["1"]))
        if u.path == "/api/crypto":
            return self.send(200, crypto())
        if u.path == "/api/config":
            with lock:
                return self.send(200, {"sources": sources, "state": state})
        if u.path == "/api/cockpit/status":
            return self.send(200, cockpit_status())
        if u.path == "/api/opml":
            return self.send(200, opml(), "text/x-opml; charset=utf-8",
                             {"Content-Disposition": 'attachment; filename="veille-tssr.opml"'})
        path = "index.html" if u.path in ("", "/") else u.path.lstrip("/")
        f = (WEB / path).resolve()
        if WEB not in f.parents or not f.is_file():
            return self.send(404, {"error": "introuvable"})
        return self.send(200, f.read_bytes(), MIME.get(f.suffix, "application/octet-stream"))

    def do_HEAD(self):
        """Répond aux contrôles de disponibilité sans envoyer de contenu."""
        if not self.authorized():
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="Veille Azoth", charset="UTF-8"')
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/quant", "/ia"):
            self.send_response(308)
            self.send_header("Location", u.path + "/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if u.path.startswith("/quant/"):
            return self.proxy_quant()
        if u.path.startswith("/ia/"):
            return self.proxy_superia()
        path = "index.html" if u.path in ("", "/") else u.path.lstrip("/")
        f = (WEB / path).resolve()
        if WEB not in f.parents or not f.is_file():
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(f.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(f.stat().st_size))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_POST(self):
        if not self.authorized():
            return self.deny()
        if urllib.parse.urlparse(self.path).path.startswith("/quant/"):
            return self.proxy_quant()
        if urllib.parse.urlparse(self.path).path.startswith("/ia/"):
            return self.proxy_superia()
        if not self.same_origin():
            return self.send(403, {"error": "origine refusee"})
        path = urllib.parse.urlparse(self.path).path
        try:
            data = self.body(16_384 if path in {"/api/rack/call", "/api/rack/internal/call"} else 2_000_000)
        except ValueError as e:
            return self.send(400, {"error": str(e)})
        if path in {"/api/rack/call", "/api/rack/internal/call"}:
            if path == "/api/rack/internal/call" and not self.is_internal_rack_caller():
                return self.send(403, {"error": "appel interne refusé"})
            if not isinstance(data, dict):
                return self.send(400, {"error": "le corps doit être un objet JSON"})
            status, result = call_rack_capability(data.get("capability"), data.get("input", {}))
            return self.send(status, result)
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

    def do_PUT(self):
        if not self.authorized():
            return self.deny()
        if urllib.parse.urlparse(self.path).path.startswith("/quant/"):
            return self.proxy_quant()
        if urllib.parse.urlparse(self.path).path.startswith("/ia/"):
            return self.proxy_superia()
        return self.send(404, {"error": "route inconnue"})

    def do_DELETE(self):
        if not self.authorized():
            return self.deny()
        if urllib.parse.urlparse(self.path).path.startswith("/quant/"):
            return self.proxy_quant()
        if urllib.parse.urlparse(self.path).path.startswith("/ia/"):
            return self.proxy_superia()
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
