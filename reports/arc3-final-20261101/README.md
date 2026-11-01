# ASTRA AION-ARC — exécution Kaggle finale

État intermédiaire : **PARTIAL**. Aucun nouveau score officiel n'est affirmé.

## Travail repris

- Branche : `astra/arc3-emergency-20261031`.
- Candidat : `kaggle/v29-milestone2/submission.ipynb`.
- Programme CLI existant conservé : `scripts/arc3_kaggle_final_run.py`.
- Accès réel : session navigateur préexistante du compte `drstarck`, avec lecture des notebooks privés. Aucun nouveau secret créé ou publié.
- Référence officielle confirmée : soumission `57848621`, notebook `notebook2700e63354`, version 6, score public **0,07/100**. Rang observé avant la nouvelle soumission : **4523/5036**, susceptible de changer.

## Incidents conservés

| Exécution | Résultat observé | Limite |
|---|---|---|
| v2.8, `364607203` | FAIL après 2567,8 s ; expirations de requêtes locales, puis échec du contrôle de preuves ; moyenne publique 0,01 | Deux jeux publics, aucun score officiel |
| v2.9 version 1, `364609200` | FAIL après 2388,5 s ; wrapper rejetant une réponse sans contenu final ni appel d'outil ; moyenne publique 33,52 ; quatre niveaux sur sept dans chaque jeu | La présence de raisonnement dans la réponse rejetée n'a pas été conservée par l'ancien wrapper ; cause précise de son contenu UNVERIFIED |
| v2.9 version 2 | FAIL en 16 s : import UI ayant retiré les sources et sélectionné T4 x2 ; contrôle matériel bloquant | Aucune soumission officielle |
| v2.9 version 3, `364686331` | FAIL après 1050,7 s ; 48 réponses du modèle, 99 actions, quatre niveaux terminés ; aucun jeu en panne ; deux ReadTimeout à la limite programmée du test mal classés comme erreurs fatales | Moyenne de 12,10 sur deux jeux pendant cinq minutes ; non comparable au test de trente minutes |

## Correction et tests

Commit : `cd7dffa76087da1a497aab0aae0478b8da1ff374`.

Le contrôle transmet désormais les réponses contenant seulement `reasoning` ou `reasoning_content` au mécanisme de continuation du moteur Duck. Une réponse entièrement vide reste une erreur enregistrée. La validation des actions réellement exécutées et des parties en panne reste active.

Le navigateur visuel par graphe, déjà présent dans le dépôt, est intégré avant l'import du solveur. Aucun itinéraire mémorisé par identifiant de jeu n'est ajouté.

- **PASS** : 110 tests et 12 sous-tests.
- **PASS** : 34 fichiers Python du moteur après application du patch, et programme de sandbox embarqué, compilés.
- **PASS** : contrôle négatif du patch tronqué ; réponses vides et parties en panne toujours rejetées.
- **PASS** : application du véritable hook de navigation au code amont corrigé.
- **PASS** : génération reproductible du notebook, SHA-256 `902940f130b8ce0e4124bac632a767d855d9b7ab6951d503604682c5b9dccded`.

## Nouvelle exécution

Version Kaggle 3 : [`364686331`](https://www.kaggle.com/code/drstarck/astra-aion-arc3-v2-9-milestone2?scriptVersionId=364686331).

Le contrôle réel confirme Python 3.12.13, RTX PRO 6000 Blackwell (97887 MiB), CUDA 13.0, SGLang démarré et installation du hook visuel. Les cinq sources ont été rattachées dans l'interface ; Internet reste désactivé. Quota gratuit observé : 28 heures GPU restantes.

Le test public est limité à cinq minutes après chargement, contre trente minutes auparavant : ses scores ne seront donc pas une comparaison équivalente. Le budget de l'évaluation cachée reste celui du candidat initial, jusqu'à neuf heures.

**Soumission officielle nouvelle : non encore enregistrée. Score nouveau : UNVERIFIED.** L'interface confirme qu'une soumission relance le notebook sur les jeux cachés ; elle attend la sortie `submission.parquet` de la version terminée. Le petit Parquet public de prévalidation n'est jamais traité comme un score de jeu.

Les journaux originaux et les résultats négatifs sont conservés dans ce dossier. `session-evidence.json` porte les identifiants et l'état détaillé.

## Retest après le second incident

La preuve JSON affichée par Kaggle pour la version 3 confirme exactement 48 réponses, 99 actions, deux erreurs `model:ReadTimeout` et zéro `crashed_games`. Les journaux placent les deux délais au terme programmé des cinq minutes.

La version 4 distingue maintenant les délais de lecture survenus **après** l'échéance publique, à l'aide d'une horloge monotone : ils restent enregistrés, entraînent un statut **PARTIAL**, et ne suppriment pas la sortie de prévalidation. Un délai prématuré, une réponse entièrement vide, une partie publique en panne ou l'absence de jeu réel restent bloquants. Dans le rerun caché, les pannes sont conservées comme **PARTIAL** ; Kaggle peut noter les actions réellement exécutées au lieu de perdre tout le résultat sur une panne isolée.

- **PASS** : 115 tests et 16 sous-tests, incluant expiration publique, délai prématuré, délai caché, absence de jeu et maintien des échecs dans le rapport.
- **PASS** : export du brouillon Kaggle puis comparaison exacte des 14 cellules de code avec le candidat testé ; cinq sources toujours présentes.
- SHA-256 du candidat v4 : `c010f3cde9433b962810c264951098681116c35dd6c7e5067135fa1b8f97fb02`.
- Retest réellement démarré : version Kaggle 4, [`364690053`](https://www.kaggle.com/code/drstarck/astra-aion-arc3-v2-9-milestone2?scriptVersionId=364690053), RTX PRO 6000, **RUNNING**.

Cette correction ne transforme pas un échec en succès ni un test public en score officiel.
