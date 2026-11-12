# Liaison Mistral et Obsidian

Le chat principal et le mini-chat disposent de l'option « Utiliser Obsidian ».
Lorsqu'elle est cochée, le serveur recherche les mots de la dernière question
dans les notes Markdown et transmet jusqu'à six extraits au fournisseur choisi.
Avec Mistral, ces extraits quittent donc la machine. Décocher l'option coupe la
recherche pour les nouveaux messages ; démarrer une nouvelle conversation pour
retirer également les réponses précédentes de l'historique envoyé.

La recherche est lexicale, limitée à 2 000 notes et six extraits de 850 caractères.
Les dossiers cachés et liens pointant hors du coffre sont exclus. Les chemins
sont retournés comme sources et le modèle reçoit la consigne de les citer.
Une absence de résultat signifie qu'aucun extrait n'a été ajouté ; elle ne prouve
pas l'absence d'une note sur le sujet.

La clé reste côté serveur dans le coffre chiffré Super IA. Les réponses peuvent
être enregistrées via « + Obsidian » : une nouvelle note est créée dans Inbox.
Cette liaison documentaire ne donne pas au modèle un outil de modification des
notes existantes. L'utilisateur conserve l'édition normale dans Obsidian.

## État de la case et du backend

Le code d'interface actuellement inspecté initialise cette case comme cochée.
Ce n'est pas conforme à une activation explicite : le réglage doit être décoché
par défaut avant la mise en route stable. Le HEAD du dépôt Super IA transmet le
contexte demandé au fournisseur choisi; le worktree utilisé par l'unité systemd
contient une modification locale qui limite le contexte à Ollama. L'unité lance
le fichier compilé `dist/index.js`, donc vérifier le contenu effectivement
compilé et chargé avant d'affirmer le comportement Mistral.

## Activation

Après compilation de Super IA, redémarrer `superia-web.service` et
`veille-azoth.service`, puis recharger la page. Un coffre monté et une clé Mistral
valide sont nécessaires. Aucune requête facturable n'est exécutée par les tests.
