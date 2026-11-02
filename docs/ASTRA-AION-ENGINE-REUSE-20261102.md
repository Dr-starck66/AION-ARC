# ASTRA AION ENGINE Ω — extraction sans remplacer le candidat Kaggle

**Date : 2026-11-02. Statut : PARTIAL.** Prototype local et versionné, pas de produit commercial en production.

## Continuité et faits confirmés

- Dépôt : `Dr-starck66/AION-ARC`. Branche Kaggle d'origine : `astra/arc3-emergency-20261031`, **non modifiée** par cette extraction.
- Soumission Kaggle confirmée : **57886365**, score public **24,58/100**, sélectionnée pour la finale au dernier contrôle.
- Second candidat `v31` : version Kaggle `364873927`, envoyée le 2 novembre à 12:41:40 UTC, **Notebook Running** et score **UNVERIFIED** dans le dernier reçu.
- Quota officiel du compte au dernier contrôle : **0 nouvelle soumission aujourd'hui**. Le suivi existant est programmé à 23:30 Europe/Paris (22:30 UTC). Aucun doublon créé.
- Dossier de preuve : `reports/arc3-final-20261102/`. Le score public n'est pas le score privé final.

## Source et composants réellement réutilisés

- Le moteur de graphe visuel **déjà écrit dans notre dépôt** est `kaggle/arc3_graph_nav.py`. L'adaptateur `astra_aion_engine/adapters.py` charge **ce fichier existant** par chemin local : aucune deuxième copie de l'algorithme.
- Le nouveau `astra_aion_engine/core.py` fournit un contrat réutilisable **perception → planification → action** : état observé, actions légales, plan borné, exécution, résultat confirmé et audit minimal. Aucun besoin de réseau, GPU, SDK tiers ou identifiant.
- `tests/test_astra_aion_engine.py` inclut une simulation de formulaire indépendante de Kaggle et des contrôles adversariaux : action interdite, no-op, budget, erreur, échec de confirmation, absence de faux PASS, traces sans texte des actions.

## Utilisation

```python
from astra_aion_engine import AionEngine, Observation, Plan, Feedback

engine = AionEngine(
    observe=my_observer,  # retourne Observation(payload, frozenset(legal_actions))
    plan=my_planner,      # retourne Plan(tuple(actions)) ou None
    execute=my_actuator,  # retourne Feedback(executed, changed, goal_reached)
    max_actions=64,
)
outcome = engine.run()
print(outcome.status, outcome.reason, outcome.actions_executed)
```

**Contrat probatoire :** PASS si l'objectif est **réellement observé ou confirmé** ; PARTIAL si non résolu ou non pris en charge ; FAIL si plan/exécution invalides. Il s'agit du résultat d'une tâche d'adaptateur, **jamais d'un score Kaggle ni d'une preuve de navigation réelle**.

Reproduction :

```bash
python -m unittest discover -s tests -p test_astra_aion_engine.py -v
python -m compileall -q astra_aion_engine
```

Test en conteneur isolé, sans checkout complet : **13 PASS, 1 SKIP** (intégration avec le véritable fichier graph à tester dans le dépôt complet). Le navigateur n'est qu'une **simulation**, aucun site, robot ou compte externe activé.

## Distribution et prochaine intégration

Le cœur nouvellement écrit est du code ASTRA original, destiné à rester sous la licence MIT-0 du dépôt. **Aucun droit Duck/Tufa, modèle Qwen ou archive Kaggle n'est implicitement transféré** : audit tiers dans `docs/UPSTREAM-ATTRIBUTION-AND-LICENSE.md` avant redistribution d'un ensemble commercial.

Prochaine intégration : adapter **l'interface réelle déjà autorisée d'ASTRA Browser** à ce contrôleur, après inventaire du contrat et en préservant l'agent existant. Le présent commit n'a ni fusionné ce contrôleur dans la soumission Kaggle, ni créé de service ou tâche payante.
