#!/usr/bin/env python3
"""Build the dependency-free BB16 Studio static site."""

from __future__ import annotations

import argparse
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
    <a class="wordmark" href="index.html" aria-label="BB16 Studio — Accueil"><img class="wordmark-logo" src="assets/branding/bb16-studio-logo-dark.png" alt="" width="1254" height="1254"></a>
    <div class="nav-links">{"".join(links)}</div>
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
  <link rel="icon" type="image/png" href="assets/branding/bb16-studio-logo-dark.png">
  <link rel="stylesheet" href="styles.css">
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
    <div class="actions"><a class="button secondary" href="apps.html">Voir les autres apps</a><a class="button" href="contact.html">Contacter BB16 Studio</a></div>
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
    <div class="actions"><a class="button secondary" href="apps.html">Voir les autres apps</a><a class="button" href="contact.html">Contacter BB16 Studio</a></div>
  </div>
  <aside class="aside"><img class="poster" src="assets/branding/doccipher-presentation.png" alt="Affiche de présentation DocCipher avec un coffre documentaire stylisé"><dl class="facts"><div class="fact"><dt>Plateforme</dt><dd>En développement pour Android</dd></div><div class="fact"><dt>iOS</dt><dd>À l'étude</dd></div><div class="fact"><dt>Téléchargement</dt><dd>Disponible prochainement</dd></div></dl></aside>
</div></section>'''
    return title, document(title, description, f"{kind}.html", body, config, f"{kind}.html")


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
        "privacy.html": document("Confidentialité", "Politique de confidentialité du site statique BB16 Studio.", "privacy.html", f'''<section class="section"><div class="container prose"><p class="eyebrow">Site web</p><h1>Confidentialité</h1><p class="lede">Ce site est un site statique de présentation. Il est conçu pour fonctionner sans compte et sans outil d'analyse marketing.</p><h2>Données du site</h2><p>BB16 Studio ne place pas de cookie analytique, de pixel publicitaire, de SDK de suivi ou de formulaire qui collecterait des données sur cette version du site. Un hébergeur peut traiter les journaux techniques nécessaires à la distribution HTTPS ; ces journaux relèvent de son propre fonctionnement et de ses règles publiques.</p><h2>Contact</h2><p>Si vous écrivez à <a href="mailto:{email}">{email}</a>, l'équipe reçoit les informations que vous choisissez d'inclure pour répondre à votre message. N'envoyez pas de secret ou de document sensible.</p><h2>Applications</h2><p>Cette page concerne le site BB16 Studio. Les applications ont leurs propres données, services tiers et parcours de suppression. Pour HGQ, la politique publiée par l'application est disponible sur <a href="https://hgq-prod.web.app/privacy" rel="noopener">hgq-prod.web.app/privacy</a>.</p><p>La <a href="data-deletion.html">page de suppression HGQ</a> du site reprend le parcours utilisateur connu et le canal de contact actuel.</p><h2>Mise à jour</h2><p>Cette page sera mise à jour lorsque l'identité légale, l'hébergement final ou les services du site changeront.</p></div></section>''', config, "privacy.html"),
        "legal.html": document("Mentions légales", "Informations légales publiques de BB16 Studio, en attente des données validées.", "legal.html", '''<section class="section"><div class="container prose"><p class="eyebrow">Informations légales</p><h1>Mentions légales</h1><p class="lede">Ce site présente les applications et les projets de BB16 Studio.</p><div class="callout legal-missing"><p>Les informations d'identification juridique et l'adresse publique de l'éditeur sont en cours de mise à jour.</p></div><h2>Éditeur</h2><p>Éditeur : BB16 Studio — identité légale à confirmer par le propriétaire.</p><p>Contact public : <a href="contact.html">bb16studio@gmail.com</a>.</p><h2>Propriété des contenus</h2><p>Les textes et visuels de ce site sont présentés sous réserve des droits de leurs titulaires. Les affiches ConvertAir et DocCipher sont les visuels fournis pour la présentation de leurs projets. Le logo BB16 Studio est fourni par le studio ; le logo HGQ provient des ressources de l'application.</p><h2>Préparation</h2><p>Les informations d'identité seront complétées lorsque le propriétaire les aura confirmées.</p></div></section>''', config, "legal.html"),
        "data-deletion.html": document("Suppression de compte", "Parcours de suppression de compte HGQ et informations à fournir au support.", "support.html", f'''<section class="section"><div class="container prose"><p class="eyebrow">HGQ · compte</p><h1>Suppression de compte</h1><p class="lede">Le parcours recommandé pour supprimer un compte Hard Gamer Quiz passe par l'application.</p><h2>Depuis l'application</h2><ol><li>Ouvrez HGQ et connectez-vous.</li><li>Ouvrez <strong>Paramètres</strong>.</li><li>Dans la section <strong>Mon compte</strong>, choisissez <strong>Supprimer mon compte</strong>.</li><li>Confirmez la suppression.</li></ol><p>Le projet décrit ce parcours comme une suppression en cascade des données de compte et de jeu. Les délais et éventuelles obligations de conservation doivent suivre la politique de l'application en vigueur.</p><h2>Si vous n'avez plus accès à l'application</h2><p>Écrivez à <a href="mailto:{email}">{email}</a> avec le nom de l'application et l'adresse email associée au compte. N'envoyez pas de mot de passe, code de connexion ou pièce d'identité par email sans demande explicite et vérifiée.</p><h2>Informations concernées</h2><p>Selon la politique HGQ publiée par l'application, le compte peut inclure une adresse email, un pseudo, des statistiques de jeu, des données sociales, des préférences, des identifiants techniques et des éléments d'économie du jeu. La politique applicative reste la référence pour les services tiers et les obligations de conservation.</p><div class="callout"><p>Cette page décrit le point d'entrée utilisateur et le canal de contact actuel.</p></div></div></section>''', config, "data-deletion.html"),
        "404.html": document("Page introuvable", "La page demandée n'existe pas sur le site BB16 Studio.", "", '''<section class="section"><div class="container prose"><p class="eyebrow">404</p><h1>Cette page n'existe pas.</h1><p class="lede">Le lien est peut-être ancien ou incomplet.</p><div class="actions"><a class="button" href="index.html">Retour à l'accueil</a><a class="button secondary" href="contact.html">Signaler un lien</a></div></div></section>''', config, "404.html"),
    }


def write_support_files(config: dict, base_path: str) -> None:
    site_url = config.get("site_url")
    urls = [page_url(name, site_url, base_path) for name in ["index.html", "studio.html", "apps.html", "convertair.html", "doccipher.html", "hgq.html", "support.html", "contact.html", "privacy.html", "legal.html", "data-deletion.html"]]
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
    print("SITE_PAGES=12")
    print(f"SITE_ASSETS={len(ASSETS)}")


if __name__ == "__main__":
    main()
