# Audit de la Veille et étude Mistral

## Objet et décision

Cette étude décrit l'état de la Veille MU-TH-UR et une intégration possible de
Mistral pour traduire, résumer, qualifier et regrouper les articles. Aucun appel
Mistral ni aucune dépense n'ont été déclenchés pendant l'audit.

La collecte et les alertes critiques restent locales. L'IA enrichit une
sélection ; elle ne masque jamais une alerte de sécurité et ne modifie pas les
sources sans validation humaine.

## État constaté

| Domaine | Existant | Écart à traiter |
|---|---|---|
| Collecte | RSS, Atom et RSS 1.0, 101 sources, 16 catégories | pas de contenu intégral ni de PDF |
| Performance | téléchargements parallèles, TTL et cache local | pas de file de travaux IA |
| Lecture | recherche, catégories, favoris, lus et sujets suivis | pas de langue ni de traduction |
| Sécurité | écoute locale, POST same-origin, HTML nettoyé | authentification à renforcer avant exposition LAN |
| Données | titre, lien, date et résumé RSS | pas de provenance d'enrichissement |
| Qualité | fonctionnement opérateur vérifiable | pas de tests automatisés du parseur et des API |

Le serveur repose uniquement sur la bibliothèque standard Python et écrit son
cache runtime hors Git. C'est une base compacte. Un résumé RSS étant souvent
tronqué, l'interface ne doit jamais annoncer une traduction de l'article lorsque
seuls son titre et son extrait ont été traités.

## Capacités Mistral utiles

Mistral prend en charge plusieurs langues, dont le français et l'anglais. Les
sorties structurées peuvent être contraintes par un schéma JSON, ce qui convient
mieux qu'un texte libre à un tri automatisé. L'API d'embeddings couvre notamment
le regroupement, la classification et la détection de doublons. L'OCR peut
traiter ultérieurement un PDF ou une image sélectionnés par l'opérateur.

Références officielles :

- [langues prises en charge](https://docs.mistral.ai/resources/languages) ;
- [sorties structurées](https://docs.mistral.ai/inference/conversations/structured-output) ;
- [embeddings](https://docs.mistral.ai/inference/embeddings) ;
- [OCR et annotations](https://docs.mistral.ai/studio/document-processing/overview) ;
- [limites connues](https://docs.mistral.ai/resources/known-limitations).

Les alias de modèles et leurs tarifs peuvent évoluer. Le modèle est donc une
configuration serveur, jamais une valeur structurante du format stocké.

## Cas d'usage évalués

| Fonction | Valeur | Risque ou coût | Décision |
|---|---|---|---|
| Traduire titre et extrait à la demande | forte | faible et bornable | phase 1 |
| Résumer une sélection | forte | extrait parfois incomplet | phase 1, libellé clair |
| Classer par thème et priorité | forte | faux positifs et biais | phase 1, consultatif |
| Bulletin de favoris ou non lus | forte | volume et coût | phase 2, sélection plafonnée |
| Regrouper les doublons sémantiques | moyenne | stockage de vecteurs | phase 2 |
| Télécharger le texte intégral | variable | SSRF, paywall, droits, injection | après durcissement |
| OCR automatique de tous les PDF | faible | coût et fuite documentaire | exclu |
| Laisser l'IA supprimer une alerte | dangereuse | faux négatif critique | interdit |

## Architecture recommandée

```text
Navigateur
    │ sélectionne une action et des articles connus
    ▼
Veille /api/ai/*
    ├── valide identifiants, taille et budget
    ├── file bornée et cache par empreinte
    ├── Ollama local (premier choix privé)
    └── courtier Super IA → Mistral (opt-in explicite)
                               │
                               ▼
                    résultat JSON validé
```

Le navigateur ne reçoit jamais la clé Mistral. La Veille ne lit pas directement
le coffre chiffré de Super IA : Super IA expose un courtier local minimal, ou la
Veille reçoit son propre secret au runtime. Aucun secret, prompt personnel ou
résultat runtime ne va dans Git.

Ollama est recommandé pour un premier tri privé et sans coût à l'appel. Mistral
reste un choix explicite pour comparer la qualité, traduire un contenu difficile
ou servir de solution de repli.

## Contrat de données proposé

```json
{
  "article_id": "identifiant-existant",
  "status": "done",
  "ai": {
    "provider": "mistral",
    "model": "alias-configure-cote-serveur",
    "prompt_version": "veille-enrichment-v1",
    "source_hash": "sha256:…",
    "generated_at": "ISO-8601",
    "source_language": "en",
    "translation_fr": {"title": "…", "summary": "…"},
    "summary_fr": "…",
    "categories": ["securite"],
    "priority": "haute",
    "reason": "…",
    "confidence": "moyenne"
  }
}
```

L'original, le lien, la source et la date restent visibles. Le cache est indexé
par article, empreinte du contenu, fournisseur, modèle et version de prompt.

## API locale envisagée

- `POST /api/ai/enrich` : article(s) et action `translate`, `summarize` ou
  `classify` ;
- `GET /api/ai/result?id=…` : état et résultat validé ;
- `POST /api/ai/digest` : bulletin d'une sélection plafonnée ;
- `GET /api/ai/status` : fournisseur disponible, file et budget restant.

L'API accepte uniquement des identifiants présents dans le cache et jamais une
URL arbitraire fournie par le navigateur.

## Garde-fous obligatoires

- Mistral désactivé par défaut et confirmation avant le premier envoi externe ;
- affichage exact du contenu sortant : titre, extrait ou texte ;
- limites de caractères, travaux simultanés et consommation quotidienne ;
- délais courts, reprises limitées et aucun appel payant en boucle ;
- sortie JSON Schema validée côté serveur et rejetée en cas d'écart ;
- texte d'article traité comme donnée non fiable, jamais comme instruction ;
- conservation locale minimale, purge et invalidation ;
- journal technique sans texte sensible ni clé ;
- règles CVE et mots surveillés toujours autoritaires.

Le futur téléchargement d'un article complet exige une liste d'hôtes issue des
flux, le blocage des IP privées et redirections dangereuses, une limite de taille
et de type MIME, et le respect des paywalls et conditions du site.

## Plan de réalisation

### Phase 0 — fiabiliser

1. Ajouter des fixtures RSS/Atom et des tests de parseur.
2. Tester authentification, POST same-origin et écritures atomiques.
3. Attribuer un identifiant stable aux articles et documenter la rétention.

### Phase 1 — enrichissement contrôlé

1. Créer l'interface fournisseur et un faux fournisseur pour les tests.
2. Ajouter file bornée, cache, budget et schéma de résultat.
3. Livrer la traduction d'extrait, puis résumé et classement sur sélection.
4. Comparer Ollama et Mistral sur un corpus relu manuellement.

### Phase 2 — synthèse et regroupement

1. Produire un bulletin sur un nombre limité de favoris ou non lus.
2. Évaluer les embeddings pour dédupliquer et grouper par thème.
3. Ajouter texte intégral ou OCR seulement après revue sécurité.

## Critères d'acceptation

- zéro secret dans le navigateur, les journaux et Git ;
- aucun appel externe sans choix visible de l'opérateur ;
- original et provenance toujours accessibles ;
- résultat invalide jamais utilisé pour trier silencieusement ;
- même entrée et même version servis depuis le cache ;
- plafond de consommation testé ;
- alertes inchangées lorsque l'IA est coupée ou en erreur ;
- tests contre injection de prompt, SSRF, taille excessive et JSON invalide.

## Conclusion

La meilleure première livraison n'est pas un agent autonome. C'est un bouton de
traduction d'extrait, puis un enrichissement structuré sur une sélection courte,
avec Ollama local par défaut et Mistral explicitement choisi. Cette trajectoire
apporte immédiatement de la valeur tout en gardant la Veille rapide, explicable
et souveraine.
