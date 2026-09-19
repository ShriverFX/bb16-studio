# Checklist de publication — BB16 Studio

Publication de la vitrine explicitement demandée par le propriétaire le
19 septembre 2026. Les informations légales manquantes ne sont pas inventées ;
leur complétion et la vérification du compte Organisation restent à suivre.

## Champs encore requis

- [ ] Nom légal exact de l'éditeur.
- [ ] Adresse publique de l'éditeur.
- [x] Dépôt public dédié : `ShriverFX/bb16-studio`.
- [x] URL configurée : `https://shriverfx.github.io/bb16-studio/`.

## Vérifications avant publication

- [x] `python build_site.py --site-url ... --base-path ...` exécuté avec les
      valeurs réelles.
- [x] `python validate_site.py` retourne `SITE_VALIDATION_OK`.
- [x] GitHub Pages sert `index.html` en HTTPS avec HTTP 200 ; les 12 pages,
      CSS, quatre images, sitemap et robots ont été contrôlés le 19 septembre.
- [x] Navigateur : accueil, catalogue, fiche DocCipher, images chargées et 404
      imbriquée avec liens racine. Aucun débordement horizontal sur les pages
      contrôlées au viewport mobile 390 px (largeur cliente 375 px) et 637 px.
- [ ] Test mobile réel : navigation, focus clavier, aucune barre horizontale.
- [ ] Test desktop réel : navigation, images, pages 404 et liens mailto.
- [x] `sitemap.xml`, `robots.txt`, canonical et Open Graph contiennent l'URL
      réelle et aucune valeur temporaire.
- [ ] Search Console configurée par le propriétaire du compte Google, si
      cette option est retenue.

Les conditions propres à un compte Google Play ou à un futur domaine sont
gérées séparément par leur propriétaire. Elles ne constituent pas des champs
à inventer dans ce site.

Publication initiale : workflow `35459819961` réussi. Correctif de contact :
commit `489d917`, workflow `35460709304` réussi ; lien
`mailto:bb16studio@gmail.com` relu dans le HTML HTTPS et le navigateur.
Le placeholder initial reste un défaut détecté puis corrigé, pas un PASS
initial. Les essais sandbox réseau et les délais du navigateur ont été
distingués de l'accès public confirmé depuis l'environnement utilisateur.

## Limites assumées

Les applications décrites sur ce site restent en développement ou en
préparation. Aucune URL Store n'est affichée tant qu'une adresse publique
réelle n'est pas confirmée.
