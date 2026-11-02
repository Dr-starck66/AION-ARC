# ARC-AGI-3 : résultat officiel du 2 novembre

La soumission **57886365**, notebook `drstarck/astra-aion-arc3-v2-9-milestone2`, version **4**, `scriptVersionId=364690053`, a réussi. L'interface authentifiée Kaggle affiche **24,58/100** et le classement public **2103/5048** au contrôle de ce dossier. Ancienne référence : soumission 57848621, 0,07/100. L'objectif 100/100 n'est pas atteint. Le classement privé final reste inconnu.

Preuve structurée : [official-result.json](official-result.json). La note 12,22 du smoke test de la veille concernait deux jeux publics pendant cinq minutes : elle n'est pas la note officielle 24,58. Le dialogue de soumission réussie consulté ne propose pas de journaux du rerun caché ; aucune panne cachée particulière n'est donc affirmée.

Un second candidat expérimental reprend le même moteur, sans changement de poids, de scheduler ou de budget caché. Il expose RESET sur le niveau courant et active le garde upstream contre les no-op répétés, avec comparaison de toute l'image. Une insistance immédiate peut contourner ce refus ; ce n'est pas une interdiction permanente. Ces fonctions peuvent coûter des tours supplémentaires du modèle et leur bénéfice doit être mesuré.

Génération : `python scripts/build_arc3_recovery_challenger.py`. Candidat : `kaggle/v30-recovery/submission.ipynb`. Le brouillon Kaggle exporté contient exactement les 14 cellules de code attendues et conserve les cinq sources. Seule la cellule de configuration du moteur change par rapport à la version 4 ; le fichier local ajoute aussi un en-tête documentaire. Les tests passent : 115 tests, 16 sous-tests ; 34 fichiers Python et le sandbox embarqué compilent ; le contrôle EOF corrompu échoue comme prévu ; six contrats du garde sont vérifiés, notamment la possibilité d'insister, les clics distincts, les changements de niveau et les observations contradictoires.

Exécution Kaggle réelle lancée : version **5**, `scriptVersionId=364868478`, RTX PRO 6000, Python 3.12.13 confirmé par le journal. Son résultat et son éventuelle soumission officielle seront consignés dans [challenger.json](challenger.json). Au lancement, une soumission officielle reste autorisée aujourd'hui. La version 4 et son score sont préservés.

Voir [comparaison des trois premiers](top-three-review.md). Aucun accès à un code privé, achat, nouveau compte, service payant ou secret publié.

Liens officiels :

- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/submissions
- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard
- https://www.kaggle.com/code/drstarck/astra-aion-arc3-v2-9-milestone2?scriptVersionId=364868478
