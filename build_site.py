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


# ---------------------------------------------------------------------------
# DÉCISIONS PROPRIÉTAIRE EN ATTENTE — pages de confidentialité (jamais rendu).
# Tant que le propriétaire ne les a pas tranchés, ces points ne sont PAS écrits
# dans les pages. Ne rien inventer à leur place.
#
# 1. Identité du responsable du traitement. Les deux pages nomment « BB16
#    Studio » et bb16studio@gmail.com, rien de plus : site.config.json porte
#    legal_name et public_address à null. L'article 13(1)(a) du RGPD demande
#    l'identité et les coordonnées du responsable, et Google Play attend que
#    l'entité corresponde au nom de développeur de la fiche. À fournir : nom
#    légal (personne physique ou société), adresse postale, numéro
#    d'immatriculation le cas échéant.
# 2. DocCipher, public visé et enfants. Le dépôt DocCipher ne déclare aucun
#    public cible. Pour ConvertAir, docs/store/data-safety.md répond
#    « Families : Non » et le brouillon docs/store/politique-confidentialite.md
#    contient la phrase « Enfants » reprise dans la page. La section
#    « Enfants » de DocCipher s'écrit une fois la tranche d'âge déclarée dans la
#    Play Console.
# 3. Durées de conservation chiffrées. Les pages donnent le critère : tant que
#    la donnée d'achat sert à gérer et restaurer l'achat, et suppression sur
#    demande. Une durée précise, ainsi que la conservation des emails de
#    support, restent à fixer par le propriétaire.
# 4. DocCipher, Premium en 1.0.0 (revue DC-L1-C2 du 22/09). Si la version
#    publiée ne vend rien, la section « Achats facultatifs », la permission
#    BILLING et le formulaire Data Safety sont à revoir avec cette décision.
# ---------------------------------------------------------------------------


def convertair_privacy_body(email: str) -> str:
    """Politique de confidentialité ConvertAir, bilingue sur une seule URL.

    POURQUOI UNE SEULE PAGE POUR DEUX LANGUES — le site est monolingue : le
    gabarit force `<html lang="fr">` et il n'existe aucun mécanisme de locale.
    Or l'application est distribuée dans vingt langues et sa fiche Play est
    relue en anglais. Une deuxième URL aurait obligé l'application à choisir
    laquelle ouvrir, donc à porter deux constantes au lieu d'une. Le français
    reste la langue du document ; la partie anglaise est balisée `lang="en"`
    pour les lecteurs d'écran et les moteurs.

    D'OÙ VIENT CHAQUE PHRASE — ce qui décrit l'application est adossé à une
    lecture du code de ConvertAir : manifeste release et test
    `expected_permissions_test.dart`, wrapper RevenueCat, règles de sauvegarde,
    dépendances de `pubspec.yaml`, `FontPackChannel.kt`, services de partage et
    d'impression. Le rôle de sous-traitant de RevenueCat et les clauses
    contractuelles types viennent de l'accord de traitement des données publié
    par RevenueCat (revenuecat.com/dpa, lu le 22 septembre 2026). Ce qui relève
    d'une décision du propriétaire n'est pas écrit : voir le bloc DÉCISIONS
    PROPRIÉTAIRE ci-dessus.
    """
    return f'''<section class="section"><div class="container prose">
<p class="eyebrow">ConvertAir · application mobile</p>
<h1>Politique de confidentialité</h1>
<p class="lede">ConvertAir traite vos documents sur votre appareil. Cette page décrit ce que l'application fait réellement, ce qu'elle ne fait pas, et les seules données qui en sortent : celles de vos achats.</p>
<p class="meta">Dernière mise à jour : 22 septembre 2026 · <a href="#english">Read this page in English</a></p>

<h2>Responsable du traitement</h2>
<p>Le responsable du traitement est BB16 Studio, éditeur de ConvertAir. Pour toute question ou demande sur vos données, écrivez à <a href="mailto:{email}">{email}</a>. Cette politique couvre la version Android de ConvertAir distribuée sur Google Play.</p>

<h2>Vos documents restent sur votre appareil</h2>
<p>La numérisation, les conversions, l'assemblage, la compression, l'annotation, la signature et la reconnaissance de texte (OCR) s'exécutent sur votre téléphone. Aucun document, aucune image et aucun texte reconnu n'est transmis à BB16 Studio ni à un tiers.</p>
<p>La reconnaissance de texte utilise des modèles embarqués dans l'application : elle a lieu sur l'appareil, et ConvertAir n'envoie aucune image à un serveur pour cela. La capture de documents est déléguée aux services Google Play installés sur votre téléphone ; ConvertAir ne transmet lui-même aucun document, mais ce traitement se déroule dans un composant Google, régi par la politique de confidentialité de Google et non par la nôtre.</p>

<h2>Partage, enregistrement et impression</h2>
<p>Un fichier ne quitte ConvertAir que lorsque vous le décidez : partage par la feuille de partage d'Android, enregistrement à l'emplacement que vous choisissez, ou impression. Il part alors vers l'application, le dossier ou le service d'impression que vous avez désigné, qui le traite selon ses propres règles. BB16 Studio n'en reçoit aucune copie.</p>

<h2>La seule connexion réseau de l'application : les achats</h2>
<p>ConvertAir ouvre une connexion réseau pour une seule raison : les achats. Cela couvre l'affichage des offres, l'achat et la restauration d'un achat. Le paiement est réalisé par Google Play. La vérification de l'achat et de votre accès Premium est confiée à RevenueCat, un prestataire qui agit pour le compte de BB16 Studio et sur ses instructions (sous-traitant au sens du RGPD). Aucun contenu de document ne passe par ce chemin.</p>
<p>Lors de ces échanges, RevenueCat reçoit :</p>
<ul>
<li>le jeton d'achat (reçu) Google Play, le produit acheté, les dates de la transaction et l'état de votre accès Premium (actif ou expiré) ;</li>
<li>un identifiant d'utilisateur aléatoire, créé par le SDK RevenueCat lors de la première utilisation ;</li>
<li>des informations techniques jointes à chaque requête : la plateforme et la version d'Android, la version de l'application et celle du SDK ;</li>
<li>l'adresse IP de votre connexion, que reçoit tout serveur contacté et dont un pays approximatif peut être déduit.</li>
</ul>
<p>Cet identifiant ne contient ni votre nom ni votre adresse email, mais il n'est pas anonyme : il est associé à vos achats Google Play, eux-mêmes liés à votre compte Google, et une restauration d'achat peut le relier aux identifiants de vos autres installations. C'est une donnée pseudonyme. Aucun compte n'est créé, la collecte automatique d'identifiants d'appareil (identifiant publicitaire, identifiant Android) est désactivée, et les diagnostics du SDK sont désactivés.</p>
<p>Comme pour tout achat sur le Play Store, Google Play reçoit votre compte Google, le produit et vos informations de paiement. Google traite ces données en tant que responsable distinct, selon sa propre politique de confidentialité. Dans sa console, Google Play fournit à BB16 Studio les informations de commande nécessaires à la gestion des ventes, notamment le numéro de commande, le produit, le prix et le pays d'achat. BB16 Studio ne voit jamais vos coordonnées bancaires.</p>

<h2>Finalité et base légale</h2>
<p>Les données d'achat servent uniquement à vous fournir, vérifier et restaurer ce que vous avez acheté. Ce traitement est nécessaire à l'exécution du contrat d'achat (article 6, paragraphe 1, point b, du RGPD). Elles ne servent ni à la publicité, ni au profilage, ni au suivi. Si vous nous écrivez, votre message et votre adresse email servent à vous répondre, sur la base de notre intérêt légitime à le faire, ou de nos obligations légales lorsque vous exercez vos droits.</p>

<h2>Transfert hors de l'Union européenne</h2>
<p>RevenueCat, Inc. est établie aux États-Unis, où les données d'achat décrites ci-dessus sont traitées. Ce transfert est encadré par les clauses contractuelles types de la Commission européenne, intégrées à l'accord de traitement des données de RevenueCat. Vous pouvez en demander une copie à <a href="mailto:{email}">{email}</a>.</p>

<h2>Durée de conservation</h2>
<p>Les données d'achat sont conservées par RevenueCat tant qu'elles servent à gérer et à restaurer votre achat, et supprimées si vous le demandez (voir « Vos droits »). Google Play conserve ses propres données de commande selon sa politique. Les données stockées sur votre appareil y restent jusqu'à ce que vous les supprimiez ou désinstalliez l'application.</p>

<h2>Ce que l'application ne fait pas</h2>
<ul>
<li>Aucun compte, aucune inscription, aucune adresse email demandée.</li>
<li>Aucun outil de mesure d'audience, de statistiques d'usage ou de rapport de plantage intégré à l'application.</li>
<li>Aucun identifiant publicitaire : la permission <code>com.google.android.gms.permission.AD_ID</code> n'est pas déclarée.</li>
<li>Aucune publicité, aucune vente de données, aucun partage à des fins commerciales.</li>
<li>Aucun suivi d'une application à l'autre ni d'un site à l'autre.</li>
</ul>

<h2>Rapports de plantage d'Android</h2>
<p>Si vous avez accepté, dans les réglages de votre appareil, de partager les données d'utilisation et de diagnostic avec Google, Android peut envoyer à Google des rapports de plantage et de performance. Google Play les met à la disposition de BB16 Studio dans sa console (Android Vitals), sous forme de statistiques agrégées et de rapports techniques : modèle d'appareil, version d'Android, trace de l'erreur. Ce mécanisme appartient au système, pas à ConvertAir. Ces rapports ne contiennent ni vos documents, ni votre nom, ni votre adresse email, et vous pouvez les désactiver dans les réglages de l'appareil.</p>

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
<p>Les fichiers que vous produisez, un historique local des opérations, vos préférences d'affichage et vos signatures enregistrées, dans l'espace privé de l'application. Les images de signature sont chiffrées sur l'appareil. L'historique peut être purgé automatiquement au bout de 30 jours, de 90 jours, ou conservé, selon le réglage que vous choisissez dans l'écran Réglages.</p>
<p>Désinstaller ConvertAir efface cet espace privé, y compris les fichiers produits que vous n'avez ni partagés ni enregistrés ailleurs. Les copies enregistrées hors de l'application restent à l'emplacement choisi.</p>

<h2>Polices supplémentaires, téléchargées par Google Play</h2>
<p>Pour produire un PDF interrogeable en chinois, en japonais, en coréen ou dans une écriture devanagari, ConvertAir a besoin de polices supplémentaires. Elles ne sont téléchargées que si vous le demandez, depuis l'écran Réglages ou les options de reconnaissance de texte. Le téléchargement est assuré par Google Play (Play Asset Delivery), comme une mise à jour de l'application : ConvertAir n'ouvre aucune connexion pour cela et ne transmet aucun document. Google Play, qui reçoit cette demande, applique sa propre politique de confidentialité.</p>

<h2>Enfants</h2>
<p>ConvertAir ne s'adresse pas spécifiquement aux enfants et ne collecte sciemment aucune donnée les concernant.</p>

<h2>Vos droits</h2>
<p>Vos documents, votre historique et vos signatures ne se trouvent que sur votre appareil : vous les consultez, les exportez et les supprimez vous-même, dans l'application ou en la désinstallant. BB16 Studio n'en détient aucune copie.</p>
<p>Pour les données d'achat que RevenueCat traite pour le compte de BB16 Studio, vous pouvez demander l'accès, la rectification, l'effacement, la limitation ou la portabilité, et vous opposer au traitement lorsqu'il repose sur notre intérêt légitime. Écrivez à <a href="mailto:{email}">{email}</a> en indiquant votre numéro de commande Google Play : il commence par « GPA. » et figure dans l'email de reçu envoyé par Google Play. L'application ne vous demandant aucune identité, ce numéro est le seul moyen de retrouver votre achat. Le RGPD nous donne un mois pour vous répondre.</p>
<p>Effacer ces données n'annule pas votre achat : Google Play le conserve, et une restauration ultérieure le retrouve, en transmettant de nouveau à RevenueCat les données décrites plus haut. Un abonnement se gère et s'annule dans Google Play.</p>
<p>Si vous estimez que vos droits ne sont pas respectés, vous pouvez introduire une réclamation auprès d'une autorité de protection des données, en France la <a href="https://www.cnil.fr/" rel="noopener">CNIL</a>.</p>

<h2>Modifications</h2>
<p>Si le comportement de l'application change, cette page est mise à jour avec lui et la date ci-dessus change.</p>

<hr>

<div lang="en">
<h2 id="english">English version</h2>
<p class="lede">ConvertAir processes your documents on your device. This page describes what the app actually does, what it does not do, and the only data that leaves it: your purchase data.</p>
<p class="meta">Last updated: 22 September 2026 · <a href="#main">Lire cette page en français</a></p>

<h3>Data controller</h3>
<p>The data controller is BB16 Studio, publisher of ConvertAir. For any question or request about your data, write to <a href="mailto:{email}">{email}</a>. This policy covers the Android version of ConvertAir distributed on Google Play.</p>

<h3>Your documents stay on your device</h3>
<p>Scanning, conversions, merging, compression, annotation, signing and text recognition (OCR) all run on your phone. No document, no image and no recognised text is sent to BB16 Studio or to any third party.</p>
<p>Text recognition uses models bundled inside the app: it runs on the device, and ConvertAir sends no image to any server for it. Document capture is delegated to the Google Play services installed on your phone; ConvertAir itself transmits no document, but that step runs inside a Google component, governed by Google's privacy policy rather than ours.</p>

<h3>Sharing, saving and printing</h3>
<p>A file leaves ConvertAir only when you decide so: sharing through the Android share sheet, saving to a location you choose, or printing. It then goes to the app, folder or print service you selected, which handles it under its own rules. BB16 Studio receives no copy.</p>

<h3>The app's only network connection: purchases</h3>
<p>ConvertAir opens a network connection for one reason: purchases. That covers showing the offers, buying, and restoring a purchase. The payment is carried out by Google Play. Checking the purchase and your Premium access is entrusted to RevenueCat, a provider acting on behalf of BB16 Studio and on its instructions (a processor under the GDPR). No document content travels over that path.</p>
<p>During these exchanges, RevenueCat receives:</p>
<ul>
<li>the Google Play purchase token (receipt), the product purchased, the transaction dates and the status of your Premium access (active or expired);</li>
<li>a random user identifier, created by the RevenueCat SDK on first use;</li>
<li>technical information attached to each request: the platform and Android version, the app version and the SDK version;</li>
<li>the IP address of your connection, which any server contacted receives and from which an approximate country can be derived.</li>
</ul>
<p>This identifier contains neither your name nor your email address, but it is not anonymous: it is associated with your Google Play purchases, which are linked to your Google account, and restoring a purchase can link it to the identifiers of your other installations. It is pseudonymous data. No account is created, automatic collection of device identifiers (advertising ID, Android ID) is turned off, and SDK diagnostics are turned off.</p>
<p>As with any Play Store purchase, Google Play receives your Google account, the product and your payment details. Google processes this data as a separate controller, under its own privacy policy. In its console, Google Play gives BB16 Studio the order information needed to manage sales, including the order number, product, price and country of purchase. BB16 Studio never sees your payment card details.</p>

<h3>Purpose and legal basis</h3>
<p>Purchase data is used only to provide, verify and restore what you bought. This processing is necessary for the performance of the purchase contract (GDPR Article 6(1)(b)). It is not used for advertising, profiling or tracking. If you write to us, your message and email address are used to answer you, on the basis of our legitimate interest in doing so, or of our legal obligations when you exercise your rights.</p>

<h3>Transfer outside the European Union</h3>
<p>RevenueCat, Inc. is based in the United States, where the purchase data described above is processed. This transfer is covered by the European Commission's standard contractual clauses, included in RevenueCat's data processing agreement. You can request a copy at <a href="mailto:{email}">{email}</a>.</p>

<h3>Retention</h3>
<p>Purchase data is kept by RevenueCat for as long as it is needed to manage and restore your purchase, and deleted if you ask (see "Your rights"). Google Play keeps its own order data under its policy. Data stored on your device stays there until you delete it or uninstall the app.</p>

<h3>What the app does not do</h3>
<ul>
<li>No account, no sign-up, no email address requested.</li>
<li>No analytics, usage measurement or crash-reporting tool built into the app.</li>
<li>No advertising identifier: the <code>com.google.android.gms.permission.AD_ID</code> permission is not declared.</li>
<li>No advertising, no sale of data, no sharing for commercial purposes.</li>
<li>No tracking across apps or across websites.</li>
</ul>

<h3>Android crash reports</h3>
<p>If you agreed, in your device settings, to share usage and diagnostics data with Google, Android may send crash and performance reports to Google. Google Play makes them available to BB16 Studio in its console (Android Vitals), as aggregated statistics and technical reports: device model, Android version, error trace. This mechanism belongs to the system, not to ConvertAir. These reports contain none of your documents, nor your name or email address, and you can turn them off in your device settings.</p>

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
<p>The files you produce, a local history of operations, your display preferences and your saved signatures, in the app's private storage. Signature images are encrypted on the device. History can be purged automatically after 30 days, after 90 days, or kept, depending on the setting you choose in the Settings screen.</p>
<p>Uninstalling ConvertAir erases that private storage, including produced files that you have neither shared nor saved elsewhere. Copies saved outside the app remain where you put them.</p>

<h3>Additional fonts, downloaded by Google Play</h3>
<p>To produce a searchable PDF in Chinese, Japanese, Korean or a Devanagari script, ConvertAir needs additional fonts. They are downloaded only if you ask, from the Settings screen or the text-recognition options. The download is handled by Google Play (Play Asset Delivery), like an app update: ConvertAir opens no connection for it and sends no document. Google Play, which receives the request, applies its own privacy policy.</p>

<h3>Children</h3>
<p>ConvertAir is not directed at children and does not knowingly collect any data about them.</p>

<h3>Your rights</h3>
<p>Your documents, history and signatures exist only on your device: you view, export and delete them yourself, in the app or by uninstalling it. BB16 Studio holds no copy of them.</p>
<p>For the purchase data that RevenueCat processes on behalf of BB16 Studio, you can request access, rectification, erasure, restriction or portability, and object to processing based on our legitimate interest. Write to <a href="mailto:{email}">{email}</a> with your Google Play order number: it starts with "GPA." and appears in the receipt email sent by Google Play. Since the app asks for no identity, this number is the only way to find your purchase. The GDPR gives us one month to reply.</p>
<p>Erasing this data does not cancel your purchase: Google Play keeps it, and a later restore finds it again, sending the data described above to RevenueCat once more. Subscriptions are managed and cancelled in Google Play.</p>
<p>If you believe your rights are not respected, you can lodge a complaint with a data protection authority; in France, the <a href="https://www.cnil.fr/" rel="noopener">CNIL</a>.</p>

<h3>Changes</h3>
<p>If the app's behaviour changes, this page changes with it and the date above is updated.</p>
</div>

<div class="actions"><a class="button secondary" href="convertair.html">Retour à ConvertAir</a><a class="button" href="contact.html">Nous écrire</a></div>
</div></section>'''


def doccipher_privacy_body(email: str) -> str:
    """Politique de confidentialité DocCipher, français et anglais.

    Même construction que la page ConvertAir. Ce qui décrit l'application est
    adossé au code de DocCipher : manifeste et test
    `expected_permissions_test.dart` (cinq permissions, dont USE_BIOMETRIC et
    USE_FINGERPRINT bornée à l'API 28), `biometric_gate.dart`, wrapper
    RevenueCat, règles d'extraction des données. Aucune section « Enfants » :
    voir le point 2 du bloc DÉCISIONS PROPRIÉTAIRE.
    """
    return f'''<section class="section"><div class="container prose">
<p class="eyebrow">DocCipher · application mobile</p>
<h1>Politique de confidentialité</h1>
<p class="lede">DocCipher conserve vos documents dans un coffre chiffré sur votre appareil. Il n'existe ni compte DocCipher ni serveur documentaire BB16 Studio.</p>
<p class="meta">Dernière mise à jour : 22 septembre 2026 · <a href="#english">Read this page in English</a></p>

<h2>Responsable du traitement</h2>
<p>Le responsable du traitement est BB16 Studio, éditeur de DocCipher. Pour toute question ou demande sur vos données, écrivez à <a href="mailto:{email}">{email}</a>. Cette politique couvre la version Android de DocCipher distribuée sur Google Play.</p>

<h2>Documents et chiffrement local</h2>
<p>Les documents importés ou numérisés, leurs aperçus, le texte reconnu par OCR, les dossiers, les tags et les données du coffre restent dans l'espace privé de l'application. Le coffre est chiffré sur l'appareil. BB16 Studio ne reçoit ni vos documents, ni leur contenu, ni votre mot de passe, ni votre matériel de récupération.</p>
<p>La reconnaissance de texte (OCR) s'exécute sur l'appareil, avec des modèles embarqués dans l'application : aucune image et aucun texte ne sont envoyés à un serveur pour cela. La capture est déléguée au scanner de documents fourni par les services Google Play installés sur le téléphone : DocCipher ne transmet lui-même aucun document, mais cette étape s'exécute dans un composant Google régi par les règles de Google.</p>

<h2>Ni serveur documentaire, ni synchronisation</h2>
<p>BB16 Studio n'exploite aucun serveur qui héberge, analyse, synchronise ou sauvegarde vos documents. La synchronisation WebDAV ou Nextcloud n'est pas disponible dans cette version, pas plus qu'un autre stockage en ligne. Vos documents ne quittent l'appareil que par un export que vous déclenchez vous-même.</p>

<h2>Exports et sauvegardes que vous choisissez</h2>
<p>Un document ou une sauvegarde <code>.dcvault</code> ne quitte l'application que lorsque vous déclenchez explicitement un export et choisissez sa destination avec le sélecteur ou la feuille de partage du système. Une sauvegarde <code>.dcvault</code> reste chiffrée ; un document exporté en clair ne l'est plus et relève alors de la sécurité de la destination choisie.</p>
<p>La sauvegarde automatique Android et le transfert automatique vers un nouvel appareil sont désactivés.</p>

<h2>Déverrouillage biométrique</h2>
<p>Si vous l'activez, le déverrouillage biométrique passe par l'invite du système Android. DocCipher ne reçoit que sa réponse, identité confirmée ou non : il n'accède à aucune empreinte, à aucune image de visage ni à aucun gabarit biométrique, qui restent dans la zone sécurisée de l'appareil. La biométrie ne remplace pas votre code PIN, qui reste nécessaire.</p>

<h2>Achats facultatifs</h2>
<p>DocCipher n'ouvre de connexion réseau que pour les achats facultatifs : afficher les offres, acheter, restaurer un achat. Vous pouvez utiliser DocCipher sans rien acheter. Le paiement est réalisé par Google Play. La vérification de l'achat et de votre accès Premium est confiée à RevenueCat, un prestataire qui agit pour le compte de BB16 Studio et sur ses instructions (sous-traitant au sens du RGPD). Aucun document, aucun mot de passe et aucune clé ne passent par ce chemin.</p>
<p>Lors de ces échanges, RevenueCat reçoit :</p>
<ul>
<li>le jeton d'achat (reçu) Google Play, le produit acheté, les dates de la transaction et l'état de votre accès Premium (actif ou expiré) ;</li>
<li>un identifiant d'utilisateur aléatoire, créé par le SDK RevenueCat lors de la première utilisation ;</li>
<li>des informations techniques jointes à chaque requête : la plateforme et la version d'Android, la version de l'application et celle du SDK ;</li>
<li>l'adresse IP de votre connexion, que reçoit tout serveur contacté et dont un pays approximatif peut être déduit.</li>
</ul>
<p>Cet identifiant ne contient ni votre nom ni votre adresse email, mais il n'est pas anonyme : il est associé à vos achats Google Play, eux-mêmes liés à votre compte Google, et une restauration d'achat peut le relier aux identifiants de vos autres installations. C'est une donnée pseudonyme. Aucun compte n'est créé, la collecte automatique d'identifiants d'appareil (identifiant publicitaire, identifiant Android) est désactivée, et les diagnostics du SDK sont désactivés.</p>
<p>Comme pour tout achat sur le Play Store, Google Play reçoit votre compte Google, le produit et vos informations de paiement. Google traite ces données en tant que responsable distinct, selon sa propre politique de confidentialité. Dans sa console, Google Play fournit à BB16 Studio les informations de commande nécessaires à la gestion des ventes, notamment le numéro de commande, le produit, le prix et le pays d'achat. BB16 Studio ne voit jamais vos coordonnées bancaires.</p>

<h2>Finalité et base légale</h2>
<p>Les données d'achat servent uniquement à vous fournir, vérifier et restaurer ce que vous avez acheté. Ce traitement est nécessaire à l'exécution du contrat d'achat (article 6, paragraphe 1, point b, du RGPD). Elles ne servent ni à la publicité, ni au profilage, ni au suivi. Si vous nous écrivez, votre message et votre adresse email servent à vous répondre, sur la base de notre intérêt légitime à le faire, ou de nos obligations légales lorsque vous exercez vos droits.</p>

<h2>Transfert hors de l'Union européenne</h2>
<p>RevenueCat, Inc. est établie aux États-Unis, où les données d'achat décrites ci-dessus sont traitées. Ce transfert est encadré par les clauses contractuelles types de la Commission européenne, intégrées à l'accord de traitement des données de RevenueCat. Vous pouvez en demander une copie à <a href="mailto:{email}">{email}</a>.</p>

<h2>Durée de conservation</h2>
<p>Les données d'achat sont conservées par RevenueCat tant qu'elles servent à gérer et à restaurer votre achat, et supprimées si vous le demandez (voir « Suppression et vos droits »). Google Play conserve ses propres données de commande selon sa politique. Le coffre et les autres données locales restent sur votre appareil jusqu'à ce que vous supprimiez le coffre ou désinstalliez l'application.</p>

<h2>Ce que DocCipher ne fait pas</h2>
<ul>
<li>Aucun compte utilisateur DocCipher et aucune adresse email demandée.</li>
<li>Aucune publicité, aucun identifiant publicitaire et aucune vente de données.</li>
<li>Aucun outil d'analytics, de suivi d'usage ou de rapport de plantage intégré à l'application.</li>
<li>Aucun suivi d'une application à l'autre ni d'un site à l'autre.</li>
</ul>

<h2>Rapports de plantage d'Android</h2>
<p>Si vous avez accepté, dans les réglages de votre appareil, de partager les données d'utilisation et de diagnostic avec Google, Android peut envoyer à Google des rapports de plantage et de performance. Google Play les met à la disposition de BB16 Studio dans sa console (Android Vitals), sous forme de statistiques agrégées et de rapports techniques : modèle d'appareil, version d'Android, trace de l'erreur. Ce mécanisme appartient au système, pas à DocCipher. Ces rapports ne contiennent ni vos documents, ni votre nom, ni votre adresse email, et vous pouvez les désactiver dans les réglages de l'appareil.</p>

<h2>Permissions Android</h2>
<p>Le manifeste de la version publiée déclare exactement cinq entrées :</p>
<ul>
<li><code>android.permission.INTERNET</code> — les achats, et rien d'autre ;</li>
<li><code>com.android.vending.BILLING</code> — la facturation Google Play ;</li>
<li><code>android.permission.USE_BIOMETRIC</code> — afficher l'invite biométrique du système ; elle ne donne accès à aucune donnée biométrique ;</li>
<li><code>android.permission.USE_FINGERPRINT</code>, limitée à Android 9 et aux versions antérieures — le même rôle sur ces versions ;</li>
<li>une permission de signature interne à l'application, qui n'ouvre aucune capacité de l'appareil.</li>
</ul>
<p>Aucune permission de caméra, de localisation, de contacts, de microphone ou de stockage étendu n'est demandée : les fichiers passent par les sélecteurs du système et la capture par le composant des services Google Play.</p>

<h2>Suppression et vos droits</h2>
<p>Vous pouvez supprimer les données locales en supprimant le coffre ou en désinstallant l'application. Une copie que vous avez exportée reste à l'emplacement choisi jusqu'à ce que vous l'y supprimiez. BB16 Studio ne peut pas extraire, déchiffrer ni restaurer votre coffre à distance.</p>
<p>Pour les données d'achat que RevenueCat traite pour le compte de BB16 Studio, vous pouvez demander l'accès, la rectification, l'effacement, la limitation ou la portabilité, et vous opposer au traitement lorsqu'il repose sur notre intérêt légitime. Écrivez à <a href="mailto:{email}">{email}</a> en indiquant votre numéro de commande Google Play : il commence par « GPA. » et figure dans l'email de reçu envoyé par Google Play. L'application ne vous demandant aucune identité, ce numéro est le seul moyen de retrouver votre achat. Ne joignez jamais de document, de mot de passe, de clé ou de phrase de récupération. Le RGPD nous donne un mois pour vous répondre.</p>
<p>Effacer ces données n'annule pas votre achat : Google Play le conserve, et une restauration ultérieure le retrouve, en transmettant de nouveau à RevenueCat les données décrites plus haut. Un abonnement se gère et s'annule dans Google Play.</p>
<p>Si vous estimez que vos droits ne sont pas respectés, vous pouvez introduire une réclamation auprès d'une autorité de protection des données, en France la <a href="https://www.cnil.fr/" rel="noopener">CNIL</a>.</p>

<h2>Modifications</h2>
<p>Cette page sera mise à jour si les flux de données, les services tiers ou les permissions de l'application changent.</p>

<hr>

<div lang="en">
<h2 id="english">English version</h2>
<p class="lede">DocCipher keeps your documents in an encrypted vault on your device. There is no DocCipher account and no BB16 Studio document server.</p>
<p class="meta">Last updated: 22 September 2026 · <a href="#main">Lire cette page en français</a></p>

<h3>Data controller</h3>
<p>The data controller is BB16 Studio, publisher of DocCipher. For any question or request about your data, write to <a href="mailto:{email}">{email}</a>. This policy covers the Android version of DocCipher distributed on Google Play.</p>

<h3>Documents and local encryption</h3>
<p>Imported or scanned documents, previews, recognised text, folders, tags and vault data remain in the app's private storage. The vault is encrypted on the device. BB16 Studio receives neither your documents nor their content, your password or your recovery material.</p>
<p>Text recognition (OCR) runs on the device, using models bundled in the app: no image and no text is sent to any server for it. Capture is delegated to the document scanner supplied by Google Play services on the phone: DocCipher itself sends no document, but this step runs in a Google component governed by Google's rules.</p>

<h3>No document server, no synchronisation</h3>
<p>BB16 Studio runs no server that hosts, analyses, synchronises or backs up your documents. WebDAV or Nextcloud synchronisation is not available in this version, and neither is any other online storage. Your documents leave the device only through an export you start yourself.</p>

<h3>Exports and backups you choose</h3>
<p>A document or <code>.dcvault</code> backup leaves the app only when you explicitly start an export and choose its destination through the system picker or share sheet. A <code>.dcvault</code> backup remains encrypted; a document exported in clear form is no longer encrypted and then depends on the security of your chosen destination.</p>
<p>Android automatic backup and automatic device-to-device transfer are disabled.</p>

<h3>Biometric unlock</h3>
<p>If you turn it on, biometric unlock uses the Android system prompt. DocCipher only receives its answer, identity confirmed or not: it has no access to any fingerprint, face image or biometric template, which stay in the device's secure area. Biometrics do not replace your PIN, which is still required.</p>

<h3>Optional purchases</h3>
<p>DocCipher opens a network connection only for optional purchases: showing offers, buying, restoring a purchase. You can use DocCipher without buying anything. The payment is carried out by Google Play. Checking the purchase and your Premium access is entrusted to RevenueCat, a provider acting on behalf of BB16 Studio and on its instructions (a processor under the GDPR). No document, password or key travels over this path.</p>
<p>During these exchanges, RevenueCat receives:</p>
<ul>
<li>the Google Play purchase token (receipt), the product purchased, the transaction dates and the status of your Premium access (active or expired);</li>
<li>a random user identifier, created by the RevenueCat SDK on first use;</li>
<li>technical information attached to each request: the platform and Android version, the app version and the SDK version;</li>
<li>the IP address of your connection, which any server contacted receives and from which an approximate country can be derived.</li>
</ul>
<p>This identifier contains neither your name nor your email address, but it is not anonymous: it is associated with your Google Play purchases, which are linked to your Google account, and restoring a purchase can link it to the identifiers of your other installations. It is pseudonymous data. No account is created, automatic collection of device identifiers (advertising ID, Android ID) is turned off, and SDK diagnostics are turned off.</p>
<p>As with any Play Store purchase, Google Play receives your Google account, the product and your payment details. Google processes this data as a separate controller, under its own privacy policy. In its console, Google Play gives BB16 Studio the order information needed to manage sales, including the order number, product, price and country of purchase. BB16 Studio never sees your payment card details.</p>

<h3>Purpose and legal basis</h3>
<p>Purchase data is used only to provide, verify and restore what you bought. This processing is necessary for the performance of the purchase contract (GDPR Article 6(1)(b)). It is not used for advertising, profiling or tracking. If you write to us, your message and email address are used to answer you, on the basis of our legitimate interest in doing so, or of our legal obligations when you exercise your rights.</p>

<h3>Transfer outside the European Union</h3>
<p>RevenueCat, Inc. is based in the United States, where the purchase data described above is processed. This transfer is covered by the European Commission's standard contractual clauses, included in RevenueCat's data processing agreement. You can request a copy at <a href="mailto:{email}">{email}</a>.</p>

<h3>Retention</h3>
<p>Purchase data is kept by RevenueCat for as long as it is needed to manage and restore your purchase, and deleted if you ask (see "Deletion and your rights"). Google Play keeps its own order data under its policy. The vault and other local data stay on your device until you delete the vault or uninstall the app.</p>

<h3>What DocCipher does not do</h3>
<ul>
<li>No DocCipher user account and no email address requested.</li>
<li>No advertising, advertising identifier or sale of data.</li>
<li>No analytics, usage tracking or crash-reporting tool built into the app.</li>
<li>No tracking across apps or across websites.</li>
</ul>

<h3>Android crash reports</h3>
<p>If you agreed, in your device settings, to share usage and diagnostics data with Google, Android may send crash and performance reports to Google. Google Play makes them available to BB16 Studio in its console (Android Vitals), as aggregated statistics and technical reports: device model, Android version, error trace. This mechanism belongs to the system, not to DocCipher. These reports contain none of your documents, nor your name or email address, and you can turn them off in your device settings.</p>

<h3>Android permissions</h3>
<p>The published build's manifest declares exactly five entries:</p>
<ul>
<li><code>android.permission.INTERNET</code> — purchases, and nothing else;</li>
<li><code>com.android.vending.BILLING</code> — Google Play billing;</li>
<li><code>android.permission.USE_BIOMETRIC</code> — showing the system biometric prompt; it gives no access to any biometric data;</li>
<li><code>android.permission.USE_FINGERPRINT</code>, limited to Android 9 and earlier — the same role on those versions;</li>
<li>an app-internal signature permission, which grants no device capability.</li>
</ul>
<p>No camera, location, contacts, microphone or broad storage permission is requested: files use system pickers and capture uses the Google Play services component.</p>

<h3>Deletion and your rights</h3>
<p>You can remove local data by deleting the vault or uninstalling the app. A copy you exported remains at the destination you chose until you delete it there. BB16 Studio cannot remotely extract, decrypt or restore your vault.</p>
<p>For the purchase data that RevenueCat processes on behalf of BB16 Studio, you can request access, rectification, erasure, restriction or portability, and object to processing based on our legitimate interest. Write to <a href="mailto:{email}">{email}</a> with your Google Play order number: it starts with "GPA." and appears in the receipt email sent by Google Play. Since the app asks for no identity, this number is the only way to find your purchase. Never attach a document, password, key or recovery phrase. The GDPR gives us one month to reply.</p>
<p>Erasing this data does not cancel your purchase: Google Play keeps it, and a later restore finds it again, sending the data described above to RevenueCat once more. Subscriptions are managed and cancelled in Google Play.</p>
<p>If you believe your rights are not respected, you can lodge a complaint with a data protection authority; in France, the <a href="https://www.cnil.fr/" rel="noopener">CNIL</a>.</p>

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
