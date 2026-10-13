# Prix et confidentialité — 14 octobre 2026

La référence du catalogue France a été relue dans Google Play Console : ConvertAir 19,99 EUR/an, 49,99 EUR à vie au lancement ; produit standard 59,99 EUR encore en brouillon (prix futur prévu). Zéro base plan mensuel actif. DocCipher 19,99 EUR à vie actif. La présence en console ne prouve ni achat sur appareil ni disponibilité publique d'une app.

La source versionnée content/commercial-reference.json alimente les cartes tarifaires. Le validateur i18n compare prix ET périodicité dans les 22 variantes. La langue du site ne détermine pas le pays du compte Google Play ; les prix EUR affichés restent des références France.

Fiches et politiques distinguent traitement documentaire local et données d'achat Google Play/RevenueCat. Les vérifications Premium peuvent survenir hors d'un paiement. Les données pseudonymes/techniques, l'historique des achats et les statistiques de ventes sont mentionnés ; aucun document n'est envoyé par ces chemins. La portée des avis Google Play est conservée. WebDAV DocCipher demeure indisponible dans cette version.

## Vérifications

- Build : 268 pages, 22 variantes.
- validate_site.py : PASS.
- validate_i18n.py : PASS, 264 pages dont 88 avec garde prix/confidentialité, 546 médias.
- test_i18n.py : 9/9 PASS, incluant mutations ancien prix, période incorrecte, disclosure supprimée et mauvaise date.
- Export : 866 fichiers, 12 390 liens, SHA-256 4bc7aea0fc89504b0c43055ea7b6b8f9df9fc5e5305ffffc9decef66f547fb98.
- Revue indépendante ciblée : prix et formulations cohérents. Le tarif futur reste annoncé conformément au catalogue existant ; aucune activation Store.
- Campagnes locales exhaustives Python et navigateur : INTERRUPTED_LOW_DISK après alerte <1 GiB. Les réussites partielles et l'échec initial du gate d'avis (corrigé puis réussi) sont conservés dans la preuve locale. Pas de PASS global déduit de ces campagnes interrompues.
- CSS, JS et médias inchangés : anciennes preuves encore pertinentes pour leur périmètre. Aucun APK/AAB ni validation appareil dans ce lot.

Le site servi avant cette correction affichait encore les anciens tarifs ConvertAir et répondait 404 pour /en/convertair.html. Publication et contenu servi après correction seront contrôlés séparément.

Offre courante RevenueCat et intégrations du compte non recontrôlées jusqu'au bout : accès navigateur interrompu. Déclaration Data Safety effective, DPA et validation juridique globale non attestés ici. Relecture linguistique native non observée ; contrôles sémantiques automatisés et structurels ne sont pas une revue native.

Modification préexistante du footer X préservée hors commit. Aucun changement HGQ/PeakSolo, aucune publication d'application ni modification d'achat/Store.
