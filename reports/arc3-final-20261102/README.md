# ARC-AGI-3 : résultat officiel du 2 novembre

La soumission **57886365**, notebook `drstarck/astra-aion-arc3-v2-9-milestone2`, version **4**, `scriptVersionId=364690053`, a réussi. L'interface authentifiée Kaggle affiche **24,58/100** et le classement public **2103/5048** au contrôle de ce dossier. Ancienne référence : soumission 57848621, 0,07/100. L'objectif 100/100 n'est pas atteint. Le classement privé final reste inconnu.

**Nouvel envoi effectivement enregistré le 2 novembre à 12:41:40 UTC :** v31, notebook version **6**, `scriptVersionId=364873927`, état officiel **Notebook Running**. Score et identifiant numérique de cette nouvelle soumission encore **UNVERIFIED** : le numéro de version ne doit pas être présenté comme un numéro de soumission. Voir [le reçu officiel](official-v31-browser-receipt.json). La soumission à 24,58 reste explicitement sélectionnée pour le score final. Le quota officiel affiche désormais **0 restant aujourd'hui**, avec une soumission en cours.

| Candidat | Test public configuré à 300 s, deux jeux | Réponses / actions | Évaluation officielle |
| --- | --- | --- | --- |
| v29, version 4 | 12,22 ; quatre niveaux | 52 / 112 | **24,58**, soumission 57886365, sélectionnée |
| v30, version 5, reprise et répétitions | 6,77 ; trois niveaux | 53 / 60 | Non envoyée ; résultat négatif conservé |
| v31, version 6, images réelles des animations | 7,14 ; trois niveaux | 43 / 74 | **Notebook Running**, score inconnu |

Ces essais ne démontrent aucune amélioration publique. Le dernier quota officiel est utilisé pour une expérience sur les autres jeux, avec la référence conservée. Un passage stochastique sur deux jeux ne prédit pas la note cachée. V31 a terminé sans panne du moteur en 977,4 s ; trois délais d'arrêt sont gardés PARTIAL. Le benchmark a duré 315 s, dont la fin des requêtes en cours après la limite configurée : ce n'est pas une comparaison strictement égale en durée réelle. [Journal v31](v31-version6-browser-log.txt).

Le suivi existant `6ae5fe6216e0819197eddcfe2786a44e` a été actualisé avec ces faits et un **contrôle unique le 2 novembre à 23:30 Europe/Paris, 22:30 UTC**. Les créneaux ordinaires 09:00, 14:00 et 19:00 sont préservés ; aucune nouvelle tâche n'est créée. À ce créneau additionnel, contrôler seulement Kaggle, récupérer état/identifiant/score/rang, préserver les preuves et sélectionner la seconde candidature si elle est terminée. Cet enregistrement de suivi ne prouve pas que le contrôle futur a déjà été exécuté.

Preuve structurée : [official-result.json](official-result.json). La note 12,22 du smoke test de la veille concernait deux jeux publics pendant cinq minutes : elle n'est pas la note officielle 24,58. Le dialogue de soumission réussie consulté ne propose pas de journaux du rerun caché ; aucune panne cachée particulière n'est donc affirmée.

Un second candidat expérimental reprend le même moteur, sans changement de poids, de scheduler ou de budget caché. Il expose RESET sur le niveau courant et active le garde upstream contre les no-op répétés, avec comparaison de toute l'image. Une insistance immédiate peut contourner ce refus ; ce n'est pas une interdiction permanente. Ces fonctions peuvent coûter des tours supplémentaires du modèle et leur bénéfice doit être mesuré.

Génération : `python scripts/build_arc3_recovery_challenger.py`. Candidat : `kaggle/v30-recovery/submission.ipynb`. Le brouillon Kaggle exporté contient exactement les 14 cellules de code attendues et conserve les cinq sources. Seule la cellule de configuration du moteur change par rapport à la version 4 ; le fichier local ajoute aussi un en-tête documentaire. Les tests passent : 115 tests, 16 sous-tests ; 34 fichiers Python et le sandbox embarqué compilent ; le contrôle EOF corrompu échoue comme prévu ; six contrats du garde sont vérifiés, notamment la possibilité d'insister, les clics distincts, les changements de niveau et les observations contradictoires.

Exécution Kaggle réelle lancée : version **5**, `scriptVersionId=364868478`, RTX PRO 6000, Python 3.12.13 confirmé par le journal. Son résultat et son éventuelle soumission officielle seront consignés dans [challenger.json](challenger.json). Au lancement, une soumission officielle reste autorisée aujourd'hui. La version 4 et son score sont préservés.

**Résultat de la version 5 :** exécution réussie en **883,6 s**, mais comparaison publique inférieure : **6,77**, trois niveaux, 53 réponses et 60 actions ; zéro panne et zéro erreur prématurée, deux délais à l'arrêt programmé conservés en PARTIAL. Contre 12,22 et quatre niveaux pour v29. Ce résultat négatif reste conservé dans [le journal intégral](v30-version5-browser-log.txt) ; cette variante n'est pas envoyée au dernier quota officiel. Un passage stochastique ne prouve pas la causalité de la baisse.

Un second essai **v31**, notebook version **6**, repart de v29 sans les réglages de reprise v30. Il active seulement les images `peak` des animations ordinaires et fatales : une véritable image intermédiaire, plutôt qu'un composite. Cette piste répond à une limite documentée de perception ; elle n'est pas une amélioration démontrée. Le brouillon exporté correspond aux 14 cellules de code et aux cinq sources. Le vérificateur CPU teste aussi l'image choisie (couleurs et dimensions), l'absence de transition, l'absence de pixels transitoires et le rejet d'une valeur booléenne invalide. Détails : [animation-challenger.json](animation-challenger.json).

Voir [comparaison des trois premiers](top-three-review.md). Aucun accès à un code privé, achat, nouveau compte, service payant ou secret publié.

Liens officiels :

- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/submissions
- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard
- https://www.kaggle.com/code/drstarck/astra-aion-arc3-v2-9-milestone2?scriptVersionId=364868478
