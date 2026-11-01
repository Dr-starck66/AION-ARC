# ASTRA AION-ARC Ω — preuves du 1 novembre 2026

**Statut global : PARTIAL. Aucun notebook du challenger n'a été exécuté sur Kaggle pendant cette intervention. Aucun nouveau score n'est revendiqué.**

## État Kaggle observé dans le navigateur

- Classement public : **Dr starck, 4514e sur 5028 équipes, 0,07, 1 entrée**.
- Lien observé : https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard?search=Dr+starck
- Leaders observés : Fields Model 75,56 ; Tufa Labs 70,02 ; faster machine is all you need 58,59.
- Le tableau indique que le score public utilise environ 50 % des données de test.
- La soumission historique #57848621 / version 6 / scriptVersionId 364319161 est préservée. Son identifiant et son ancien statut proviennent de la mission et du registre antérieur ; ses détails privés n'ont pas pu être revérifiés aujourd'hui.
- La connexion Google accessible ouvre le compte **ced669**, distinct de **drstarck**, avec « Join Competition ». Aucun calcul ni inscription n'y a été lancé.
- La dernière tentative via Email a été rejetée par Kaggle : « The username or password provided is incorrect. » Les nouvelles demandes de connexion sont arrêtées conformément à la demande de l'utilisateur.
- L'ouverture de la gestion du compte Google a été rejetée par le contrôle automatique d'autorisation, car elle dépassait le flux de connexion Kaggle. Aucun contournement n'a été tenté.
- Aucun jeton Kaggle n'est configuré dans cet environnement d'exécution. Aucun secret n'est inclus dans les fichiers.

## Défauts reproduits et correctifs

| Point | Preuve négative | Modification v2.8 | Statut du correctif |
|---|---|---|---|
| v2.7 saute l'agent hors rerun | Toutes les cellules réelles sont conditionnées à TRUE_RERUN | Exécution normale sur deux vrais jeux publics, filtre absent en rerun caché | PASS code/test ; exécution Kaggle UNVERIFIED |
| Syntaxe du bac à sable | Application réelle des surcouches v2.5 au code Duck : SyntaxError ligne 22 | Séparation des délimiteurs des docstrings imbriquées ; compilation du programme interne | PASS intégration source et processus enfant |
| Déplacements visuels confondus | Objets de même forme à deux positions : signatures identiques | Ajout de la position (bbox) dans la signature | PASS contrôle négatif/positif |
| Mauvaise prédiction traitée comme action fatale | Politique v2.5 blacklistant host_mismatches | Réutilisation de la politique de reprise v2.6 existante | PASS tests de politique |
| Clics à deux coordonnées confondus | Clé historique limitée au nom de l'action | Clé comprenant row/col ; MOUSE n'est plus bloqué par la seule répétition du nom | PASS transport contrôlé |
| Cellules de bord perdues | Signature hôte rognant trois cellules de chaque bord | Conservation du plateau entier pour la mémoire d'échec | PASS fonction extraite du code généré |
| Faux succès d'exécution | Parquet seul, réponses de modèle absentes ou crash avalé par Benchmark | Journal des réponses du modèle local et retours d'environnement ; validation après bm.run | PASS tests de refus ; preuve en jeu UNVERIFIED |

Le test du processus enfant utilise le véritable bac à sable Duck, avec un hôte contrôlé et deux clics synthétiques. **Ce n'est ni un jeu ARC résolu ni une inférence du modèle.** Le code Duck public testé est figé au commit `7652836056c59e044f093e3c13ed7438c814169e`. L'identité de ce code avec le contenu effectivement monté du dataset Kaggle reste UNVERIFIED.

## Livrables et vérifications exécutées

- `scripts/build_arc3_verified_challenger.py` : générateur v2.8 séparé ; réutilise v2.5/v2.6.
- `scripts/verify_arc3_upstream_patch.py` : intégration des surcouches sur le vrai code Duck, compilation imbriquée, contrôle négatif conservé et test de processus enfant.
- `tests/test_arc3_v28_builder.py` : tests de régression et refus des fausses preuves.
- `kaggle/v28-recovery/submission.ipynb` et `kernel-metadata.json` : challenger complet.
- `kaggle/v28-upstream/submission.ipynb` et `kernel-metadata.json` : témoin Duck sans surcouches ASTRA.
- `reports/arc3-v28-20261101/` : logs, intégration JSON et registre d'état.

Commandes réellement exécutées :

```bash
python -m pytest -q tests kaggle/test_aion_guard.py kaggle/test_aion_v26_recovery.py
python scripts/verify_arc3_upstream_patch.py ../duck-harness
python scripts/build_arc3_verified_challenger.py --out kaggle/v28-recovery/submission.ipynb
python scripts/build_arc3_verified_challenger.py --profile upstream --out kaggle/v28-upstream/submission.ipynb
git diff --check
```

Résultats : **103 tests réussis, 7 sous-tests réussis ; 26 fichiers Python générés compilés ; deux actions contrôlées transmises dans le vrai processus enfant**. Les empreintes exactes sont enregistrées dans le registre JSON.

## Configuration prévue et limites

Les deux packages déclarent les trois datasets demandés :

1. `jeroencottaar/taaf-kaggle-source-share`
2. `driessmit1/arc3-vllm-h100-wheelhouse-v3`
3. `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot`

Internet désactivé, notebooks privés, accélérateur notebook `nvidiaRtx6000` selon le starter officiel. Le contrôle d'exécution exige un RTX PRO 6000 ou H100 et adapte KAGGLE_GPU_TYPE au matériel constaté. **Allocation GPU, quota disponible, montage effectif des datasets et compatibilité des roues : UNVERIFIED sur Kaggle.** Aucun GPU payant n'est réservé.

Une exécution normale doit jouer `ls20` et `vc33` avec le modèle local durant au plus 30 minutes après installation. Le rerun officiel doit utiliser tous les jeux exposés par la passerelle et ne reçoit aucun filtre public. Le fichier de démonstration nécessaire à la validation de commit n'est créé qu'après validation des journaux de jeu. Un crash du benchmark ou l'absence d'inférence/actions fait échouer ce contrôle.

Les deux jeux constituent un test de fonctionnement, pas une évaluation scientifique complète. Les graines et le déterminisme du serveur d'inférence restent à vérifier. Le comparateur existant exige 25 jeux et au moins deux graines pour qualifier une amélioration publique ; même cette comparaison ne démontre pas le score caché.

## Recherche sur les meilleurs agents

**Fields Model** : score 75,56 vérifié directement sur Kaggle. Aucune méthode technique primaire suffisamment documentée n'a été trouvée pendant cette recherche ; méthode UNVERIFIED. Aucune architecture ne lui est attribuée par supposition.

**Tufa Labs** : l'article de l'équipe décrit un petit modèle local Qwen 3.6 27B FP8, un interpréteur Python, une observation combinant image et texte, et l'éviction des vieux messages. Le challenger conserve ce socle déjà présent dans AION. Le 70,02 actuel du classement ne prouve pas que la version publique de juin reproduit ce score.

Source primaire : https://tufalabs.ai/research/duck-harness/

Code primaire consulté : https://github.com/Tufalabs/duck-harness

**NVIDIA AVO** : l'équipe rapporte 100,00 RHAE sur 25 jeux publics et 183 niveaux avec Claude Opus 5, mémoire persistante et supervision. Elle distingue explicitement ces résultats des jeux semi-privés/privés et précise que la comparaison avec VISTA n'est pas une ablation contrôlée. Ce résultat ne démontre pas une recette gagnante sous les contraintes gratuites hors ligne de Kaggle.

Source primaire : https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/

Starter matériel/flux officiel : https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter/blob/main/scripts/build_notebook.py

Le bonus conditionnel de 700 000 USD exige 100 % et suit les règles de répartition Kaggle ; ce n'est pas une récompense individuelle garantie. Échéance des soumissions : 2 novembre 2026 à 23 h 59 UTC, soit le 3 novembre à 00 h 59 à Paris.

Source : https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview/prizes

## État final et prochaine priorité

| Élément | Statut |
|---|---|
| Score et rang publics observés | PASS |
| Correction, reconstruction et contrôles CPU | PASS |
| Compatibilité des patches avec le code Duck public testé | PASS |
| Moteur avancé réellement exécuté sur Kaggle | UNVERIFIED |
| Dernière authentification au compte drstarck | FAIL |
| Datasets réellement attachés, GPU et quotas vérifiés | UNVERIFIED |
| Nouvelle soumission officielle et nouveau score | UNVERIFIED — aucune tentative engagée |
| Gain contre 0,07 | UNVERIFIED — aucun nouveau score |
| Mission complète | PARTIAL |

Priorité unique : obtenir l'exécution Kaggle du témoin Duck puis du challenger corrigé sur les mêmes jeux, avec journaux d'inférence et d'actions, avant d'engager une nouvelle soumission. La session correcte est le blocage actuel ; aucune nouvelle demande de connexion ni tâche de fond n'est lancée.
