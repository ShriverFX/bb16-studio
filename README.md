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

La génération normale utilise les sept assets déjà copiés dans ce dépôt. Elle
ne dépend d'aucun dépôt privé voisin. Pour actualiser volontairement ces
copies depuis les projets source locaux, utiliser explicitement
`python .\build_site.py --import-assets`.

Le logo BB16 Studio fourni par le propriétaire est conservé sans modification
dans `assets/branding/bb16-studio-logo.jpg` (1280 × 1280), affiché en mode clair.
La variante `assets/branding/bb16-studio-logo-dark.png` (1254 × 1254 RGBA),
affichée en mode sombre, a été préparée
avec l'outil intégré imagegen pour retirer le fond blanc et préserver les
lettres blanches sur fond noir. L'alpha transparent est conservé. Le bleu
officiel confirmé par le propriétaire, `#0097D7`, est la couleur principale du
site. Le logo HGQ transparent provient de
`HGQ/hgq/assets/images/Logo_hgq_fond_transparent.png` (709 × 784), également sans
modification. Les empreintes des deux originaux sont vérifiées par le validateur.
Le logo BB16 est grand et centré dans l'en-tête, sans texte de marque ajouté
à côté ; la navigation est centrée en dessous. HGQ utilise son logo sur
l'accueil, le catalogue et sa fiche, sans fond blanc ajouté.

## Apparence claire et sombre

Le sélecteur « Clair / Sombre » sous la navigation change la palette de toutes
les pages et affiche le logo adapté : JPG original sur blanc en clair, PNG
transparent sur noir en sombre. Le logo garde la même taille et reste centré.
Le bleu principal est toujours `#0097D7` ; les petits textes bleus sont assombris
en clair pour leur contraste.

`theme.js` applique le choix enregistré avant le rendu. La clé locale
`bb16-theme` contient uniquement `light` ou `dark`, sans transmission réseau.
Sans choix enregistré, le site suit la préférence du système, y compris ses
changements. Si le stockage est bloqué, la bascule fonctionne dans la page
courante, mais le choix ne peut pas être conservé après rechargement.
Sans JavaScript, la feuille de style suit le système et le sélecteur est masqué.
Le script et la feuille de style portent une version de contenu pour éviter
de réutiliser une ancienne palette après déploiement.

Consigne utilisée avec l'outil imagegen intégré : retirer le papier blanc du
logo fourni et produire un PNG réellement transparent, préserver la composition,
les textures et les lettres blanches intentionnelles, employer le bleu
`#0097D7`, sans ajout ni cadre, pour affichage sur fond noir. L'original reste
disponible séparément et n'est pas remplacé par cette adaptation.

Elle produit les pages HTML, `sitemap.xml`, `robots.txt` et `404.html`. Les
liens internes sont préfixés par le chemin de base afin de fonctionner depuis
une page 404 imbriquée.

Le site n'embarque aucun code privé d'application, document interne, secret,
fichier Firebase, configuration de paiement ou donnée utilisateur. Les seules
captures d'écran publiées sont celles des pages produit (voir plus bas),
choisies sans adresse email ni donnée de compte visible.

## Pages produit, vidéos et notation Store

`convertair.html`, `doccipher.html` et `hgq.html` sont décrites dans
`product_pages.py` (textes, prix, FAQ, captures, vidéos) : en-tête, visite
guidée où l'écran d'un téléphone générique dessiné en CSS suit le défilement,
cartes dont la vidéo se joue au survol (ou quand elles apparaissent sur un
écran tactile), prix, confidentialité, FAQ et « Notez-nous sur le Store ».
`product.js` pilote l'écran et les vidéos : elles ne sont chargées qu'au moment
de les jouer, et jamais avec `prefers-reduced-motion` (captures fixes).

Les médias viennent de vraies captures lues dans les dépôts des apps
(`SCREENS` dans `product_pages.py`). Pour les refaire, sur la machine source :

```powershell
python .\make_media.py   # Pillow + ffmpeg ; WebP 540 px, MP4 H.264 432 px, sans son
```

Les captures HGQ de développement sont nettoyées des indicateurs de toucher
d'Android ; rien d'autre n'est modifié. La génération normale et la CI n'ont
besoin ni de Pillow ni de ffmpeg : elles vérifient seulement la présence des
fichiers produits.

Les boutons Google Play dépendent de `store_listings` dans
`site.config.json` : tant que `published` vaut `false`, la page affiche
« Bientôt sur Google Play » et aucun lien Store n'est écrit. Passer une app à
`true` après sa publication, puis régénérer. Pas de parrainage ni de
récompense contre un avis : le validateur le refuse.

Le code de panique et le coffre leurre de DocCipher (décision D-0051) ne sont
pas implémentés : ils n'apparaissent que dans le bloc « Bientôt, inclus dans
Premium », avec la formulation bornée de la décision, et le validateur refuse
toute mention hors de ce cadre.

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
