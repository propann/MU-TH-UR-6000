# Réseau local Azoth

## État actuel

Le serveur utilise uniquement le Wi-Fi à l'adresse observée `192.168.2.132`. Le
switch n'est pas encore raccordé et l'interface Ethernet `enp6s0` reste
débranchée. Aucune configuration réseau active ne doit être modifiée avant le
branchement physique.

## Cible

Le switch Ethernet deviendra le réseau principal entre le serveur Pop!_OS, le
poste Windows 11 et les autres machines. Le dossier Drive `SuperIA-Vault` reste
la source documentaire officielle et est rendu disponible hors connexion sur
chaque machine autorisée.

Le serveur possède un contrôleur Realtek RTL8111/8168 piloté par `r8169`, donc
un lien Ethernet Gigabit. Le Wi-Fi Intel AX210 sera conservé pendant les essais.

## Branchement futur

1. Relier la box ou le routeur au switch.
2. Relier le serveur et Windows 11 au switch en Cat 5e ou mieux.
3. Garder le Wi-Fi actif et laisser DHCP attribuer l'adresse Ethernet.
4. Relever cette adresse puis créer une réservation DHCP dans le routeur.
5. Tester depuis Windows avec `ping ADRESSE_DU_SERVEUR` et ouvrir le cockpit.
6. Ne désactiver le Wi-Fi qu'après validation complète, si cela reste souhaité.

Un switch seul relie les machines, mais ne distribue généralement pas les
adresses IP. Il faut donc aussi le relier au routeur, sauf réseau isolé configuré
manuellement.

Seul le reverse proxy du cockpit sera exposé sur le LAN. Ollama, Freqtrade, les
bases et MQTT resteront sur localhost ou le réseau Docker interne.

## Obsidian

- source officielle : dossier Google Drive `SuperIA-Vault` ;
- copie Linux : miroir synchronisé hors ligne et index de recherche local ;
- accès Windows : cockpit web et copie Drive hors ligne ;
- conflits : conserver les deux versions et demander une validation ;
- Git : code et configuration seulement, jamais les secrets ni le vault privé.
