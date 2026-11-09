@echo off
rem ============================================================
rem  Veille Azoth : demarre le serveur local et ouvre le
rem  navigateur sur http://127.0.0.1:8765
rem  Fermer cette fenetre arrete le serveur.
rem  Acces depuis le telephone (meme Wi-Fi) : lancer plutot
rem    py -3 veille.py --host 0.0.0.0 --password TonMotDePasse
rem ============================================================
title MU-TH-UR // Veille Azoth
cd /d "%~dp0"
where py >nul 2>nul && (py -3 veille.py %* & goto :fin)
where python >nul 2>nul && (python veille.py %* & goto :fin)
echo Python est introuvable. Installe-le depuis https://www.python.org/downloads/
echo (coche "Add python.exe to PATH" pendant l'installation).
pause
:fin
