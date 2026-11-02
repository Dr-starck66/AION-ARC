# Les trois premiers : ce qui est effectivement accessible

Positions et scores lus dans le classement Kaggle authentifié le 2 novembre 2026, vers midi UTC. Ils sont publics, provisoires et différents du classement privé final.

| Rang | Équipe | Score public observé | Méthode analysable | Conclusion vérifiable |
| --- | --- | --- | --- | --- |
| 1 | Yi-Chia Chen @ Fields Model | 75,56 | Aucun code ou compte rendu ARC-AGI-3 de cette version trouvé dans les sources recherchées | Les forces techniques et défauts de cette version restent UNVERIFIED. Ne pas les déduire de sa seule note. |
| 2 | Tufa Labs | 70,24 | Publication et dépôt du Milestone 1 accessibles ; la version actuelle à 70,24 n'est pas reproduite par ces seules ressources | Base exploitable : agent de code Python, perception de grille et historique. Le dépôt public ne prouve pas les méthodes exactes de la version actuelle. |
| 3 | xz (`xiaoz259`) | 58,59 | Aucun code ou compte rendu ARC-AGI-3 de cette version trouvé dans les sources recherchées | La technique de cette version reste UNVERIFIED. Son ancien nom « faster machine is all you need » ne prouve aucune configuration matérielle. |

## Tufa : analyse du matériel public

Le modèle inspecte les observations dans un REPL Python et exécute ses actions via des outils. Cette architecture permet de mesurer, tester des hypothèses et réutiliser du code. Les représentations visuelles et textuelles sont complémentaires. Le dépôt fournit les actions et raisonnements d'un benchmark répété : utile pour repérer les échecs et la variance, au lieu de sélectionner un seul essai réussi.

Limites documentées de cette ancienne publication : performance très inégale selon les jeux ; contexte ancien évincé ; capacités du modèle et débit contraints par le GPU Kaggle. Ces constats ne décrivent pas nécessairement leur dernière version. La publication compare aussi du calcul externe : ses résultats ne sont pas directement transférables au budget Kaggle.

## Application dans AION-ARC

La base Duck de Tufa et les améliorations publiques de Daniel Franzen sont déjà reprises avec leurs attributions dans v29 : modèle Qwen3.8 FlashNext, animations, images de différences, UNDO, préfixes conservés et priorité de calcul. La référence officielle AION est désormais 24,58, inférieure au meilleur score 34,30 affiché par le notebook public Franzen au contrôle web. Il serait faux d'en conclure un effet causal : matériel, tirages et versions ne sont pas une ablation contrôlée.

Le candidat v30 teste une variation limitée : rendre un redémarrage de niveau explicite et éviter de répéter une action observée sans effet, avec une possibilité d'insister. Il conserve le modèle, le scheduler et le budget caché pour limiter les facteurs qui changent. Les deux jeux publics et leur budget de cinq minutes restent identiques ; un seul passage aléatoire ne suffit pas à établir une supériorité scientifique. La soumission 24,58 est conservée comme référence pendant l'essai.

Le test v30 a donné 6,77 contre 12,22 pour v29 : il reste un résultat négatif, sans soumission officielle. V31 revient aux contrôles initiaux et teste des images réelles au pic des animations. Franzen décrit des essais non concluants avec des composites ; une image réelle n'est pas cette même représentation et son bénéfice reste à mesurer. Le coût supplémentaire en images peut aussi nuire au débit. La décision repose sur les tests réels, pas sur une promesse x10.

## Sources primaires consultées

- Classement Kaggle : https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard
- Tufa, publication datée du 1 juillet 2026 : https://tufalabs.ai/research/duck-harness/
- Code Tufa : https://github.com/Tufalabs/duck-harness
- Code et note Franzen : https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution
- Compte rendu Franzen : https://github.com/da-fr/arc-agi-3-solution/blob/main/WRITEUP.md

Recherches ciblées effectuées sur les noms, pseudos, Kaggle et GitHub des trois équipes. « Non trouvé » ne signifie pas « prouvé privé » ni « n'existe pas ». Aucune faiblesse technique n'est inventée pour les deux solutions non inspectables ; aucun gain x10 ou score 100 n'est revendiqué.
