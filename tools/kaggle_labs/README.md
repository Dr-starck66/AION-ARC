# ASTRA Ω — Exécutions Kaggle sur données réelles (13 novembre 2026)

## Ce qui est prouvé
- Le titulaire a confirmé depuis PowerShell `You are now logged in as [drstarck]`.
- Le lanceur antérieur a téléchargé un reçu `ASTRA_KAGGLE_GPU_VERIFIED_PASS` : 2 Tesla T4 ; il s'agit d'un ancien test GPU, pas d'un résultat scientifique.
- Le nouveau lanceur ne transfère aucune clé. Il invoque uniquement l'outil Kaggle installé localement et son OAuth existant.

## Exécution en un bloc PowerShell
Télécharger le lanceur `tools/astra_kaggle_research.py` depuis une révision GitHub **épinglée**, puis exécuter avec `%LOCALAPPDATA%\ASTRA-Kaggle\.venv\Scripts\python.exe`.

## Deux vraies analyses d'abord
1. **NFL Big Data Bowl 2027** : attache `competition_sources=["nfl-big-data-bowl-2027"]` pour explorer les fichiers officiels, les colonnes et un échantillon borné de vitesses. Le signal football pertinent, les appariements Combine–match et les performances prédictives restent **UNVERIFIED**. L'adhésion au règlement Kaggle n'est **jamais acceptée à la place de l'utilisateur** : en cas de refus API, statut `PARTIAL` avec blocage explicite.
2. **BIO-MIMIC X** : attache `lachmann12/human-liver-rnaseq-gene-expression-903-samples` (ARCHS4, CC0 déclaré, 903 colonnes, 35 238 gènes attendus). Lecture du TSV réel, vérification des valeurs, identifiants et empreinte SHA-256, comptages de détection. Aucun résultat de rajeunissement ou clinique n'est déduit de ce contrôle qualité.

La procédure est **séquentielle**, préserve le quota GPU (`enable_gpu=false`), conserve tous les notebooks en **privé**, désactive Internet dans Kaggle et ne publie aucune donnée. Un reçu Kaggle est conservé dans `%LOCALAPPDATA%\ASTRA-Kaggle\research\<project>\output\`. Synthèse locale : `astra_kaggle_research_summary.json`.

## Avant chaque soumission distante
- Téléchargement de deux scripts Python épinglés à un SHA GitHub.
- Compilation Python locale et **deux tests sur fixtures synthétiques** : un jeu valide doit produire `PARTIAL` avec les bons identifiants/empreinte ; un répertoire vide doit être refusé par `FAIL`. Les tests locaux ne prouvent pas l'accès aux données réelles.
- Réutilisation d'un reçu Kaggle existant **seulement si son projet, sa source et le SHA-256 du script concordent**.
- Si la session est déjà en cours, ne pas pousser de doublon.

## Périmètre préservé
- **AION-ARC** : anciens notebooks maintenus, compétition 2026 close ; score caché non revendiqué.
- **SplatForge** : GPU T4 confirmé, pas de jeu d'images/COLMAP vérifié ; entraînement 3D `UNVERIFIED`.
- **ASTRA DC ENERGY** : traces d'énergie/latence réelles non appariées ; pas de gain énergétique revendiqué.
- **ASTRA Quantum Gate** : validateur structurel existant, physique et score officiel `UNVERIFIED`.
- **NEXUS** : corpus de sécurité sous licence autorisée non branché.
- **QuantFlow** : historique de marché et validation temporelle hors fuite non branchés.
- **BetGPT, SEO, production Web, Wine Else** : Kaggle n'est pas un hébergement de production ou un moteur de publication.

## Statuts stricts
- `ASTRA_KAGGLE_AUTH_PASS` : authentification Windows à Kaggle.
- `ASTRA_LOCAL_SELFTEST_PASS` : tests locaux de fixture, PAS expérience Kaggle.
- `ASTRA_KAGGLE_NFL_DATA_PARTIAL` et `ASTRA_KAGGLE_BIO_DATA_PARTIAL` : un reçu sur de vraies données a été téléchargé et contrôlé ; pas de conclusion scientifique.
- `FAIL` / `UNVERIFIED` : échec ou absence de preuve. Ne pas confondre un notebook marqué COMPLETE et une validation scientifique.

Statut **actuel avant exécution du nouveau lanceur** : code ajouté à une PR brouillon ; **aucun nouveau résultat Kaggle scientifique encore observé**.

## Incident Kaggle observé et reprise v2 (13/11/2026)

**PASS** : compte `drstarck`, preuve GPU historique 2 × T4 et tests locaux synthétiques NFL/BIO.

**FAIL sur les données réelles** :
- NFL : `kernels.get denied` pour le slug attendu. Il faut retrouver le slug réel dans la liste des notebooks du compte.
- BIO : reçu `PUBLIC_ARCHS4_EXPRESSION_QC_FAILED` : `Kaggle public expression dataset is not mounted`.

**Remédiation versionnée** :
- BIO recherche uniquement `human_liver.tsv` dans les sous-répertoires montés de `/kaggle/input`, sans supposer un nom de répertoire.
- NFL découvre le montage officiel du concours et refuse les montages absents ou ambigus.
- Le lanceur lit `kernels list --mine -v`, choisit une seule correspondance et refuse les doublons ou une permission refusée.
- En cas de `KernelWorkerStatus.ERROR`, le lanceur récupère les journaux Kaggle et le reçu d'échec dans la même exécution.
- Les scripts scientifiques sont figés au commit `3bedfdb957e225684f13eadeb41e9547f250ccac` et les reçus sont validés par leur SHA-256.

Audit local ciblé du 13/11 : sept contrôles reproduits sur l'algorithme de résolution des slugs et de découverte des montages : `7/7 PASS`. Ce n'est pas une validation intégrale du nouveau lanceur ou une exécution scientifique sur Kaggle. Ces exécutions distantes restent `UNVERIFIED`.

Sources : [NFL Big Data Bowl 2027](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027) ; [ARCHS4 human liver samples](https://www.kaggle.com/datasets/lachmann12/human-liver-rnaseq-gene-expression-903-samples).
