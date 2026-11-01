# AION-ARC : reprise Kaggle via une session navigateur existante

Procédure issue des exécutions réelles de la nuit du 1 au 2 novembre 2026. Aucun jeton, cookie, lien signé ou mot de passe ne doit être copié dans ce dépôt. Cette procédure ne crée pas de service permanent.

## Reprise et intégrité

1. Lire le dernier état dans `reports/arc3-final-20261101/` et reprendre la branche `astra/arc3-emergency-20261031`. Ne pas réécrire le notebook historique `drstarck/notebook2700e63354` : version 6, résultat officiel 0,07.
2. Générer et vérifier le candidat avec `python scripts/arc3_kaggle_final_run.py`. Le mode sans `--execute` contrôle uniquement le paquet ; ce n'est pas une exécution Kaggle.
3. Réutiliser une session déjà ouverte sur le compte `drstarck`, vérifiée par la lecture des notebooks privés et du profil. L'accès a été confirmé pendant cette mission ; sa disponibilité future doit être recontrôlée. Aucune nouvelle authentification n'a été nécessaire ici.
4. Candidat actif : `drstarck/astra-aion-arc3-v2-9-milestone2`. Vérifier la version précise, pas seulement le dernier notebook affiché par défaut.

## Piège de l'import UI observé

L'import du fichier complet a retiré les sources et sélectionné T4 x2 malgré les métadonnées du fichier. Le contrôle matériel a correctement rejeté la version 2. Recontrôler les réglages réels après chaque import :

- compétition `arc-prize-2026-arc-agi-3` ;
- datasets `dfranzen/pennyroyal-v253` et `dfranzen/taaf-kaggle-source-bundle-copy` ;
- modèles `dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/transformers/default/1` et `dfranzen/albucino-qwen3-8-flash-next-drafter/transformers/default/1` ;
- GPU **RTX PRO 6000**, visible seulement après rattachement de la compétition ;
- Internet désactivé ; environnement original Python **3.12** épinglé ; quota gratuit disponible.

Dans « Add Input », les URL complètes ont trouvé exactement les datasets et modèles, contrairement à une recherche libre avec `owner/slug`. Les modèles demandent ensuite la sélection de leur variante Transformers/default/V1.

Pour une petite correction, conserver les cinq sources et modifier seulement les cellules concernées. Avec l'éditeur observé, `setValue` seul n'a pas remplacé le texte CodeMirror ; la sélection dans la cellule puis Ctrl+A et le collage du wrapper `exec(compile(...))` ont fonctionné. L'affichage DOM tronque les longues lignes vers 2 090 caractères : il ne prouve pas leur intégrité complète.

**Contrôle obligatoire effectué ici :** File → Download Notebook, puis comparaison exacte de toutes les cellules de code de l'export avec celles du candidat généré. Les 14 cellules de la v4 correspondaient, avec cinq sources préservées. Ne pas se contenter d'une compilation du fichier local.

## Deux étapes distinctes

**A — Save & Run All.** Démarrer une version nommée avec le GPU. Noter `scriptVersionId`, le type de GPU, la durée, les journaux et les preuves d'actions. Le test public est volontairement borné à cinq minutes après le lancement du benchmark ; les scores de deux jeux ne prédisent pas le classement. Le fichier `submission.parquet` de cette étape est un fichier de validation, pas un résultat officiel.

**B — Submit Prediction.** Uniquement après la fin de A et l'apparition du fichier attendu, sélectionner le notebook et la **version exacte**. Le dialogue officiel indique qu'il relance le notebook avec les jeux cachés. Ne jamais téléverser simplement le petit Parquet de validation comme s'il était la mesure du solveur. Conserver le quota affiché et le résultat de l'envoi.

Dans la liste officielle des soumissions, la case de sélection de chaque ligne porte son identifiant numérique dans l'attribut DOM `name`. Cela a été vérifié sur la soumission historique : `57848621`. Lire cet attribut sur la nouvelle ligne sans cocher la case. Ne pas confondre cet identifiant avec `scriptVersionId` ou le numéro de version.

## Verdicts et conservation

- « Save & Run All terminé » ne prouve pas un score officiel.
- Une vraie réponse seulement composée de `reasoning` ou `reasoning_content` doit rester accessible à la continuation native de Duck. Une réponse entièrement vide reste une erreur.
- Un ReadTimeout ne relève de l'arrêt public prévu que s'il survient après l'échéance monotone enregistrée ; il reste visible dans `budget_timeouts` avec statut **PARTIAL**. Les erreurs prématurées et les parties publiques en panne restent bloquantes.
- Lors du rerun caché, conserver les pannes et les classer **PARTIAL** ; permettre à Kaggle de noter les actions réelles plutôt que perdre tous les résultats pour une panne isolée. Sans action réelle et réponse réelle du modèle, refuser toute réussite.
- État en attente ≠ score obtenu. Score public ≠ score privé final. Aucun score ou prix de 100/100 ne doit être affirmé sans résultat officiel.
- Conserver les résultats négatifs, les journaux, les empreintes et les reçus sur la branche existante. Ne pas créer de workflow, de facture ou d'automatisation en doublon pour poursuivre ce suivi.
