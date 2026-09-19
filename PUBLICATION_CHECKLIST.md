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
- [ ] GitHub Pages sert `index.html` en HTTPS avec HTTP 200.
- [ ] Test mobile réel : navigation, focus clavier, aucune barre horizontale.
- [ ] Test desktop réel : navigation, images, pages 404 et liens mailto.
- [ ] `sitemap.xml`, `robots.txt`, canonical et Open Graph contiennent l'URL
      réelle et aucune valeur temporaire.
- [ ] Search Console configurée par le propriétaire du compte Google, si
      cette option est retenue.

Les conditions propres à un compte Google Play ou à un futur domaine sont
gérées séparément par leur propriétaire. Elles ne constituent pas des champs
à inventer dans ce site.

## Limites assumées

Les applications décrites sur ce site restent en développement ou en
préparation. Aucune URL Store n'est affichée tant qu'une adresse publique
réelle n'est pas confirmée.
