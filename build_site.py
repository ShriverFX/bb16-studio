#!/usr/bin/env python3
"""Build the dependency-free BB16 Studio static site."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import re
from urllib.parse import urlsplit
from pathlib import Path
from html import escape


SITE = Path(__file__).resolve().parent
BB16 = SITE.parents[1]
CONFIG_PATH = SITE / "site.config.json"
CSS_PATH = SITE / "styles.css"

ASSETS = {
    "assets/branding/convertair-presentation.png": BB16 / "10_STUDIO/ConvertAir/assets/branding/convertair_presentation.png",
    "assets/branding/doccipher-presentation.png": BB16 / "10_STUDIO/DocCipher/assets/branding/doccipher_presentation.png",
    "assets/apps/convertair-icon-512.png": BB16 / "10_STUDIO/ConvertAir/assets/store/icon-512.png",
    "assets/apps/doccipher-icon-512.png": BB16 / "10_STUDIO/DocCipher/docs/store/assets/icon-512.png",
    "assets/apps/hgq-logo.png": BB16 / "10_STUDIO/HGQ/hgq/assets/images/Logo_hgq_fond_transparent.png",
    "assets/branding/bb16-studio-logo.jpg": None,  # Original supplied by the owner, versioned here.
    "assets/branding/bb16-studio-logo-dark.png": None,  # Display derivative supplied for the black site background.
}

NAV = [
    ("index.html", "Accueil"),
    ("studio.html", "Studio"),
    ("apps.html", "Apps"),
    ("support.html", "Support"),
]


def read_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def normalise_base(value: str) -> str:
    value = value.strip()
    if not value or value == "/":
        return "/"
    return "/" + value.strip("/") + "/"


def page_url(filename: str, site_url: str | None, base_path: str) -> str | None:
    if not site_url:
        return None
    site_url = site_url.rstrip("/")
    if filename == "index.html":
        return f"{site_url}{base_path}"
    return f"{site_url}{base_path}{filename}"


def validate_site_url(site_url: str | None) -> str | None:
    if not site_url:
        return None
    parsed = urlsplit(site_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("--site-url doit être une origine HTTPS, par exemple https://shriverfx.github.io ; le chemin est fourni par --base-path.")
    return site_url.rstrip("/")


def prefix_internal_links(markup: str, base_path: str) -> str:
    """Prefix local href/src values so GitHub Pages 404s remain navigable."""
    def replace(match: re.Match[str]) -> str:
        attribute, value, closing = match.groups()
        return f'{attribute}{base_path}{value}{closing}'

    pattern = r'((?:href|src)=["\'])(?![A-Za-z][A-Za-z0-9+.-]*:|/|#)([^"\']+)(["\'])'
    return re.sub(pattern, replace, markup)


def header(active: str) -> str:
    links = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == active else ""
        links.append(f'<a href="{href}"{current}>{label}</a>')
    return f'''<a class="skip-link" href="#main">Aller au contenu</a>
<header class="site-header">
  <nav class="nav" aria-label="Navigation principale">
    <a class="wordmark" href="index.html" aria-label="BB16 Studio — Accueil"><img class="wordmark-logo logo-dark" src="assets/branding/bb16-studio-logo-dark.png" alt="" width="1254" height="1254"><img class="wordmark-logo logo-light" src="assets/branding/bb16-studio-logo.jpg" alt="" width="1280" height="1280"></a>
    <div class="nav-links">{"".join(links)}</div>
    <div class="theme-switch" role="group" aria-label="Apparence" hidden><button class="theme-option" type="button" data-set-theme="light" aria-pressed="false">Clair</button><button class="theme-option" type="button" data-set-theme="dark" aria-pressed="false">Sombre</button></div>
  </nav>
</header>'''


def footer() -> str:
    return '''<footer class="footer"><div class="container footer-grid">
  <span>© 2026 BB16 Studio · projets numériques indépendants</span>
  <span class="footer-links"><a href="privacy.html">Confidentialité</a><a href="legal.html">Mentions légales</a><a href="contact.html">Contact</a></span>
</div></footer>'''


def document(title: str, description: str, active: str, body: str, config: dict, filename: str) -> str:
    site_url = config.get("site_url")
    base_path = normalise_base(config.get("base_path", "/"))
    canonical = page_url(filename, site_url, base_path)
    canonical_tag = f'<link rel="canonical" href="{escape(canonical)}">' if canonical else ""
    og_url = f'<meta property="og:url" content="{escape(canonical)}">' if canonical else ""
    og_asset = {"convertair.html": "assets/branding/convertair-presentation.png", "doccipher.html": "assets/branding/doccipher-presentation.png", "hgq.html": "assets/apps/hgq-logo.png"}.get(filename, "assets/branding/bb16-studio-logo-dark.png")
    og_image = page_url(og_asset, site_url, base_path)
    og_image_tag = f'<meta property="og:image" content="{escape(og_image)}">' if og_image else ""
    email = escape(config["contact_email"])
    asset_version = hashlib.sha256(CSS_PATH.read_bytes() + (SITE / "theme.js").read_bytes()).hexdigest()[:12]
    raw = f'''<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#0097D7">
  <meta name="description" content="{escape(description)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="BB16 Studio">
  <meta property="og:title" content="{escape(title)} · BB16 Studio">
  <meta property="og:description" content="{escape(description)}">
  {og_url}{og_image_tag}{canonical_tag}
  <link id="site-icon" rel="icon" type="image/png" href="assets/branding/bb16-studio-logo-dark.png" data-dark="{base_path}assets/branding/bb16-studio-logo-dark.png" data-light="{base_path}assets/branding/bb16-studio-logo.jpg">
  <script src="theme.js?v={asset_version}"></script>
  <link rel="stylesheet" href="styles.css?v={asset_version}">
  <title>{escape(title)} · BB16 Studio</title>
</head>
<body>
  {header(active)}
  <main id="main">{body}</main>
  {footer()}
</body>
</html>
'''
    return prefix_internal_links(raw, base_path)


def product_page(kind: str, config: dict) -> tuple[str, str]:
    if kind == "convertair":
        title = "ConvertAir"
        description = "Outils documentaires sur appareil, avec un parcours Android en préparation."
        body = '''<section class="section"><div class="container product-layout">
  <div class="prose"><p class="eyebrow">Application documentaire</p><h1>ConvertAir</h1>
    <p class="lede">ConvertAir rassemble des outils de conversion, de création et de manipulation de documents directement sur l'appareil.</p>
    <p><span class="status pending">Android V1 en préparation</span></p>
    <h2>Une approche locale pour les documents</h2>
    <p>Le projet vise les parcours de scan, conversion PDF et image, assemblage, compression, annotation, signature, OCR et gestion de fichiers locaux. Les documents sont traités sur le téléphone selon le périmètre courant du projet.</p>
    <p>La connexion nécessaire aux achats reste distincte du traitement documentaire. ConvertAir est en préparation pour Android.</p>
    <p>La <a href="convertair-privacy.html">politique de confidentialité de ConvertAir</a> décrit le périmètre réel de l'application : traitement sur l'appareil, réseau limité aux achats, permissions déclarées.</p>
    <div class="actions"><a class="button secondary" href="convertair-privacy.html">Confidentialité ConvertAir</a><a class="button" href="contact.html">Contacter BB16 Studio</a></div>
  </div>
  <aside class="aside"><img class="poster" src="assets/branding/convertair-presentation.png" alt="Affiche de présentation ConvertAir montrant un document et des flèches de conversion"><dl class="facts"><div class="fact"><dt>Plateforme</dt><dd>Bientôt sur Android</dd></div><div class="fact"><dt>iOS</dt><dd>À l'étude</dd></div><div class="fact"><dt>Téléchargement</dt><dd>Disponible prochainement</dd></div></dl></aside>
</div></section>'''
    else:
        title = "DocCipher"
        description = "Coffre documentaire local-first chiffré, en développement pour Android."
        body = '''<section class="section"><div class="container product-layout">
  <div class="prose"><p class="eyebrow">Coffre documentaire</p><h1>DocCipher</h1>
    <p class="lede">DocCipher explore un coffre documentaire local-first : vos papiers, votre clé et une sauvegarde que vous choisissez.</p>
    <p><span class="status pending">Android en développement</span></p>
    <h2>Chiffrement local et sauvegarde exportable</h2>
    <p>Le projet travaille sur un format de coffre chiffré, des opérations locales et l'export ou l'import manuel d'une sauvegarde <code>.dcvault</code> via le sélecteur de fichiers. WebDAV et Nextcloud restent planifiés et ne sont pas disponibles dans l'application actuelle. DocCipher ne repose pas sur un backend documentaire BB16.</p>
    <p>DocCipher est en développement pour Android. Le produit vise la conservation et l'export de documents avec un traitement local-first.</p>
    <p>La <a href="doccipher-privacy.html">politique de confidentialité de DocCipher</a> décrit le chiffrement local, les exports choisis par l'utilisateur et la connexion limitée aux achats.</p>
    <div class="actions"><a class="button secondary" href="doccipher-privacy.html">Confidentialité DocCipher</a><a class="button" href="contact.html">Contacter BB16 Studio</a></div>
  </div>
  <aside class="aside"><img class="poster" src="assets/branding/doccipher-presentation.png" alt="Affiche de présentation DocCipher avec un coffre documentaire stylisé"><dl class="facts"><div class="fact"><dt>Plateforme</dt><dd>En développement pour Android</dd></div><div class="fact"><dt>iOS</dt><dd>À l'étude</dd></div><div class="fact"><dt>Téléchargement</dt><dd>Disponible prochainement</dd></div></dl></aside>
</div></section>'''
    return title, document(title, description, f"{kind}.html", body, config, f"{kind}.html")


def convertair_privacy_body(email: str) -> str:
    """Politique de confidentialité ConvertAir, bilingue sur une seule URL.

    POURQUOI UNE SEULE PAGE POUR DEUX LANGUES — le site est monolingue : le
    gabarit force `<html lang="fr">` et il n'existe aucun mécanisme de locale.
    Or l'application est distribuée dans vingt langues et sa fiche Play est
    relue en anglais. Une deuxième URL aurait obligé l'application à choisir
    laquelle ouvrir, donc à porter deux constantes au lieu d'une. Le français
    reste la langue du document ; la partie anglaise est balisée `lang="en"`
    pour les lecteurs d'écran et les moteurs.

    POURQUOI CE TEXTE EST COURT — chaque phrase ci-dessous est adossée à une
    lecture du code de ConvertAir (manifeste release et test
    `expected_permissions_test.dart`, wrapper RevenueCat, règles de sauvegarde,
    dépendances de `pubspec.yaml`). Les clauses usuelles qu'on ne pouvait pas
    prouver dans le code — durées de conservation côté serveur, base légale,
    sous-traitants, transferts hors UE — ne sont pas écrites du tout plutôt
    qu'écrites au conditionnel.
    """
    return f'''<section class="section"><div class="container prose">
<p class="eyebrow">ConvertAir · application mobile</p>
<h1>Politique de confidentialité</h1>
<p class="lede">ConvertAir traite vos documents sur votre appareil. Cette page décrit ce que l'application fait réellement, et ce qu'elle ne fait pas.</p>
<p class="meta">Dernière mise à jour : 21 septembre 2026 · <a href="#english">Read this page in English</a></p>

<h2>Vos documents restent sur votre appareil</h2>
<p>La numérisation, les conversions, l'assemblage, la compression, l'annotation, la signature et la reconnaissance de texte (OCR) s'exécutent sur votre téléphone. Aucun document, aucune image et aucun texte reconnu n'est transmis à BB16 Studio ni à un tiers.</p>
<p>La reconnaissance de texte utilise des modèles embarqués dans l'application : elle a lieu sur l'appareil, et ConvertAir n'envoie aucune image à un serveur pour cela. La capture de documents est déléguée aux services Google Play installés sur votre téléphone ; ConvertAir ne transmet lui-même aucun document, mais ce traitement se déroule dans un composant Google, régi par la politique de confidentialité de Google et non par la nôtre.</p>

<h2>La seule connexion réseau de l'application</h2>
<p>ConvertAir ouvre une connexion réseau pour une seule raison : les achats. Cela couvre l'affichage des offres, l'achat et la restauration d'un achat. La licence est gérée par RevenueCat ; le paiement lui-même est réalisé par Google Play ou l'App Store. Aucun contenu de document ne passe par ce chemin.</p>
<p>Le client RevenueCat est configuré en mode anonyme : aucun compte n'est créé, la collecte automatique d'identifiants d'appareil est désactivée, les diagnostics du SDK sont désactivés. L'identifiant utilisé est un identifiant anonyme produit par le SDK et rattaché à l'installation, pas à vous.</p>
<p>Si aucune clé d'achat n'est configurée, l'application n'ouvre aucune connexion et reste gratuite.</p>

<h2>Ce que l'application ne fait pas</h2>
<ul>
<li>Aucun compte, aucune inscription, aucune adresse email demandée.</li>
<li>Aucun outil de mesure d'audience, de statistiques d'usage ou de rapport de plantage.</li>
<li>Aucun identifiant publicitaire : la permission <code>com.google.android.gms.permission.AD_ID</code> n'est pas déclarée.</li>
<li>Aucune publicité, aucune vente de données, aucun partage à des fins commerciales.</li>
<li>Aucun suivi d'une application à l'autre ni d'un site à l'autre.</li>
</ul>

<h2>Permissions Android</h2>
<p>Le manifeste de la version publiée déclare exactement trois entrées :</p>
<ul>
<li><code>android.permission.INTERNET</code> — les achats, et rien d'autre ;</li>
<li><code>com.android.vending.BILLING</code> — la facturation Google Play ;</li>
<li>une permission de signature interne à l'application, qui n'ouvre aucune capacité de l'appareil.</li>
</ul>
<p>Aucune permission de caméra, de localisation, de contacts, de microphone ou de stockage étendu n'est demandée. Les fichiers que vous ouvrez le sont par le sélecteur de fichiers du système ou par un partage entrant : l'application en reçoit un accès temporaire, le temps d'en faire une copie locale.</p>

<h2>Sauvegarde et transfert d'appareil</h2>
<p>La sauvegarde automatique d'Android est désactivée et les règles d'extraction excluent explicitement la sauvegarde vers le cloud et le transfert d'un appareil à l'autre. Les données de l'application ne sont donc pas téléversées vers un espace Google Drive ni recopiées vers un nouveau téléphone par ces canaux.</p>

<h2>Ce qui est conservé sur votre appareil</h2>
<p>Les fichiers que vous produisez, un historique local des opérations, vos préférences d'affichage et vos signatures enregistrées. Les images de signature sont chiffrées sur l'appareil. L'historique peut être purgé automatiquement au bout de 30 jours, de 90 jours, ou conservé, selon le réglage que vous choisissez dans l'écran Réglages. Désinstaller l'application supprime les données de son répertoire privé.</p>
<p>Lorsque des polices supplémentaires sont nécessaires pour les écritures non latines, elles sont distribuées par le mécanisme de modules à la demande de Google Play. ConvertAir n'ouvre pas de connexion pour les récupérer.</p>

<h2>Vos droits</h2>
<p>BB16 Studio ne détient aucun fichier ni aucune donnée personnelle vous concernant au titre de ConvertAir : il n'y a rien, de notre côté, à exporter ou à supprimer. Vos données d'achat sont détenues par Google Play ou l'App Store et par RevenueCat, chacun selon sa propre politique. Pour toute question, écrivez à <a href="mailto:{email}">{email}</a>.</p>

<h2>Modifications</h2>
<p>Si le comportement de l'application change, cette page est mise à jour avec lui et la date ci-dessus change.</p>

<hr>

<div lang="en">
<h2 id="english">English version</h2>
<p class="lede">ConvertAir processes your documents on your device. This page describes what the app actually does, and what it does not do.</p>
<p class="meta">Last updated: 21 September 2026 · <a href="#main">Lire cette page en français</a></p>

<h3>Your documents stay on your device</h3>
<p>Scanning, conversions, merging, compression, annotation, signing and text recognition (OCR) all run on your phone. No document, no image and no recognised text is sent to BB16 Studio or to any third party.</p>
<p>Text recognition uses models bundled inside the app: it runs on the device, and ConvertAir sends no image to any server for it. Document capture is delegated to the Google Play services installed on your phone; ConvertAir itself transmits no document, but that step runs inside a Google component, governed by Google's privacy policy rather than ours.</p>

<h3>The app's only network connection</h3>
<p>ConvertAir opens a network connection for one reason: purchases. That covers showing the offers, buying, and restoring a purchase. Entitlements are handled by RevenueCat; the payment itself is carried out by Google Play or the App Store. No document content travels over that path.</p>
<p>The RevenueCat client runs in anonymous mode: no account is created, automatic device-identifier collection is turned off, and SDK diagnostics are turned off. The identifier used is an anonymous one generated by the SDK and tied to the installation, not to you.</p>
<p>If no purchase key is configured, the app opens no connection at all and stays free.</p>

<h3>What the app does not do</h3>
<ul>
<li>No account, no sign-up, no email address requested.</li>
<li>No analytics, usage measurement or crash-reporting tool.</li>
<li>No advertising identifier: the <code>com.google.android.gms.permission.AD_ID</code> permission is not declared.</li>
<li>No advertising, no sale of data, no sharing for commercial purposes.</li>
<li>No tracking across apps or across websites.</li>
</ul>

<h3>Android permissions</h3>
<p>The published build's manifest declares exactly three entries:</p>
<ul>
<li><code>android.permission.INTERNET</code> — purchases, and nothing else;</li>
<li><code>com.android.vending.BILLING</code> — Google Play billing;</li>
<li>an app-internal signature permission, which grants no device capability.</li>
</ul>
<p>No camera, location, contacts, microphone or broad storage permission is requested. Files you open come through the system file picker or through an incoming share: the app receives temporary access, just long enough to make a local copy.</p>

<h3>Backup and device transfer</h3>
<p>Android's automatic backup is disabled, and the data-extraction rules explicitly exclude both cloud backup and device-to-device transfer. The app's data is therefore not uploaded to a Google Drive space, nor copied to a new phone through those channels.</p>

<h3>What is kept on your device</h3>
<p>The files you produce, a local history of operations, your display preferences and your saved signatures. Signature images are encrypted on the device. History can be purged automatically after 30 days, after 90 days, or kept, depending on the setting you choose in the Settings screen. Uninstalling the app removes the data in its private directory.</p>
<p>Font packs for non-Latin scripts are downloaded by the Play Store itself, outside the app.</p>

<h3>Your rights</h3>
<p>BB16 Studio holds no file and no personal data about you in connection with ConvertAir: there is nothing on our side to export or delete. Your purchase data is held by Google Play or the App Store and by RevenueCat, each under its own policy. For any question, write to <a href="mailto:{email}">{email}</a>.</p>

<h3>Changes</h3>
<p>If the app's behaviour changes, this page changes with it and the date above is updated.</p>
</div>

<div class="actions"><a class="button secondary" href="convertair.html">Retour à ConvertAir</a><a class="button" href="contact.html">Nous écrire</a></div>
</div></section>'''


def doccipher_privacy_body(email: str) -> str:
    """Politique de confidentialité DocCipher, français et anglais."""
    return f'''<section class="section"><div class="container prose">
<p class="eyebrow">DocCipher · application mobile</p>
<h1 id="main">Politique de confidentialité</h1>
<p class="lede">DocCipher conserve vos documents dans un coffre chiffré sur votre appareil. Il n'existe ni compte DocCipher ni serveur documentaire BB16 Studio.</p>
<p class="meta">Dernière mise à jour : 22 septembre 2026 · <a href="#english">Read this page in English</a></p>

<h2>Documents et chiffrement local</h2>
<p>Les documents importés ou numérisés, leurs aperçus, le texte reconnu par OCR, les dossiers, les tags et les données du coffre restent dans l'espace privé de l'application. Le coffre est chiffré sur l'appareil. BB16 Studio ne reçoit ni vos documents, ni leur contenu, ni votre mot de passe, ni votre matériel de récupération.</p>
<p>La reconnaissance de texte utilise des modèles embarqués et s'exécute sur l'appareil. La capture est déléguée au scanner de documents fourni par les services Google Play installés sur le téléphone : DocCipher ne transmet lui-même aucun document, mais cette étape s'exécute dans un composant Google régi par les règles de Google.</p>

<h2>Exports et sauvegardes que vous choisissez</h2>
<p>Un document ou une sauvegarde <code>.dcvault</code> ne quitte l'application que lorsque vous déclenchez explicitement un export et choisissez sa destination avec le sélecteur ou la feuille de partage du système. Une sauvegarde <code>.dcvault</code> reste chiffrée ; un document exporté en clair ne l'est plus et relève alors de la sécurité de la destination choisie.</p>
<p>La sauvegarde automatique Android et le transfert automatique vers un nouvel appareil sont désactivés. La synchronisation WebDAV ou Nextcloud n'est pas disponible dans la version actuelle.</p>

<h2>Achats facultatifs</h2>
<p>La connexion réseau de l'application sert aux achats, à leur restauration et à l'affichage des offres. Google Play traite le paiement ; lorsque RevenueCat est configuré dans la version distribuée, ce service traite le reçu, le produit acheté et l'état du droit Premium. Aucun contenu de document ne passe par ce chemin.</p>
<p>RevenueCat est configuré sans compte DocCipher, avec un identifiant anonyme généré par le SDK ; la collecte automatique d'identifiants d'appareil et les diagnostics du SDK sont désactivés. Sans clé d'achat configurée, l'application reste en mode gratuit et ne configure pas RevenueCat.</p>

<h2>Ce que DocCipher ne fait pas</h2>
<ul>
<li>Aucun compte utilisateur DocCipher et aucune adresse email demandée.</li>
<li>Aucune publicité, aucun identifiant publicitaire et aucune vente de données.</li>
<li>Aucun outil d'analytics, de suivi d'usage ou de rapport de plantage.</li>
<li>Aucun serveur BB16 Studio qui héberge, analyse ou sauvegarde vos documents.</li>
</ul>

<h2>Permissions Android</h2>
<p>La version Android demande l'accès Internet pour les achats et inclut la permission de facturation Google Play. Une permission interne de niveau signature est générée pour des composants privés de l'application. Elle ne demande aucune permission de caméra, localisation, contacts, microphone ou stockage étendu : les fichiers passent par les sélecteurs du système et la capture par le composant Google Play Services.</p>

<h2>Suppression et demandes</h2>
<p>Vous pouvez supprimer les données locales en supprimant le coffre ou en désinstallant l'application. Une copie que vous avez exportée reste à l'emplacement que vous avez choisi jusqu'à ce que vous l'y supprimiez. Les données d'achat éventuelles sont conservées par Google Play et RevenueCat selon leurs propres politiques.</p>
<p>BB16 Studio ne peut pas extraire, déchiffrer ou restaurer votre coffre à distance. Pour une question de confidentialité ou une demande concernant un identifiant d'achat anonyme, écrivez à <a href="mailto:{email}">{email}</a> sans joindre de document, de mot de passe, de clé ou de phrase de récupération.</p>

<h2>Modifications</h2>
<p>Cette page sera mise à jour si les flux de données, les services tiers ou les permissions de l'application changent.</p>

<hr>

<div lang="en">
<h2 id="english">English version</h2>
<p class="lede">DocCipher keeps your documents in an encrypted vault on your device. There is no DocCipher account and no BB16 Studio document server.</p>
<p class="meta">Last updated: 22 September 2026 · <a href="#main">Lire cette page en français</a></p>

<h3>Documents and local encryption</h3>
<p>Imported or scanned documents, previews, recognised text, folders, tags and vault data remain in the app's private storage. The vault is encrypted on the device. BB16 Studio receives neither your documents nor their content, your password or your recovery material.</p>
<p>Text recognition uses bundled models and runs on the device. Capture is delegated to the document scanner supplied by Google Play services on the phone: DocCipher itself sends no document, but this step runs in a Google component governed by Google's rules.</p>

<h3>Exports and backups you choose</h3>
<p>A document or <code>.dcvault</code> backup leaves the app only when you explicitly start an export and choose its destination through the system picker or share sheet. A <code>.dcvault</code> backup remains encrypted; a document exported in clear form is no longer encrypted and then depends on the security of your chosen destination.</p>
<p>Android automatic backup and automatic device-to-device transfer are disabled. WebDAV or Nextcloud synchronisation is not available in the current version.</p>

<h3>Optional purchases</h3>
<p>The app's network connection is used for purchases, purchase restoration and showing offers. Google Play processes the payment; when RevenueCat is configured in the distributed build, it processes the receipt, purchased product and Premium entitlement status. No document content travels over this path.</p>
<p>RevenueCat is configured without a DocCipher account, using an anonymous identifier generated by the SDK; automatic device-identifier collection and SDK diagnostics are disabled. Without a configured purchase key, the app stays in free mode and does not configure RevenueCat.</p>

<h3>What DocCipher does not do</h3>
<ul>
<li>No DocCipher user account and no email address requested.</li>
<li>No advertising, advertising identifier or sale of data.</li>
<li>No analytics, usage tracking or crash-reporting tool.</li>
<li>No BB16 Studio server that hosts, analyses or backs up your documents.</li>
</ul>

<h3>Android permissions</h3>
<p>The Android version requests Internet access for purchases and includes the Google Play billing permission. A signature-level internal permission is generated for private app components. It requests no camera, location, contacts, microphone or broad-storage permission: files use system pickers and capture uses the Google Play services component.</p>

<h3>Deletion and requests</h3>
<p>You can remove local data by deleting the vault or uninstalling the app. A copy you exported remains at the destination you chose until you delete it there. Any purchase data is retained by Google Play and RevenueCat under their own policies.</p>
<p>BB16 Studio cannot remotely extract, decrypt or restore your vault. For a privacy question or a request about an anonymous purchase identifier, write to <a href="mailto:{email}">{email}</a> without attaching a document, password, key or recovery phrase.</p>

<h3>Changes</h3>
<p>This page will be updated if the app's data flows, third-party services or permissions change.</p>
</div>

<div class="actions"><a class="button secondary" href="doccipher.html">Retour à DocCipher</a><a class="button" href="contact.html">Nous écrire</a></div>
</div></section>'''


def pages(config: dict) -> dict[str, str]:
    email = escape(config["contact_email"])
    return {
        "index.html": document("Accueil", "BB16 Studio crée des applications sobres, locales et utiles.", "index.html", f'''<section class="hero"><div class="container hero-copy"><h1>Des outils qui respectent votre attention.</h1><p class="lede">Nous concevons des expériences utiles autour des documents, de la confidentialité et du jeu compétitif. Chaque projet avance avec des limites explicites.</p><div class="actions"><a class="button" href="apps.html">Découvrir les apps</a><a class="button secondary" href="studio.html">Notre approche</a></div></div></section>
<section class="section alt"><div class="container"><div class="section-head"><div><p class="eyebrow">Projets en cours</p><h2>Trois produits, trois usages.</h2></div><p>Les pages produit présentent les applications et leur état de préparation.</p></div><div class="grid"><article class="card icon-card"><img class="app-icon" src="assets/apps/convertair-icon-512.png" alt="Icône ConvertAir"><div><h3>ConvertAir</h3><p>Outils documentaires sur appareil, avec une V1 Android en préparation.</p><p class="meta">Bientôt sur Android</p></div></article><article class="card icon-card"><img class="app-icon" src="assets/apps/doccipher-icon-512.png" alt="Icône DocCipher"><div><h3>DocCipher</h3><p>Coffre documentaire local-first chiffré, en développement.</p><p class="meta">En développement pour Android</p></div></article><article class="card icon-card"><img class="app-icon hgq-icon" src="assets/apps/hgq-logo.png" alt="Logo HGQ" width="709" height="784"><div><h3>HGQ</h3><p>Quiz multijoueur en temps réel autour de la culture jeu vidéo, avec comptes, amis et classements.</p><p class="meta">Bientôt sur Android</p></div></article></div></div></section>
<section class="section"><div class="container"><div class="section-head"><div><p class="eyebrow">Écrire à l'équipe</p><h2>Une question sur un projet ?</h2></div><p>Le support public passe par une adresse unique. N'envoyez jamais de mot de passe, clé privée ou document sensible par email.</p></div><a class="email-box" href="mailto:{email}">{email}</a></div></section>''', config, "index.html"),
        "studio.html": document("BB16 Studio", "L'approche BB16 Studio : produits locaux, privacy claire et décisions vérifiables.", "studio.html", '''<section class="section"><div class="container prose"><p class="eyebrow">L'atelier</p><h1>Le studio</h1><p class="lede">Un studio indépendant qui préfère les produits lisibles aux promesses bruyantes.</p><h2>Construire avec des limites claires</h2><p>Nous travaillons sur des applications où la confiance compte : documents personnels, données de compte, parties compétitives. Les fonctions sont décrites selon leur état réel.</p><div class="grid"><article class="card"><h3>Local d'abord</h3><p>Quand le produit le permet, les opérations sensibles restent sur l'appareil. Les connexions nécessaires sont isolées et expliquées.</p></article><article class="card"><h3>Privacy compréhensible</h3><p>Les pages de confidentialité distinguent le site, l'application et les services tiers. Aucune télémétrie marketing n'est ajoutée à ce site.</p></article><article class="card"><h3>Une mise en route progressive</h3><p>Chaque application est présentée avec son périmètre actuel et son prochain jalon.</p></article></div><div class="actions"><a class="button" href="apps.html">Voir les applications</a><a class="button secondary" href="contact.html">Nous contacter</a></div></div></section>''', config, "studio.html"),
        "apps.html": document("Applications", "Découvrez les projets applicatifs de BB16 Studio.", "apps.html", '''<section class="section"><div class="container"><p class="eyebrow">Catalogue</p><h1>Nos applications</h1><p class="lede">Chaque fiche indique le rôle du produit et son état de préparation.</p><div class="grid"><article class="card"><div class="icon-card"><img class="app-icon" src="assets/apps/convertair-icon-512.png" alt="Icône ConvertAir"><div><h2>ConvertAir</h2><p>Outils documentaires et PDF sur appareil.</p></div></div><p style="margin-top:1rem">Scanner, convertir, organiser et travailler sur des documents dans le périmètre Android V1.</p><p class="meta">Bientôt sur Android</p><div class="actions"><a class="button secondary" href="convertair.html">Lire la fiche</a></div></article><article class="card"><div class="icon-card"><img class="app-icon" src="assets/apps/doccipher-icon-512.png" alt="Icône DocCipher"><div><h2>DocCipher</h2><p>Coffre documentaire local-first.</p></div></div><p style="margin-top:1rem">Chiffrer, conserver et exporter des documents selon le format et les limites du projet.</p><p class="meta">En développement pour Android</p><div class="actions"><a class="button secondary" href="doccipher.html">Lire la fiche</a></div></article><article class="card"><div class="icon-card"><img class="app-icon hgq-icon" src="assets/apps/hgq-logo.png" alt="Logo HGQ" width="709" height="784"><div><h2>HGQ</h2><p>Quiz multijoueur temps réel.</p></div></div><p style="margin-top:1rem">Défier d'autres joueurs, progresser et jouer dans un environnement connecté.</p><p class="meta">Bientôt sur Android</p><div class="actions"><a class="button secondary" href="hgq.html">Lire la fiche</a></div></article></div></div></section>''', config, "apps.html"),
        "convertair.html": product_page("convertair", config)[1],
        "doccipher.html": product_page("doccipher", config)[1],
        "hgq.html": document("HGQ", "Hard Gamer Quiz, quiz multijoueur temps réel édité par BB16 Studio.", "apps.html", '''<section class="section"><div class="container product-layout"><div class="prose"><p class="eyebrow">Jeu compétitif</p><h1>HGQ</h1><p class="lede">Hard Gamer Quiz est un quiz multijoueur temps réel autour de la culture jeu vidéo.</p><p><span class="status pending">Bientôt sur Android</span></p><h2>Jouer, progresser, défier</h2><p>Le projet comprend des comptes, des parties en temps réel, le mode solo, des amis, des profils, des résultats et des classements. Les parties classées sont validées côté serveur selon les règles du projet.</p><p>Les services de compte et de jeu appartiennent à l'application HGQ. La page de confidentialité de l'application reste la référence pour ses données et services.</p><h2>Données et suppression de compte</h2><p>La politique opérationnelle de l'application décrit les comptes, statistiques de jeu, données sociales et services tiers utilisés par HGQ. La suppression peut être demandée depuis le parcours de compte de l'application.</p><div class="actions"><a class="button" href="data-deletion.html">Suppression de compte</a><a class="button secondary" href="privacy.html">Privacy du site</a></div></div><aside class="aside"><img class="poster hgq-poster" src="assets/apps/hgq-logo.png" alt="Logo Hard Gamer Quiz : lettres HGQ et manette bleue" width="709" height="784"><div class="card"><h3>Disponibilité</h3><p>La fiche Android sera ajoutée lorsqu'elle sera publique.</p></div><div class="card" style="margin-top:1rem"><h3>Support</h3><p><a href="mailto:bb16studio@gmail.com">bb16studio@gmail.com</a></p></div></aside></div></section>''', config, "hgq.html"),
        "support.html": document("Support", "Contacter le support public de BB16 Studio.", "support.html", f'''<section class="section"><div class="container prose"><p class="eyebrow">Aide et retours</p><h1>Support</h1><p class="lede">Une adresse publique pour les questions produit, les problèmes d'accès et les demandes liées aux données.</p><a class="email-box" href="mailto:{email}">{email}</a><h2>Pour obtenir une réponse utile</h2><ul><li>Indiquez l'application concernée : ConvertAir, DocCipher ou HGQ.</li><li>Décrivez le comportement observé et l'appareil ou la version si vous les connaissez.</li><li>Ne joignez jamais de mot de passe, clé privée, phrase de récupération, fichier de coffre ou document personnel.</li></ul><div class="callout"><p>Pour une suppression HGQ, utilisez d'abord le parcours dans l'application. Si vous avez perdu l'accès, la <a href="data-deletion.html">page de suppression</a> explique les informations minimales à fournir.</p></div><h2>Retour produit</h2><p>Les idées et signalements sont lus selon les capacités de l'équipe et l'état du projet. Un message reçu ne vaut pas promesse de fonctionnalité, de délai ou de publication.</p></div></section>''', config, "support.html"),
        "contact.html": document("Contact", "Coordonnées publiques de BB16 Studio.", "contact.html", f'''<section class="section"><div class="container prose"><p class="eyebrow">Parlons du produit</p><h1>Contact</h1><p class="lede">Pour une question générale, un retour utilisateur ou un sujet de confidentialité :</p><p><a class="email-box" href="mailto:{email}">{email}</a></p><h2>Quel message envoyer ?</h2><p>Un sujet précis, le nom du produit et les étapes reproductibles nous aideront à vous répondre. Pour la sécurité, restez descriptif et ne transmettez aucune donnée secrète.</p><h2>Identité légale</h2><p>Les informations légales publiques de l'éditeur seront ajoutées après validation par le propriétaire. Cette page affiche uniquement une adresse de contact confirmée ; elle ne constitue pas une identité légale complète.</p></div></section>''', config, "contact.html"),
        "privacy.html": document("Confidentialité", "Politique de confidentialité du site statique BB16 Studio.", "privacy.html", f'''<section class="section"><div class="container prose"><p class="eyebrow">Site web</p><h1>Confidentialité</h1><p class="lede">Ce site est un site statique de présentation. Il est conçu pour fonctionner sans compte et sans outil d'analyse marketing.</p><h2>Données du site</h2><p>BB16 Studio ne place pas de cookie analytique, de pixel publicitaire, de SDK de suivi ou de formulaire qui collecterait des données sur cette version du site. Le choix du mode clair ou sombre est mémorisé uniquement dans le navigateur, sans transmission à BB16 Studio. Un hébergeur peut traiter les journaux techniques nécessaires à la distribution HTTPS ; ces journaux relèvent de son propre fonctionnement et de ses règles publiques.</p><h2>Contact</h2><p>Si vous écrivez à <a href="mailto:{email}">{email}</a>, l'équipe reçoit les informations que vous choisissez d'inclure pour répondre à votre message. N'envoyez pas de secret ou de document sensible.</p><h2>Applications</h2><p>Cette page concerne le site BB16 Studio. Les applications ont leurs propres données, services tiers et parcours de suppression. Pour ConvertAir, consultez la <a href="convertair-privacy.html">confidentialité ConvertAir</a> ; pour DocCipher, la <a href="doccipher-privacy.html">confidentialité DocCipher</a>. Pour HGQ, la politique publiée par l'application est disponible sur <a href="https://hgq-prod.web.app/privacy" rel="noopener">hgq-prod.web.app/privacy</a>.</p><p>La <a href="data-deletion.html">page de suppression HGQ</a> du site reprend le parcours utilisateur connu et le canal de contact actuel.</p><h2>Mise à jour</h2><p>Cette page sera mise à jour lorsque l'identité légale, l'hébergement final ou les services du site changeront.</p></div></section>''', config, "privacy.html"),
        "convertair-privacy.html": document("Politique de confidentialité ConvertAir", "Politique de confidentialité de l'application ConvertAir : traitement local des documents, réseau limité aux achats.", "apps.html", convertair_privacy_body(email), config, "convertair-privacy.html"),
        "doccipher-privacy.html": document("Politique de confidentialité DocCipher", "Politique de confidentialité de DocCipher : coffre chiffré local, exports choisis et réseau limité aux achats.", "apps.html", doccipher_privacy_body(email), config, "doccipher-privacy.html"),
        "legal.html": document("Mentions légales", "Informations légales publiques de BB16 Studio, en attente des données validées.", "legal.html", '''<section class="section"><div class="container prose"><p class="eyebrow">Informations légales</p><h1>Mentions légales</h1><p class="lede">Ce site présente les applications et les projets de BB16 Studio.</p><div class="callout legal-missing"><p>Les informations d'identification juridique et l'adresse publique de l'éditeur sont en cours de mise à jour.</p></div><h2>Éditeur</h2><p>Éditeur : BB16 Studio — identité légale à confirmer par le propriétaire.</p><p>Contact public : <a href="contact.html">bb16studio@gmail.com</a>.</p><h2>Propriété des contenus</h2><p>Les textes et visuels de ce site sont présentés sous réserve des droits de leurs titulaires. Les affiches ConvertAir et DocCipher sont les visuels fournis pour la présentation de leurs projets. Le logo BB16 Studio est fourni par le studio ; le logo HGQ provient des ressources de l'application.</p><h2>Préparation</h2><p>Les informations d'identité seront complétées lorsque le propriétaire les aura confirmées.</p></div></section>''', config, "legal.html"),
        "data-deletion.html": document("Suppression de compte", "Parcours de suppression de compte HGQ et informations à fournir au support.", "support.html", f'''<section class="section"><div class="container prose"><p class="eyebrow">HGQ · compte</p><h1>Suppression de compte</h1><p class="lede">Le parcours recommandé pour supprimer un compte Hard Gamer Quiz passe par l'application.</p><h2>Depuis l'application</h2><ol><li>Ouvrez HGQ et connectez-vous.</li><li>Ouvrez <strong>Paramètres</strong>.</li><li>Dans la section <strong>Mon compte</strong>, choisissez <strong>Supprimer mon compte</strong>.</li><li>Confirmez la suppression.</li></ol><p>Le projet décrit ce parcours comme une suppression en cascade des données de compte et de jeu. Les délais et éventuelles obligations de conservation doivent suivre la politique de l'application en vigueur.</p><h2>Si vous n'avez plus accès à l'application</h2><p>Écrivez à <a href="mailto:{email}">{email}</a> avec le nom de l'application et l'adresse email associée au compte. N'envoyez pas de mot de passe, code de connexion ou pièce d'identité par email sans demande explicite et vérifiée.</p><h2>Informations concernées</h2><p>Selon la politique HGQ publiée par l'application, le compte peut inclure une adresse email, un pseudo, des statistiques de jeu, des données sociales, des préférences, des identifiants techniques et des éléments d'économie du jeu. La politique applicative reste la référence pour les services tiers et les obligations de conservation.</p><div class="callout"><p>Cette page décrit le point d'entrée utilisateur et le canal de contact actuel.</p></div></div></section>''', config, "data-deletion.html"),
        "404.html": document("Page introuvable", "La page demandée n'existe pas sur le site BB16 Studio.", "", '''<section class="section"><div class="container prose"><p class="eyebrow">404</p><h1>Cette page n'existe pas.</h1><p class="lede">Le lien est peut-être ancien ou incomplet.</p><div class="actions"><a class="button" href="index.html">Retour à l'accueil</a><a class="button secondary" href="contact.html">Signaler un lien</a></div></div></section>''', config, "404.html"),
    }


def write_support_files(config: dict, base_path: str) -> None:
    site_url = config.get("site_url")
    urls = [page_url(name, site_url, base_path) for name in ["index.html", "studio.html", "apps.html", "convertair.html", "convertair-privacy.html", "doccipher.html", "doccipher-privacy.html", "hgq.html", "support.html", "contact.html", "privacy.html", "legal.html", "data-deletion.html"]]
    urls = [url for url in urls if url]
    if urls:
        body = "\n".join(f"  <url><loc>{escape(url)}</loc></url>" for url in urls)
    else:
        body = "  <!-- Configure site_url, then rebuild to emit absolute sitemap URLs. -->"
    (SITE / "sitemap.xml").write_text(f'''<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n''', encoding="utf-8")
    sitemap_ref = f"{site_url.rstrip('/')}{base_path}sitemap.xml" if site_url else "sitemap.xml"
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {sitemap_ref}\n", encoding="utf-8")


def copy_assets(import_assets: bool = False) -> None:
    for destination, source in ASSETS.items():
        target = SITE / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        if import_assets and source is not None:
            if not source.is_file():
                raise FileNotFoundError(f"Asset autorisé introuvable : {source}")
            shutil.copy2(source, target)
        elif not target.is_file():
            raise FileNotFoundError(f"Asset local absent : {target}. Utilisez --import-assets sur la machine source.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url", help="URL absolue finale, sans slash terminal")
    parser.add_argument("--base-path", help="Chemin GitHub Pages, par exemple /bb16-studio/")
    parser.add_argument("--import-assets", action="store_true", help="Actualiser les assets des applications depuis les projets source voisins")
    args = parser.parse_args()
    config = read_config()
    if args.site_url is not None:
        config["site_url"] = args.site_url.rstrip("/") or None
    if args.base_path is not None:
        config["base_path"] = normalise_base(args.base_path)
    base_path = normalise_base(config.get("base_path", "/"))
    config["site_url"] = validate_site_url(config.get("site_url"))
    copy_assets(args.import_assets)
    for filename, content in pages(config).items():
        (SITE / filename).write_text(content, encoding="utf-8", newline="\n")
    write_support_files(config, base_path)
    print(f"SITE_BUILT={SITE}")
    print(f"SITE_BASE_PATH={base_path}")
    print(f"SITE_URL={config.get('site_url') or 'UNCONFIGURED'}")
    print("SITE_PAGES=13")
    print(f"SITE_ASSETS={len(ASSETS)}")


if __name__ == "__main__":
    main()
