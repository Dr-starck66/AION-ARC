# ASTRA Ω — NFL Open Data : analyse indépendante (13/11/2026)

**Décision propriétaire** : ne participer à aucun concours NFL/Kaggle, ne pas accepter de règlement de concours ni consommer de quota GPU.

## Travail réellement effectué

- Lecture directe, via connecteur GitHub, du CSV public `array-carpenter/nfl-draft-data/data/combine_official.csv` sur la branche `master`.
- Preuve de source **Git blob SHA-1** `dcc6532ba88038cad3d9f974ea7654b2a6e5988a`. Fichier non recopié dans ASTRA, uniquement des agrégats.
- Deux analyses séparées du contenu CSV (parseur CSV avec guillemets et contrôle des dimensions) : **6 568 lignes / 24 colonnes**, zéro ligne CSV irrégulière, **2006–2026 avec 2021 absent**, zéro doublon `(année,person_id non vide)`, deux lignes sans groupe de poste.
- **5 078** valeurs du sprint de 40 yards valides, **4 992** valeurs de saut vertical valides, **4 699** lignes avec les deux valeurs valides.
- Médianes de 40 yards : WR **4,51 s** (n=784), DB **4,52 s** (n=967), OL **5,24 s** (n=836). Comparaisons purement descriptives, jamais une capacité prédictive.
- Rapport agrégé complet : [RESULTS_20261113.json](RESULTS_20261113.json) (par position, année, sources et limites).

## Contrôles négatifs et limites obligatoires

- Le README du dépôt source annonce **6 883 lignes** tandis que le CSV exactement identifié ci-dessus en contient **6 568**. Discordance non résolue ; ne pas publier de décompte exhaustif indépendant de ce fichier versionné.
- Aucune saison 2021 dans cette source. Deux positions non classées.
- Les métriques sont descriptives et n'établissent **aucun** lien causal ou prédictif entre Combine, recrutement, performances en match, carrière ou résultats sportifs.
- La provenance NFL API est documentée par le dépôt tiers. Les droits précis de redistribution du jeu brut n'ont pas été vérifiés : ne redistribuer aucun enregistrement brut, seulement les agrégats et les liens avec attribution.
- Les études scientifiques indépendantes ont déjà documenté les différences par position et les limites prédictives des tests Combine (p. ex. PMID 37639664 et PMID 42641168). Ne pas revendiquer la nouveauté de ces constats.

## Réexécution reproductible

- `analyze_combine.py` : lit la ressource GitHub publique, impose une taille maximale de **3 Mo** et vérifie son empreinte **Git blob SHA-1** avant toute statistique ; peut aussi travailler sur une copie locale. Aucune dépendance Kaggle, aucun jeton, aucune soumission.
- `test_analyze_combine.py` : **11/11 tests unitaires PASS** sur Python dans un environnement isolé ; tests synthétiques positifs et négatifs (valeurs absentes/invalides, lignes mal formées, doublons, année invalide, fichier source modifié).
- L'analyse du CSV public dans cette conversation a été réalisée avec le **connecteur GitHub et un analyseur JavaScript** ; le script Python n'a **pas** été exécuté sur le véritable CSV dans l'environnement local faute d'accès réseau au fichier brut. Il a été testé seulement sur fixtures, ce qui interdit de revendiquer une seconde réplication Python sur données réelles.

## Périmètre préservé

**Zéro concours, zéro téléchargement Kaggle, zéro GPU, zéro dépense, aucune fusion, aucune modification en production.** BIO-MIMIC X est conservé tel quel.

**Statuts** : analyse descriptive sur CSV récupéré `PASS` ; tests locaux Python `PASS` ; réplication réelle par Python `UNVERIFIED` ; validation scientifique et prédictions `UNVERIFIED`.
