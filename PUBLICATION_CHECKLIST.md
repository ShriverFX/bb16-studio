# Checklist de publication — BB16 Studio

Le site local est prêt pour revue. La publication reste bloquée jusqu'à la
complétion des champs d'identité et du dépôt cible.

## Champs encore requis

- [ ] Nom légal exact de l'éditeur.
- [ ] Adresse publique de l'éditeur.
- [ ] Propriétaire et nom exact du dépôt public GitHub Pages.
- [ ] URL Pages finale ; régénérer avec `--site-url` et `--base-path`.

## Vérifications avant publication

- [ ] `python build_site.py --site-url ... --base-path ...` exécuté avec les
      valeurs réelles.
- [ ] `python validate_site.py` retourne `SITE_VALIDATION_OK`.
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
