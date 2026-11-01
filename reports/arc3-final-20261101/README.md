# ASTRA AION-ARC — exécution Kaggle finale

État global : **PARTIAL**. **Nouvelle soumission officielle enregistrée**, rerun caché en cours. Aucun nouveau score officiel n'est affirmé.

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

Le petit Parquet public de prévalidation n'est jamais traité comme un score de jeu. La nouvelle soumission officielle déclenche le rerun caché du notebook, conformément au dialogue Kaggle.

Les journaux originaux et les résultats négatifs sont conservés dans ce dossier. `session-evidence.json` porte les identifiants et l'état détaillé.

## Retest après le second incident

La preuve JSON affichée par Kaggle pour la version 3 confirme exactement 48 réponses, 99 actions, deux erreurs `model:ReadTimeout` et zéro `crashed_games`. Les journaux placent les deux délais au terme programmé des cinq minutes.

La version 4 distingue maintenant les délais de lecture survenus **après** l'échéance publique, à l'aide d'une horloge monotone : ils restent enregistrés, entraînent un statut **PARTIAL**, et ne suppriment pas la sortie de prévalidation. Un délai prématuré, une réponse entièrement vide, une partie publique en panne ou l'absence de jeu réel restent bloquants. Dans le rerun caché, les pannes sont conservées comme **PARTIAL** ; Kaggle peut noter les actions réellement exécutées au lieu de perdre tout le résultat sur une panne isolée.

- **PASS** : 115 tests et 16 sous-tests, incluant expiration publique, délai prématuré, délai caché, absence de jeu et maintien des échecs dans le rapport.
- **PASS** : export du brouillon Kaggle puis comparaison exacte des 14 cellules de code avec le candidat testé ; cinq sources toujours présentes.
- SHA-256 du candidat v4 : `c010f3cde9433b962810c264951098681116c35dd6c7e5067135fa1b8f97fb02`.
- Retest réellement exécuté : version Kaggle 4, [`364690053`](https://www.kaggle.com/code/drstarck/astra-aion-arc3-v2-9-milestone2?scriptVersionId=364690053), RTX PRO 6000. Kaggle confirme **925,7 secondes, successful**.
- Preuve de jeu : **52 réponses du modèle, 112 actions, quatre niveaux franchis, zéro jeu en panne, zéro erreur prématurée**. Deux ReadTimeout de fin conservés dans `budget_timeouts`, statut de jeu **PARTIAL**. Moyenne de 12,22 sur deux jeux et cinq minutes, sans valeur de score officiel ni comparaison équivalente au test de trente minutes.

Cette correction ne transforme pas un échec en succès ni un test public en score officiel.

## Soumission officielle enregistrée

**PASS — enregistrement**, le 2 novembre 2026 à **00:18:06, heure de Paris** (1 novembre 23:18:06 UTC), depuis le compte `drstarck`.

- Notebook : `drstarck/astra-aion-arc3-v2-9-milestone2`.
- Version exacte : **4**, `scriptVersionId=364690053`.
- Fichier sélectionné : `submission.parquet` ; l'option « File Upload » est désactivée pour cette compétition. L'envoi porte donc sur le notebook à réexécuter avec les jeux cachés.
- État officiel observé après envoi : **Notebook Running**.
- [Page officielle des soumissions](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/submissions).
- Description enregistrée : « ASTRA AION-ARC v29 / f34ebbff. 115 tests + 16 subtests. RTX offline. 52 model responses, 112 public actions. Expected timed stops retained as PARTIAL. Full hidden evaluation budget. »
- Identifiant numérique de **soumission** : **UNVERIFIED pendant le calcul** ; la ligne en cours n'expose pas encore la case `name` contenant l'identifiant. Ne jamais lui substituer `364690053`, qui est l'identifiant de version du notebook.
- Nouvelle note et nouveau rang : **UNVERIFIED — calcul Kaggle en cours**. Dernière note officielle effectivement vérifiée : **0,07/100** sur l'ancienne soumission `57848621`.
- Intervention manuelle demandée : **aucune**. Dépense créée : **aucune**. Aucun nouveau workflow ni nouveau service n'a été créé.

La procédure reproductible et les pièges réels de l'interface sont conservés dans [`docs/ARC3-WORK-BROWSER-EXECUTION.md`](../../docs/ARC3-WORK-BROWSER-EXECUTION.md). Les journaux du retest et le reçu UI sont inclus dans ce dossier. Le résultat 100/100 et la victoire ne sont pas obtenus ni annoncés.

**PASS — continuité :** le reçu et la version exacte ont été ajoutés à la tâche centrale déjà active `6ae5fe6216e0819197eddcfe2786a44e`, sans nouvelle automatisation et sans modification de son calendrier ni de ses autres modules. Cela enregistre une consigne de suivi ; cela ne prouve pas un résultat futur du calcul. Au dernier contrôle de cette session, environ trois minutes après l'envoi, Kaggle affiche toujours **Notebook Running**.
