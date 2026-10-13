# Checkpoint local — langues et captures, 13 octobre 2026

Mandat : ConvertAir puis DocCipher dans toutes les langues de leurs applications,
avec de vrais écrans localisés. HGQ et PeakSolo restent différés. Aucun push ni
déploiement effectué.

## Résultat vérifié

- 22 variantes BCP-47, 402 unités par catalogue ; 12 pages dans chaque variante.
  Français aux URL racine, arabe RTL, liens de langue réciproques, navigation sans
  JavaScript, états des animations localisés.
- Construction : 268 pages produites. Validation historique des pages racine
  PASS. Validation i18n : 264 pages et 546 nouveaux médias PASS. Chargement initial
  produit maximal : 186 987 octets, incluant scripts et styles de langue.
- Tests Python : 27/27 PASS ; tests JavaScript des formulaires : 28/28 PASS.
- Chrome local : 264 rendus produit (22 variantes × 2 apps × 3 largeurs ×
  2 thèmes), 220 pages générales à 320 px et 22 variantes d'interaction PASS.
  Zéro requête externe, erreur JavaScript ou débordement horizontal détecté.
  Navigation sans JS et clavier vérifiée ; ancres des anciennes politiques
  bilingues adaptées lors du changement de langue.
- Export : 866 fichiers ; 12 390 liens locaux validés.
  SHA-256 agrégé :
  `6d617a99902a8b77121e17a33427f1e5094b2047a60a2c4485c06832f78f7236`.
- Médias : hashes des sources et dérivés vérifiés ; provenance versionnée dans
  `content/i18n-media-provenance.json`, exclue de l'export. Les 546 ajouts pèsent
  19 792 742 octets. Géométrie commune des téléphones conservée.

## Corrections et preuves conservées

Les premiers catalogues incomplets ou mécaniques ont été refusés, puis remplacés
par les traductions complètes. Dix anomalies de formulation PT-BR ont été
corrigées puis revérifiées indépendamment. Des paragraphes de sécurité allemands
ont été complétés. Les dates CJK sont comparées par valeur calendérique ; le
test conserve le refus d'un mois erroné.

La première campagne navigateur complète a détecté un débordement de 23 px d'un
titre DocCipher néerlandais à 320 px. Retour à la ligne et césure corrigés, puis
nouvelle campagne complète PASS. Le débordement n'est pas masqué globalement.

Preuves locales : `_apercu/i18n-proof/browser-proof.json` et captures associées ;
logs et checkpoint détaillé dans `C:/BB16/00_INBOX/site-i18n-20261013`.
Ces fichiers de travail ne sont pas publiés.

## Limites

Relecture humaine native et validation juridique : NOT_OBSERVED. La traduction
ne certifie aucune conformité mondiale. Les prix restent les références France
en euros ; aucun prix régional Store n'est inventé. Les drapeaux de publication
Store restent inchangés.

ConvertAir utilise des captures historiques d'intégration. DocCipher utilise
176 captures fraîches des widgets réels sur hôte, avec données et services
fictifs ; le français conserve les médias existants. Les clips sont des
animations de captures fixes. Appareil physique, achats et publication :
NOT_OBSERVED. La CI complète DocCipher a été interrompue par protection du disque
pendant le build Android ; elle n'est pas déclarée réussie. Voir son checkpoint
spécifique pour les tests du générateur et les contrôles déjà passés.

La modification du footer X préexistante dans `build_site.py` est préservée hors
du commit de ce lot. Les preuves de cet export portent sur le travail local.
