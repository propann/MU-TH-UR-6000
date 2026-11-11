# Sécurité et données privées

## Ce qui reste sur la machine

- `.env` : mot de passe du cockpit et identifiants internes générés au premier déploiement, permissions `0600` ;
- volumes Docker : état du cockpit, coffre de clés Super IA et données Quant/Freqtrade ;
- clé Mistral : saisie dans l’interface et conservée chiffrée par Super IA ;
- clés exchange et Telegram : coffre privé de Quant Core ;
- modèles : stockage Ollama existant ;
- notes : coffre monté depuis l’hôte en lecture seule et Inbox dédiée en écriture ;
- journaux, caches, bases, secrets, sauvegardes et préférences : hors de Git.

Le mot de passe du portail n’est jamais écrit dans les images. Sur une migration, le script reprend le mot de passe déjà configuré quand il trouve l’ancien fichier d’environnement local ; sinon il génère un nouveau secret et le conserve dans un fichier `0600` ignoré par Git.

## Réseau

Le serveur Super IA est lié à la boucle locale et n’a pas d’authentification interne car son seul chemin réseau passe par le portail MU-TH-UR. Quant UI écoute sur la boucle locale. Freqtrade et Rack Agent restent sur le réseau privé Docker. Le moteur ne publie aucun port hôte.

Le cockpit écoute sur le réseau local avec une authentification HTTP. Le pare-feu doit limiter son port au sous-réseau privé utilisé. Ne pas rediriger ce port depuis Internet.

## Trading

Le profil Compose standard démarre la console, pas le moteur. Les clés exchange restent vides tant qu’elles ne sont pas configurées. Freqtrade garde `dry_run` actif dans sa configuration de départ. Aucun ordre réel n’est envoyé par le déploiement.

Le moteur se démarre explicitement avec le profil `trading-engine` après revue de la configuration et des protections. Le choix de l’exchange appartient à l’opérateur ; aucun compte ni identifiant Binance n’est requis par le cockpit.

## Contrôle avant publication

Avant toute branche publique : vérifier l’arborescence exacte, ignorer les fichiers locaux, lancer Gitleaks, puis relire deux fois les changements et le contenu du commit. Toute détection de secret bloque la publication jusqu’à correction et rotation du secret concerné.
