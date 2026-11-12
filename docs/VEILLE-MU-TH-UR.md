# MU-TH-UR // Veille Azoth

Tableau de bord personnel de **veille technologique** d'Azoth, technicien supérieur systèmes et réseaux (TSSR) en formation, maker et musicien.

Il rassemble en direct **100 sources** (flux RSS, versions GitHub) réparties en deux familles :

- **PRO (TSSR)** : alertes de sécurité, cyber et piratage, systèmes (dont Omarchy / Arch et Pop!_OS), réseau, homelab, cloud, chiffrement ;
- **PERSO** : firmwares alternatifs, maker (Teensy, ESP32, Raspberry Pi), musique (OP-1, EP-133 K.O. II), photo (Olympus OM-D E-M5 II, argentique), rétro et jeux, drones et radio, IA, crypto et trading, matos.

L'outil affiche aussi les **cours BTC / Monero / Dogecoin**. Il fait remonter les **alertes de sécurité** qui te concernent et repère tes sujets personnels avec le badge **◆ POUR TOI**.

Ambiance : terminal phosphore façon *Matrix* / *MU-TH-UR 6000* (Alien), avec l'œil de *HAL 9000*.

---

## Sommaire

1. [Démarrer sur Windows](#1-démarrer-sur-windows)
2. [L'écran, zone par zone](#2-lécran-zone-par-zone)
3. [Alertes et « Pour toi » : les règles](#3-alertes-et--pour-toi---les-règles)
4. [Les sources](#4-les-sources)
5. [Méthode : 15 minutes par jour](#5-méthode--15-minutes-par-jour)
6. [Installer sur un Raspberry Pi](#6-installer-sur-un-raspberry-pi)
7. [Utiliser un autre lecteur RSS](#7-utiliser-un-autre-lecteur-rss)
8. [Fichiers du projet](#8-fichiers-du-projet)
9. [Fonctionnement technique](#9-fonctionnement-technique)
10. [Dépannage](#10-dépannage)

---

## 1. Démarrer sur Windows

**Prérequis :** Python 3.9 ou plus récent (installé sur ton PC : 3.12). Rien d'autre à installer : l'outil n'utilise que la bibliothèque standard de Python.

### En un clic (usage normal)

1. **Une seule fois :** double-clique sur **`Installer-Raccourcis.bat`**. Il crée l'icône **Veille Azoth** (l'œil de HAL) sur le Bureau et dans le menu Démarrer.
2. **Ensuite :** clique sur l'icône **Veille Azoth**. La veille démarre **sans fenêtre noire** et le navigateur s'ouvre sur <http://127.0.0.1:8765>.
   Si elle tourne déjà, le clic rouvre simplement la page.
3. **Pour l'arrêter :** bouton **⏻** en haut à droite du tableau de bord.

Sans fenêtre, les messages du serveur sont écrits dans `data\veille.log`.
Si tu déplaces le dossier `veille-azoth`, relance `Installer-Raccourcis.bat`.

### Avec la console (pour dépanner)

Double-clique sur **`Lancer-Veille.bat`** : même chose, mais avec une fenêtre noire qui affiche les messages. Fermer cette fenêtre arrête la veille.

En ligne de commande :

```
python veille.py                              # usage normal
python veille.py --port 9000                  # autre port
python veille.py --host 0.0.0.0 --password X  # accessible depuis le téléphone (même Wi-Fi)
python veille.py --no-browser                 # sans ouvrir le navigateur
```

> Astuce : fais un raccourci de `Lancer-Veille.bat` sur le bureau, ou place-le dans `shell:startup` (Win + R) pour que la veille démarre avec Windows.

---

## 2. L'écran, zone par zone

| Zone | Rôle |
|---|---|
| **Œil de HAL** (en haut à gauche) | Force le rafraîchissement de toutes les sources. Il pulse pendant la collecte (une vingtaine de secondes). |
| **Bandeau crypto** | Prix en euros, variation sur 24 h et 7 jours, mini-courbe sur 7 jours (CoinGecko, mise à jour toutes les 5 min). |
| **État du système** | Articles parus depuis ta dernière visite, alertes, articles « pour toi », sources en ligne. |
| **Onglets, ligne 1** | `Tout`, `Priorité` (toutes les alertes), `Pour toi` (tes sujets), `Favoris`. |
| **Onglets PRO / PERSO** | Le bouton en pointillés regroupe toute la famille, puis une catégorie par bouton. Le chiffre indique les **non lus**. |
| **Filtres** | Recherche texte, période (24 h → tout), « non lus », « nouveaux », « tout lu » (marque la vue affichée comme lue). |
| **Article** | Clic sur le titre : ouvre l'article dans un nouvel onglet et le marque comme lu. ☆ = favori, ✓ = lu / non lu. Bordure rouge = alerte, violette = pour toi. Les CVE citées renvoient vers cve.org. |
| **Alertes prioritaires** (panneau rouge) | Ce qui est urgent sur les 7 derniers jours. |
| **Dernières versions** | La version actuelle de chaque firmware ou logiciel suivi, avec son âge. En vert : sortie depuis moins de 30 jours. |
| **◆ Mes sujets** (violet) | Ton matériel et tes passions. Ajoute ou retire des mots. |
| **Mots surveillés** | Les produits professionnels dont une faille doit t'alerter. |
| **Sources** | Point vert = OK, orange = rien de neuf récemment, rouge = erreur (survole pour lire le détail). ⏸ met en pause, × supprime. « + Ajouter un flux RSS » teste le flux avant de l'ajouter. |
| **⇩ Synthèse** | Fichier Markdown : alertes de la semaine, nouvelles versions de firmwares, favoris classés par catégorie, avec des lignes « Ce que j'en retiens » et « Action » à compléter. |
| **⇩ OPML** | Exporte toutes tes sources (voir §7). |
| **⁂ Matrix** | Active ou coupe la pluie de caractères en fond. |
| **⏻** | Arrête la veille (le serveur local). |

L'affichage se rafraîchit automatiquement toutes les 15 minutes. Favoris, articles lus, sujets et mots surveillés sont enregistrés dans `data/state.json`.

**Raccourcis clavier :** `/` rechercher · `R` rafraîchir · `J` / `K` article suivant / précédent · `O` ouvrir · `F` favori · `L` lu / non lu · `Échap` quitter la recherche.

---

## 3. Alertes et « Pour toi » : les règles

### Une alerte (rouge) se déclenche si :

1. l'article vient de **CERT-FR Alertes** (alertes officielles, rares et importantes) ;
2. **ou** il cite un de tes **mots surveillés** (Windows Server, Proxmox, OpenSSH, Cisco…) **et** il traite de sécurité : soit il vient d'une source sécurité (Alertes, Cyber), soit son titre parle de faille, de correctif, d'attaque ou de vulnérabilité.
   Ainsi, une simple discussion « Proxmox » sur r/homelab ne sonne pas ;
3. **ou**, dans une catégorie technique, son titre contient un mot critique :
   *critique, 0-day, exploité, ransomware, backdoor, fuite de données, RCE, remote code execution, manual intervention…*
   « Manual intervention » attrape les annonces **Arch Linux** à lire **avant** de mettre à jour Omarchy.

### Le badge « ◆ POUR TOI » (violet) apparaît si :

l'article cite un de **tes sujets** (Teensy, OP-1, EP-133, E-M5, Meshtastic, Omarchy…) **dans une source qui n'est pas dédiée à ce sujet**.
Tout ce que publie le forum Teensy parle de Teensy, donc il ne reçoit pas le badge « Teensy ». En revanche, un article Hackaday sur un synthé à base de Teensy le reçoit.
Le badge sert à repérer ton matériel dans le flot général.

Les mots sont reconnus **en mot entier** : « LoRa » ne se déclenche pas dans « Flora », ni « OP-1 » dans « OP-10 ».

Les listes de mots critiques (`HOT`) et de vocabulaire sécurité (`SEC`) sont modifiables en haut de `dist/app.js`.

---

## 4. Les sources

Toutes ont été testées le 09/11/2026.

### PRO (TSSR)

| Catégorie | Sources |
|---|---|
| **Alertes** | CERT-FR Alertes, CERT-FR Avis, Ubuntu Security Notices, Debian Security (DSA) |
| **Cyber & piratage** | CERT-FR Actualités, SANS Internet Storm Center, BleepingComputer, The Hacker News, Zataz, Krebs on Security, Numerama Cyberguerre, Cisco Talos |
| **Systèmes** | IT-Connect, LeMagIT, Windows Blog, LWN.net, LinuxFr, Korben, **Arch Linux News**, **Omarchy**, **Hyprland**, **Pop!_OS COSMIC**, r/pop_os |
| **Réseau** | Blog de Stéphane Bortzmeyer (DNS, protocoles), Cloudflare Blog, APNIC Blog, RIPE Labs, Netgate (pfSense) |
| **Homelab** | selfh.st, Proxmox (annonces), Docker Blog, r/homelab (top du jour) |
| **Cloud** | AWS What's New, Azure Updates, Google Cloud Blog (15 articles max chacun : ces flux sont très bavards) |
| **Chiffrement** | Let's Encrypt, Schneier on Security |

### PERSO

| Catégorie | Sources |
|---|---|
| **Firmwares** | OP-1 : op1repacker (mods du firmware OP-1), Magic Lantern (Canon), Teensy (cores PJRC), ESP-IDF, Meshtastic, ExpressLRS, EdgeTX, Betaflight, Flipper Zero Momentum et Unleashed, OpenWrt, OPNsense, Tasmota, ESPHome |
| **Maker** | Hackaday, CNX Software, Raspberry Pi News, Forum PJRC (Teensy), Adafruit, Arduino |
| **Musique** | op-forums OP-1, op-forums EP-133 K.O. II, r/teenageengineering, r/synthdiy, Elektronauts, Synthtopia, CDM, Audiofanzine, Gearnews FR, MusicRadar, Strudel, Dexed |
| **Photo** | 43rumors (Olympus / OM System), r/M43, Phototrend, PetaPixel, DPReview, Kosmo Foto, 35mmc, Emulsive (argentique), darktable |
| **Rétro & jeux** | Time Extension, RetroRGB, Libretro / RetroArch, Amiberry (Amiga), mGBA (Game Boy), Godot Engine |
| **Drones & radio** | Oscar Liang (FPV), Meshtastic Blog, RTL-SDR Blog |
| **IA** | Simon Willison, Ollama |
| **Crypto & trading** | CoinDesk, Cointelegraph, Journal du Coin, Bitcoin Magazine, Monero (officiel), r/dogecoin, Freqtrade |
| **Matos** | Tom's Hardware FR, Les Numériques, ServeTheHome, Phoronix |

### Ce qu'il faut savoir sur les firmwares alternatifs de ton matériel

- **OP-1 (premier du nom)** : il n'existe pas de firmware alternatif complet. Le seul outil communautaire est **op1repacker**, qui modifie le firmware officiel (graphismes, presets, fonctions cachées). Il est suivi dans Firmwares. Les nouveautés passent surtout par op-forums.
- **EP-133 K.O. II** : pas de firmware alternatif connu. Les mises à jour officielles de Teenage Engineering et les astuces de la communauté arrivent via **op-forums EP-133** et r/teenageengineering.
- **Olympus OM-D E-M5 Mark II** : **aucun firmware alternatif n'existe** (pas d'équivalent de Magic Lantern chez Olympus). La veille passe par **43rumors** et **r/M43**, plus les mots « E-M5 », « OM System » et « M.Zuiko » dans tes sujets.
- **Canon** : **Magic Lantern** est suivi, si tu ressors un boîtier Canon compatible.
- **Teensy** : pas de firmware au sens strict, mais les versions des **cores PJRC** (Teensyduino) et le forum officiel sont suivis.

### Écartées (ne répondent pas proprement)

CISA (bloque les robots), Microsoft MSRC (flux mal formé), Cisco Blogs (certificat invalide), Cowcotland (flux introuvable), Cybermalveillance.gouv.fr et n8n (chaîne de certificats incomplète côté serveur), ANSSI (protection anti-robot), Pitchfork et Fstoppers (hors de ton profil).

### Ajouter une source

- **Depuis l'interface** : panneau Sources → « + Ajouter un flux RSS ». L'outil télécharge le flux et te dit combien d'articles il a trouvés.
- **À la main** : édite `sources.json` (serveur arrêté). Une entrée par flux :
  ```json
  {"name": "Mon site", "url": "https://exemple.fr/feed/", "cat": "Maker", "on": true}
  ```
  Options : `"ttl": 3600` (secondes entre deux téléchargements), `"max": 15` (articles gardés), `"days": 90` (âge maximum).
  `cat` doit être une catégorie listée dans `GROUPS` en haut de `dist/app.js`, sinon elle n'aura pas d'onglet.

**Trouver le flux d'un site :** essaie `/feed`, `/rss`, `/feed.xml` ou `/rss.xml` après l'adresse du site. Les sites WordPress ont presque toujours `/feed/`.

**Suivre les versions d'un projet GitHub :** `https://github.com/AUTEUR/PROJET/releases.atom`, ou `tags.atom` si le projet ne publie pas de « releases ». Ces flux gardent leurs 5 dernières versions quel que soit leur âge, apparaissent dans « Dernières versions », et les « nightly » sont ignorées.

**Forum Discourse** (op-forums, Elektronauts…) : ajoute `.rss` à l'adresse d'une catégorie, par exemple `https://op-forums.com/c/ep-133/34.rss`.

---

## 5. Méthode : 15 minutes par jour

La veille est un cycle : **sources → collecte → tri → exploitation → partage**. L'outil automatise les deux premières étapes ; à toi les suivantes.

1. **Alertes** (2 min) : panneau rouge. Un produit que tu utilises est touché ? Note la CVE et cherche le correctif. Annonce Arch Linux ? Lis-la avant ton prochain `pacman -Syu` sous Omarchy.
2. **PRO** (6 min) : onglet `PRO` + case « nouveaux ». Parcours avec `J` / `K`, mets en favori (`F`) ce qui sert ton métier, puis « tout lu ».
3. **Pour toi** (2 min) : ton matériel cité ailleurs.
4. **PERSO** (5 min) : firmwares, musique, photo, maker… pour le plaisir.
5. **Une fois par semaine** : **⇩ Synthèse**. Complète « Ce que j'en retiens » et « Action » pour chaque favori. Ces fiches alimentent ton **dossier professionnel** et ta préparation à l'oral du titre TSSR.

Pense à mettre dans **Mots surveillés** les produits de ton stage ou de ton entreprise (pare-feu, hyperviseur, logiciel de sauvegarde…).

---

## 6. Installer sur un Raspberry Pi

Sur un Pi allumé en permanence, la veille collecte 24 h/24 et tu la consultes depuis ton téléphone ou n'importe quel PC du réseau. Tous les modèles conviennent (Zero 2 W, 3, 4, 5), pour 3 à 5 W de consommation.

```bash
# depuis ton PC : copier le dossier sur le Pi
scp -r veille-azoth azoth@IP-DU-PI:~/

# sur le Pi (en SSH)
cd ~/veille-azoth
bash pi/install-pi.sh
```

Le script :

1. vérifie Python 3 (déjà présent sur Raspberry Pi OS) ;
2. te demande un **mot de passe**, stocké dans `/etc/veille-azoth.env` (lisible par root seulement) ;
3. installe le **service systemd** `veille-azoth` : démarrage automatique et redémarrage en cas de plantage, avec des droits limités au dossier de la veille ;
4. ouvre le port 8765 au réseau local dans le pare-feu **ufw**, s'il est actif ;
5. affiche l'adresse à ouvrir : `http://IP-DU-PI:8765`.

Le navigateur demande alors un identifiant et un mot de passe : l'identifiant est libre, seul le mot de passe compte.

| Action | Commande |
|---|---|
| État du service | `systemctl status veille-azoth` |
| Journal en direct | `journalctl -u veille-azoth -f` |
| Redémarrer après une modification | `sudo systemctl restart veille-azoth` |
| Changer le mot de passe | `sudo nano /etc/veille-azoth.env` puis redémarrer |
| Désinstaller | `sudo systemctl disable --now veille-azoth && sudo rm /etc/systemd/system/veille-azoth.service` |

**Accès hors de la maison :** n'ouvre pas de port sur ta box. Installe plutôt **Tailscale** (VPN gratuit) sur le Pi et sur ton téléphone. C'est plus simple et bien plus sûr, car le mot de passe circule en clair en HTTP. Pour aller plus loin : un reverse proxy (Caddy ou Nginx) avec HTTPS.

**Pistes pour la suite :** notifications sur ton téléphone quand une alerte critique tombe (ntfy, Telegram, Discord), synthèse envoyée par mail chaque matin, tableau Grafana des sources.

---

## 7. Utiliser un autre lecteur RSS

**⇩ OPML** exporte toutes tes sources dans le format standard d'échange entre lecteurs RSS :

| Outil | Type | Intérêt |
|---|---|---|
| **Feedly** / **Inoreader** | En ligne, gratuit avec limites | Appli mobile. Inoreader gère les règles et les mots-clés. |
| **FreshRSS** | Auto-hébergé (Docker, Debian, Proxmox) | Gratuit et complet. **L'installer sur une VM est un bon TP TSSR** (serveur web, PHP, base de données, reverse proxy, HTTPS) à valoriser dans ton dossier. |
| **Netvibes** | En ligne | Tableau de bord à widgets, courant dans les entreprises françaises. |

---

## 8. Fichiers du projet

```
veille-azoth/
├── Installer-Raccourcis.bat crée l'icône « Veille Azoth » (Bureau + menu Démarrer), à lancer une fois
├── Lancer-Veille.bat        lanceur avec console (dépannage)
├── veille.py                serveur : collecte, cache, API, mot de passe, fichiers de l'interface
├── sources.json             tes 100 sources (modifiable)
├── README.md                ce document
├── docs/
│   ├── Veille_Technologique_TSSR_Azoth.docx  méthode de veille TSSR + description de l'outil (Word)
│   ├── Veille_Technologique_TSSR_Azoth.pdf   même document en PDF (à imprimer / joindre au dossier)
│   └── capture-veille-azoth.png              capture du tableau de bord
├── outils/
│   └── creer_icone.py       régénère dist/azoth.ico (l'œil de HAL, Python pur)
├── pi/
│   ├── install-pi.sh        installation automatique sur Raspberry Pi / Debian
│   └── veille-azoth.service modèle du service systemd
├── data/                    créé au premier lancement
│   ├── cache.json           derniers articles téléchargés (affichage immédiat au démarrage)
│   ├── state.json           favoris, lus, sujets, mots surveillés, dates de visite
│   └── veille.log           journal quand la veille tourne sans fenêtre
└── dist/                    l'interface web
    ├── azoth.ico            icône (raccourci + onglet du navigateur)
    ├── index.html           structure de la page
    ├── style.css            thème visuel (couleurs en variables en haut du fichier)
    └── app.js               logique : onglets, filtres, alertes, sujets, versions, synthèse, raccourcis
```

- **Sauvegarder ta veille :** copie `sources.json` et le dossier `data/`.
- **Repartir à zéro :** supprime `data/`.

---

## 9. Fonctionnement technique

```
navigateur ──HTTP──▶ veille.py :8765 ──HTTPS──▶ 100 flux RSS / Atom / versions GitHub
 (dist/)   ◀─JSON──  cache · data/*.json ─HTTPS─▶ API CoinGecko (cours crypto)
```

- **Pourquoi un serveur ?** Un navigateur refuse qu'une page lise un flux RSS hébergé sur un autre site (règle CORS). C'est pour ça que la maquette d'origine ne pouvait afficher que des liens écrits en dur. `veille.py` fait l'intermédiaire.
- **Collecte :** un fil de fond rafraîchit les flux toutes les 15 minutes, même sans visiteur. Les téléchargements se font en parallèle, sauf pour un même site : par exemple, les flux Reddit passent un par un, à 3 s d'intervalle et une fois par heure, car Reddit bloque les rafales. Si un flux tombe, ses anciens articles restent affichés.
- **Analyse :** RSS 2.0, RSS 1.0 (RDF) et Atom, avec une lecture de secours pour les flux mal formés. Le HTML est retiré des résumés, coupés à 320 caractères.
- **Limites :** 40 articles et 45 jours par source. Les flux de versions gardent leurs 5 dernières sorties, quel que soit leur âge.
- **Sécurité :**
  - par défaut, le serveur n'écoute que sur `127.0.0.1` (invisible depuis le réseau) ;
  - `--password` active une authentification HTTP Basic (comparaison à temps constant) ;
  - les écritures venant d'un autre site sont refusées ;
  - aucun fichier hors de `dist/` n'est servi ;
  - le texte des flux est toujours échappé, et seuls les liens `http(s)` sont cliquables.

### API locale

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/feeds` (`?force=1`) | Articles triés du plus récent au plus ancien + état de chaque source |
| GET | `/api/crypto` | Cours BTC, XMR, DOGE |
| GET | `/api/config` | Sources et état utilisateur |
| GET | `/api/opml` | Export OPML |
| POST | `/api/state` | Enregistre `fav`, `read`, `watch`, `topics`, `lastVisit`, `prevVisit` |
| POST | `/api/sources/add` | `{name, url, cat}` : ajoute et teste un flux |
| POST | `/api/sources/remove` · `/api/sources/toggle` | `{id}` : supprime ou met en pause |
| POST | `/api/shutdown` | Arrête le serveur (bouton ⏻) |

Réglages en haut de `veille.py` : `FEED_TTL`, `MAX_PER_SOURCE`, `MAX_AGE_DAYS`, `SLOW_HOSTS`, et `COINS` (identifiants CoinGecko : ajoute `ethereum` par exemple).

---

## 10. Dépannage

| Symptôme | Solution |
|---|---|
| « Liaison perdue avec le serveur local » | La veille a été arrêtée : reclique sur l'icône **Veille Azoth**. |
| Rien ne se passe au clic sur l'icône | Regarde `data\veille.log`, ou lance `Lancer-Veille.bat` pour voir l'erreur dans la console. |
| « Le port 8765 est déjà utilisé » | La veille tourne déjà et le navigateur s'ouvre dessus. Sinon : `python veille.py --port 9000`. |
| Source en rouge | Survole-la pour lire l'erreur. `429` : le site limite les accès (souvent Reddit), ça repasse tout seul. `403` : le site bloque les robots. |
| Source en orange | Elle fonctionne, mais n'a rien publié depuis 45 jours. Normal pour un projet calme. |
| Cours crypto « indisponible » | L'API gratuite de CoinGecko limite les appels : attends quelques minutes. |
| La page ne change pas après une modification du code | `Ctrl + F5` pour recharger sans cache. |
| Sur le Pi, la page ne répond pas | `systemctl status veille-azoth`, puis `journalctl -u veille-azoth -n 50`. Vérifie le pare-feu (`sudo ufw status`). |
