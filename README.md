# BB16 Studio — site statique

Site officiel statique de BB16 Studio, prévu pour GitHub Pages. Le site est
généré sans dépendance externe par `build_site.py`. Il reste publiable depuis
un dépôt public qui ne contient que ce dossier.

## Génération locale

Depuis cette racine :

```powershell
python .\build_site.py
```

La configuration de publication prévue pour le dépôt `ShriverFX/bb16-studio`
utilise une origine seule et un chemin de base séparé :

```powershell
python .\build_site.py `
  --site-url 'https://shriverfx.github.io' `
  --base-path '/bb16-studio/'
```

La génération normale utilise les six assets déjà copiés dans ce dépôt. Elle
ne dépend d'aucun dépôt privé voisin. Pour actualiser volontairement ces
copies depuis les projets source locaux, utiliser explicitement
`python .\build_site.py --import-assets`.

Le logo BB16 Studio fourni par le propriétaire est conservé sans modification
dans `assets/branding/bb16-studio-logo.jpg` (1280 × 1280). Le bleu officiel confirmé par le propriétaire,
`#0097D7`, est la couleur principale du site. Le logo HGQ transparent provient de
`HGQ/hgq/assets/images/Logo_hgq_fond_transparent.png` (709 × 784), également sans
modification. Les empreintes des deux originaux sont vérifiées par le validateur.
Le logo BB16 apparaît dans l'en-tête, l'accueil, la page Studio et les métadonnées
du site ; HGQ utilise son logo sur l'accueil, le catalogue et sa fiche.

Elle produit les pages HTML, `sitemap.xml`, `robots.txt` et `404.html`. Les
liens internes sont préfixés par le chemin de base afin de fonctionner depuis
une page 404 imbriquée.

Le site n'embarque aucun code privé d'application, document interne, secret,
fichier Firebase, configuration de paiement, capture d'écran ou donnée
utilisateur.

## Pages

`index.html`, `studio.html`, `apps.html`, `convertair.html`,
`doccipher.html`, `hgq.html`, `support.html`, `contact.html`,
`privacy.html`, `legal.html` et `data-deletion.html` sont générés en français.

Les pages produit décrivent l'état connu avec prudence. Elles n'affichent pas
de faux lien de téléchargement ; les applications sont en préparation ou en
développement.

## Vérification

```powershell
python .\validate_site.py
```

La validation vérifie les pages attendues, les liens locaux, les assets, les
liens canoniques, les liens depuis une 404 imbriquée, l'absence de secrets
connus et l'absence de scroll horizontal dans la feuille de style. Elle ne
publie pas le site et ne remplace pas la confirmation des informations
d'identité encore attendues.
