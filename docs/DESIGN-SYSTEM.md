# Trame graphique MU-TH-UR

## Intention

MU-TH-UR est une interface d'exploitation personnelle inspirée des terminaux
industriels de science-fiction. Elle doit paraître technique, dense et fiable,
sans reprendre les codes brillants d'un tableau de bord SaaS. La veille est la
référence visuelle ; Super IA et Quant Core en reprennent la grammaire sans
masquer leur fonction propre.

Les priorités sont, dans l'ordre : lisibilité, état opérationnel, cohérence,
densité utile et ambiance.

## Palette canonique

| Token | Valeur | Usage |
|---|---:|---|
| `bg` | `#030604` | fond principal |
| `panel` | `#07100a` | panneau et champ sombre |
| `panel_raised` | `#0a1710` | panneau surélevé ou survol |
| `line` | `#143521` | séparation normale |
| `line_strong` | `#1d4a2e` | contrôle et focus secondaire |
| `phosphor` | `#3dff7f` | action, titre et état nominal |
| `phosphor_dim` | `#27c25c` | information secondaire active |
| `text` | `#c9f5d6` | texte principal |
| `muted` | `#5c7d67` | aide, métadonnée et état neutre |
| `amber` | `#ffb53d` | attention, fraîcheur et mesure |
| `danger` | `#ff3b2f` | erreur, réel, arrêt et HAL |
| `personal` | `#b9a8ff` | contexte personnel ou documentaire |

Le rouge n'est jamais décoratif, sauf pour l'œil HAL qui représente la présence
du système. Le violet ne signale ni une erreur ni un état de service.

## Typographie

- titres et grands nombres : `VT323`, puis repli monospace ;
- contenu, contrôles et tableaux : `IBM Plex Mono`, puis `Consolas` ;
- titres en capitales avec espacement léger ;
- métadonnées entre 10 et 12 px ;
- texte courant à 14 px minimum sur ordinateur.

Une interface reste fonctionnelle si les polices web ne sont pas disponibles.

## Formes et profondeur

- rayons de 2 à 4 px ;
- bordure normale de 1 px ;
- ombre verte très faible, réservée au focus et aux éléments actifs ;
- aucun grand arrondi, verre dépoli ou dégradé multicolore ;
- panneaux en dégradé vertical discret de `panel_raised` vers `panel` ;
- scanlines et vignettage légers, inertes et non interactifs.

## Composants

### En-tête

L'en-tête porte l'identité `MU-TH-UR 6000`, le nom du module et les états
critiques. Il possède une seule ligne basse et reste sombre. Les commandes
secondaires sont compactes.

### Panneau

Un panneau contient un seul sujet. Son titre phosphore utilise la police
terminale ; la description ou l'eyebrow reste atténuée. Les panneaux ne doivent
pas devenir des cartes décoratives.

### États

- vert : actif, sain ou confirmé ;
- ambre : attente, simulation, fraîcheur ou attention ;
- rouge : erreur, danger ou mode réel ;
- gris-vert : inactif, inconnu ou indisponible ;
- violet : contenu personnel, Obsidian ou contexte utilisateur.

Un état ne repose jamais uniquement sur la couleur : ajouter un libellé, un
symbole ou une forme.

### Contrôles

Les champs utilisent `panel`, une bordure `line_strong` et un focus phosphore.
Le bouton principal peut être plein phosphore avec texte sombre ; les boutons
secondaires restent sombres et bordés. Une action destructive est rouge et
explicite.

### Données

Les tableaux privilégient l'alignement et les séparateurs fins. Les grands
indicateurs emploient la police terminale. Les journaux utilisent un fond presque
noir et ne colorent que les niveaux utiles.

## Adaptation par module

| Module | Accent fonctionnel | Particularité |
|---|---|---|
| Veille | vert + ambre | rouge pour les alertes, violet pour « Pour toi » |
| Super IA | vert + violet | violet réservé aux sources Obsidian |
| Quant Core | vert + ambre | rouge réservé au risque, aux pertes et au mode réel |

Les trois modules partagent exactement le fond, les panneaux, les lignes, le
texte, le focus et les règles d'état.

## Responsive et accessibilité

- passage en une colonne sous 800–900 px ;
- cible interactive d'au moins 40 px sur mobile ;
- focus clavier toujours visible ;
- aucune information essentielle dans une animation ;
- animations désactivées avec `prefers-reduced-motion` ;
- contraste texte/fond vérifié avant ajout d'une nouvelle couleur ;
- scanlines placées derrière les interactions et limitées en opacité.

## Cartographie dans le code

- Veille : `dist/style.css`, source de référence ;
- Super IA : tokens intégrés dans `src/web/chat-page.ts` ;
- Quant Core : tokens dans `console/styles/globals.css` ;
- captures relues : `docs/captures/`.

Toute nouvelle interface commence par cette palette et ces composants. Une
exception doit être motivée dans la documentation du module, jamais ajoutée
comme couleur ou effet isolé.
