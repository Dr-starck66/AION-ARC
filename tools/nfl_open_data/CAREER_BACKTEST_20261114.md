# ASTRA NFL CAREER Ω — v0.1 (14 novembre 2026)

**Objectif :** tester si les résultats physiques du NFL Combine ajoutent une information prédictive sur une carrière réelle, au-delà du poste et du rang de draft. **Aucun concours Kaggle, aucun GPU, aucune soumission.**

## Sources et provenance

Le moteur lit exclusivement les deux CSV publics publiés par [nflverse/nflverse-data](https://github.com/nflverse/nflverse-data/releases), via les URL officielles documentées dans `nflreadr` :
- [combine.csv](https://github.com/nflverse/nflverse-data/releases/download/combine/combine.csv) ; [chargeur officiel](https://github.com/nflverse/nflreadr/blob/main/R/load_combine.R).
- [draft_picks.csv](https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv) ; [chargeur officiel](https://github.com/nflverse/nflreadr/blob/main/R/load_draft_picks.R).

L'accès en lecture de ces deux archives **n'a pas réussi depuis la session ChatGPT** : Internet est désactivé dans le conteneur ; le navigateur cloud Firecrawl a refusé la requête faute de crédits et Hugging Face Jobs est facturé. **Aucun fichier de carrière réel n'a donc été téléchargé ni apparié dans cette exécution.** Aucun AUC réel n'est déclaré.

La version connue de `array-carpenter/nfl-draft-data` avec 6 568 lignes est un jeu physique indépendant, mais elle ne fournit pas l'identifiant PFR commun indispensable à cette jointure stricte. Nous ne l'avons pas rapprochée par simple nom (fort risque de faux appariements).

## Garde-fous

1. Correspondances de joueurs uniquement par clé exacte `(season, player_pfr_id)`, jamais par similarité de noms. Les clés dupliquées rendent l'analyse **FAIL**.
2. Un joueur du Combine absent du tableau de draft n'est **pas** étiqueté comme un échec de carrière. La population est restreinte aux **joueurs draftés**, appariés, avec nombre de matchs PFR connu, non négatif, et choix de draft numérique 1–400.
3. Variables initiales exclusivement disponibles au recrutement : poste, rang de draft, 40-yard dash, saut vertical, bench, broad jump, 3-cone, shuttle. **Aucune variable de résultats NFL** en entrée du modèle.
4. Cible binaire exploratoire : au moins **50 matchs NFL de carrière**. Cette mesure n'a pas un horizon fixe ; les promotions plus anciennes disposent d'une fenêtre d'exposition plus longue. On ne conclut ni à une causalité ni à une capacité opérationnelle.
5. Séparation temporelle stricte : entraînement 2006–2013 ; sélection de `C` sur validation 2014–2015 ; réentraînement train+validation ; test final sur 2016–2018 **une seule fois**.
6. Comparaison au témoin **poste + rang de draft** ; version enrichie ajoutant six mesures physiques. Comparer ROC AUC, score de Brier et log-loss. Les gains négatifs sont conservés.
7. Imputation et normalisation incluses dans les pipelines ajustés uniquement sur les données autorisées par chaque étape ; les données de test ne servent jamais à choisir `C`.
8. Rapport uniquement **agrégé**, incluant couvertures de jointure, exclusions, années, proportions positives, empreintes SHA-256 des deux sources, métriques et différences. Aucun export de joueur individuel.

## Exécution locale déjà réalisée

- `career_backtest.py` : compilation **PASS**.
- `test_career_backtest.py` : **14/14 tests PASS**, Python 3.13, numpy / pandas / scikit-learn installés.
- Les tests comprennent : CSV cassé, clés ambiguës, joueur non retrouvé, carrière manquante, choix de draft invalide, jeux de données futurs, données aberrantes, absence de classe positive en test, fuite d'identifiants vers le rapport, fichier symlink et évaluation chronologique complète sur jeux synthétiques.
- Le moteur et les 14 tests sont enregistrés **octet pour octet** comme exécutés sur cette branche. Hash Git blob moteur `cf9b046cc14a134175f1323b3d2108e41b74af19`, tests `5fe2b934222ad646021fc1a31f7ae2f4a928e0f3`.

L'essai synthétique du modèle enrichi produit des scores fictifs cohérents avec le générateur, **mais ces scores ne constituent pas des résultats NFL**. Aucun de ces nombres n'est repris comme preuve de performance prédictive réelle.

## Statut

| Gate | Statut |
| --- | --- |
| Code et tests reproductibles | **PASS** |
| Schémas et URL publiques documentés | **PASS** |
| Téléchargement effectif des deux archives dans une session autorisée et gratuite | **UNVERIFIED** |
| Jointure de joueurs réels, taux de couverture, identifiants ambigus | **UNVERIFIED** |
| Test final sur carrières NFL 2016–2018 | **UNVERIFIED** |
| Résultat scientifique indépendant validé | **UNVERIFIED** |

**Prochaine action unique** : exécuter le code sur une source réseau autorisée **sans facturation** et conserver les deux SHA-256 ainsi que toutes les métriques de couverture et de test. Ne pas créer de nouveau workflow ou abonnement.

La source nflverse est fournie sous les droits et conditions de ses fournisseurs ; pas de republication de lignes brutes dans ce dépôt.
