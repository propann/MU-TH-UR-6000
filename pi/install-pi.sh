#!/usr/bin/env bash
# =============================================================
#  Installation de la Veille Azoth sur Raspberry Pi (ou Debian)
#
#  1. Copie le dossier veille-azoth sur le Pi, par exemple :
#       scp -r veille-azoth azoth@IP-DU-PI:~/
#  2. Sur le Pi :
#       cd ~/veille-azoth && bash pi/install-pi.sh
#
#  Le script : verifie Python, demande un mot de passe, installe
#  le service systemd (demarrage automatique) et ouvre le port
#  8765 dans le pare-feu ufw s'il est actif.
#  Il peut etre relance sans risque (mise a jour du service).
# =============================================================
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"   # dossier veille-azoth
USER_NAME="$(id -un)"
SERVICE=/etc/systemd/system/veille-azoth.service
ENVFILE=/etc/veille-azoth.env

echo "== Veille Azoth : installation dans $DIR (utilisateur $USER_NAME)"

# 1) Python 3.9+ (present par defaut sur Raspberry Pi OS)
if ! command -v python3 >/dev/null; then
  echo "Installation de Python 3..."
  sudo apt-get update && sudo apt-get install -y python3
fi
python3 -c 'import sys; assert sys.version_info >= (3, 9), "Python 3.9+ requis"'

# 2) Mot de passe (stocke dans /etc/veille-azoth.env, lisible par root seulement)
if [ ! -f "$ENVFILE" ]; then
  read -rsp "Choisis un mot de passe pour la veille (vide = aucun) : " PW; echo
  printf 'VEILLE_PASSWORD=%s\n' "$PW" | sudo tee "$ENVFILE" >/dev/null
  sudo chmod 600 "$ENVFILE"
else
  echo "Mot de passe deja configure ($ENVFILE). Pour le changer : sudo nano $ENVFILE"
fi

# 3) Service systemd
sed -e "s|__USER__|$USER_NAME|g" -e "s|__DIR__|$DIR|g" "$DIR/pi/veille-azoth.service" | sudo tee "$SERVICE" >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now veille-azoth
sudo systemctl restart veille-azoth

# 4) Pare-feu (seulement si ufw est installe et actif) : reseau local uniquement
if command -v ufw >/dev/null && sudo ufw status | grep -q "Status: active"; then
  sudo ufw allow from 192.168.0.0/16 to any port 8765 proto tcp comment "Veille Azoth"
fi

IP="$(hostname -I | awk '{print $1}')"
echo
echo "== Termine. Ouvre http://$IP:8765 depuis ton PC ou ton telephone (meme Wi-Fi)."
echo "   Etat    : systemctl status veille-azoth"
echo "   Journal : journalctl -u veille-azoth -f"
