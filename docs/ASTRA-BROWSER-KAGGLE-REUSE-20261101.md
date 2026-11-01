# ASTRA Ω — inventaire du navigateur existant pour AION-ARC / Kaggle
**Audit contrôlé le 2026-11-01, Europe/Paris.** Ce document est une continuité interprojets, pas un nouveau navigateur et pas une soumission Kaggle.

## Briques retrouvées et vérifiées sur leurs sources connectées

- **ASTRA CLOUD BROWSER Ω v0.2.0** : dépôt personnel `Dr-starck66/indexation`, source `tools/astra-cloud-browser/` et pont `tools/astra-free-workers/browser-bridge.mjs`. Code vérifié par le connecteur GitHub. La configuration `wrangler.toml` n'autorise actuellement que neuf sites personnels (plus variantes www) ; **kaggle.com n'y figure pas** et `ENABLE_INTERACTION="false"`. Le moteur ouvre une **nouvelle session Chromium** à chaque plan (`browser.newPage()`, `browser.close()`) ; ne conserve pas les cookies de connexion.
- **ASTRA Secure Operator** : branche `astra/carlease-browser-secure-operator-20261101` du même dépôt, dossier `tools/astra-cloud-browser/secure-operator/`, actuellement spécifiquement borné à Netlify/Porkbun et au domaine `carleasedeal.net`. Selon son README, non déployé dans Cloudflare, n'accepte ni login Kaggle ni click/type arbitraires.
- **ASTRA CRAWL Ω / astra-playwright-mcp** : projet Railway `astra-crawl` (`33eab60b-666b-492e-ad99-5c4509666754`), service `d866278c-5faa-4965-9040-4397b3177c73`, domaine préexistant `astra-playwright-mcp-production.up.railway.app`. Le déploiement consulté est **REMOVED** (arrêt journalisé le 2026-10-30). Aucune réactivation : l'utilisateur interdit de rouvrir des dépenses Railway.

## Conséquence pour l'urgence Kaggle
Ne pas dire « pas de navigateur », ne pas demander de mot de passe, ne pas redemander d'autorisation déjà donnée. **Il existe bien plusieurs briques navigateur ASTRA**. Toutefois, une capacité de navigation sur une page publique ne donne pas les cookies de la session Kaggle `drstarck` ni l'autorisation de déclencher un notebook privé. Aucune des briques examinées ne fournit, en l'état observé, une session Kaggle authentifiée et réutilisable depuis les connecteurs présents.

Notre candidat est `kaggle/v29-milestone2/submission.ipynb`; le programme de soumission est `scripts/arc3_kaggle_final_run.py`, et le test réel d'un niveau de `tu93` a réussi sur l'API publique ARC. **Score officiel nouveau : UNVERIFIED**. Ancienne note documentée : 0,07/100. Date limite : 2026-11-02 23:59 UTC.

La prochaine priorité n'est pas d'inventer un autre navigateur : **retrouver une session Kaggle autorisée déjà liée à l'un de ces opérateurs, ou une connexion CLI préexistante**, puis tester effectivement le dépôt du notebook, lire l'identifiant de soumission et le score. Ne pas activer Railway ni acheter un service.
