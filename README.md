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

La génération normale utilise uniquement les assets déjà copiés dans ce dépôt. Elle
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
Le logo BB16 est grand et centré sur les pages générales. Sur les trois pages
produit, l'en-tête est compact : logo à gauche, navigation et choix du thème,
puis navigation interne fixe au défilement. Les deux WebP de 256 px dérivés
localement des logos d'origine réduisent leur poids de 1 942 245 à 69 516 octets,
sans modifier les originaux. HGQ utilise son logo sur
l'accueil, le catalogue et sa fiche, sans fond blanc ajouté.

## Apparence claire et sombre

Le sélecteur « Clair / Sombre » dans l'en-tête change la palette de toutes
les pages et affiche le logo adapté : JPG original sur blanc en clair, PNG
transparent sur noir en sombre (WebP locaux optimisés sur les pages produit).
Le logo garde la même taille dans les deux thèmes.
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

Tous les téléphones passent par `phone_frame()` : coque générique de 280 ×
568 px, écran de 264 × 528 px, rayons, bordure, ombre et caméra identiques dans
l'introduction, la visite et les cartes des trois pages. Aucun ratio ni taille
propre à une application ou une section. Les médias restent entiers grâce à
`object-fit: contain`. Sous 360 px, le même repli de 248 × 504 px s'applique
partout. Le téléphone de la visite devient fixe seulement lorsque la fenêtre
est assez large et haute ; sinon les captures restent dans chaque étape.

Les aperçus ont une pause globale et un bouton accessible au clavier par carte.
Une page masquée arrête les vidéos ; un changement de préférence de réduction
des animations les arrête immédiatement. Sans JavaScript, textes, captures,
navigation interne et FAQ restent utilisables.

La preuve visuelle et les interactions se reproduisent avec Playwright installé
localement (aucune dépendance ajoutée au site livré) :

```powershell
# PLAYWRIGHT_MODULE et CHROMIUM_EXECUTABLE peuvent désigner les outils locaux.
node .\scripts\capture_product_ux.cjs before  # avant toute modification
python -B .\build_site.py
python -B .\validate_site.py
node .\scripts\capture_product_ux.cjs after
```

Les captures se trouvent dans `_apercu/before/` et `_apercu/after/`, avec les
mesures JSON et la preuve d'interaction. `_apercu/comparatif-ux.html` permet de
comparer les deux versions à largeur et thème identiques. Ce dossier reste
local, exclu de Git par la règle existante.

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

ConvertAir et DocCipher sont présentés globalement comme « Bientôt sur
Android » tant que leur fiche Google Play n'est pas publiée. Pour DocCipher,
le code de panique et le coffre leurre de la décision D-0051 sont
`IMPLEMENTED_LOCAL_UNVALIDATED` et prévus dès le lancement dans le droit
Premium à vie, sans supplément. Le site borne cette annonce : effacement
logique des seuls coffres locaux choisis, sauvegardes externes conservées,
coffre leurre séparé et public, aucune garantie absolue. Leur disponibilité
publique reste conditionnée aux revues de sécurité et aux essais sur appareil.

La politique DocCipher décrit aussi la demande d'avis par l'API officielle
Google Play après une réussite, jamais au démarrage, pendant un traitement ou
après un échec, avec au moins 90 jours entre deux demandes locales. Google
Play décide si la carte apparaît ; DocCipher ne reçoit ni la note, ni le
commentaire, ni le score.

ConvertAir utilise le même canal Store avec ses propres bornes vérifiées dans
le code : seulement après un résultat réussi affiché, à partir du troisième,
jamais au démarrage, pendant un traitement, après une erreur ou un lot
partiellement réussi, et au plus une tentative tous les 60 jours. Le bouton
manuel des Réglages ouvre séparément la fiche Store.

## Artefact GitHub Pages borné

L'export de publication est produit par un script Python standard-library,
identique sous Windows et Linux :

```powershell
python .\export_site.py --output _site
```

Le script accepte uniquement `_site` comme cible et copie une allowlist exacte
des pages, fichiers racine et assets référencés par les sources de génération.
Les deux WebP de branding font partie de l'artefact. Il refuse les entrées ou
extensions imprévues et les liens locaux cassés (`href`, `src`,
`data-src`, ressources CSS), compare l'arbre produit au manifeste exact et
affiche le nombre de fichiers, le nombre de liens vérifiés et l'empreinte de
l'artefact. Les sources Python, la configuration, les documents de travail et
`_apercu` ne sont pas exportés. Le workflow Pages utilise ce même script.

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
python -m unittest -v .\test_site_gates.py
python .\export_site.py --output _site
```

La validation vérifie les pages attendues, les liens locaux, les assets, les
liens canoniques, les liens depuis une 404 imbriquée, l'absence de secrets
connus, les annonces Coming soon, les formulations bornées PC-2/PC-3 et avis
Google Play, ainsi que l'absence de scroll horizontal dans la feuille de
style. Elle ne publie pas le site et ne remplace ni une revue de sécurité
indépendante, ni un essai Android/Pixel/Play, ni la confirmation des
informations d'identité encore attendues.
