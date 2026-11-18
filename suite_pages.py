"""Shared suite presentation and bounded, unpublished PeakSolo information."""
from html import escape
import re


def peaksolo_card():
    return '''<article class="card suite-card"><div class="icon-card"><img src="assets/apps/peaksolo-icon-192.webp" alt="" width="72" height="72" class="app-icon" loading="lazy" decoding="async"><div><h3><a class="card-link" href="peaksolo.html">PeakSolo</a></h3><p>Gestion d'activité en préparation : clients, documents et trésorerie.</p></div></div><p class="meta">Bientôt sur Android</p><div class="actions"><a class="button secondary" href="peaksolo.html">Lire la fiche</a></div></article>'''


def suite_intro():
    return '''<section class="section suite-overview"><div class="container"><div class="section-head"><div><p class="eyebrow">La suite BB16</p><h2>Préparer. Protéger. Piloter.</h2></div><p>ConvertAir et DocCipher partagent les mêmes repères. PeakSolo rejoint cette famille, avec un parcours pensé pour votre activité.</p></div><ol class="suite-flow"><li><strong>ConvertAir</strong><span>Préparer vos documents</span></li><li><strong>DocCipher</strong><span>Protéger vos documents</span></li><li><strong>PeakSolo</strong><span>Piloter votre activité · en préparation</span></li></ol><p class="meta">Des applications complémentaires. Les transferts entre applications restent à votre initiative ; aucune synchronisation automatique ni offre groupée n'est disponible.</p></div></section>'''


def peaksolo_body():
    return '''<nav class="product-nav" aria-label="Dans cette page"><div class="container product-nav-inner"><a class="product-nav-name" href="#presentation">PeakSolo</a><div class="product-nav-links"><a href="#fonctions">Fonctions</a><a href="#confidentialite">Confidentialité</a><a href="#faq">FAQ</a></div></div></nav>
<section class="product-hero planned-product" id="presentation"><div class="container"><div class="peaksolo-identity" data-reveal><img src="assets/apps/peaksolo-icon-192.webp" alt="" width="160" height="160" decoding="async" fetchpriority="high"><span class="peaksolo-wordmark" dir="ltr" translate="no">Peak<span>Solo</span></span></div><p class="eyebrow">La suite BB16</p><h1>Votre activité.<br>Vos repères.</h1><p class="lede">PeakSolo se prépare à réunir clients, documents et trésorerie dans une expérience cohérente avec ConvertAir et DocCipher.</p><p class="hero-status"><span class="status pending">Bientôt sur Android</span></p><p>Présentation du projet : aucune disponibilité, conformité nationale ou date de sortie n'est annoncée.</p><div class="actions"><a class="button" href="#fonctions">Découvrir le projet</a><a class="button secondary" href="support.html">Support</a></div></div></section>
<section class="section" id="fonctions"><div class="container"><div class="section-head"><div><p class="eyebrow">En préparation</p><h2>Un projet, trois repères.</h2></div></div><div class="grid"><article class="card"><h3>Clients et documents</h3><p>Objectif : retrouver vos clients, devis et factures. Les formats et pays pris en charge seront précisés après validation.</p></article><article class="card"><h3>Trésorerie lisible</h3><p>Objectif : comprendre les encaissements, dépenses et provisions que vous renseignez, sans les présenter comme un solde bancaire vérifié.</p></article><article class="card"><h3>Des gestes familiers</h3><p>Mêmes repères visuels que ConvertAir et DocCipher, avec des parcours adaptés à la gestion d'activité.</p></article></div></div></section>
<section class="section alt" id="confidentialite"><div class="container prose"><p class="eyebrow">Confidentialité</p><h2>Une promesse à vérifier avant la sortie.</h2><p>La cible est un traitement local des données métier, avec Google Play et RevenueCat pour les achats. La version en préparation contient encore des fonctions à vérifier ou retirer avant de promettre des connexions limitées aux achats.</p><div class="actions"><a class="button secondary" href="peaksolo-privacy.html">Politique de confidentialité PeakSolo</a></div></div></section>
<section class="section" id="faq"><div class="container faq"><p class="eyebrow">FAQ</p><h2>Avant la sortie.</h2><details class="faq-item"><summary>Quel sera le prix de PeakSolo ?</summary><p>Les offres seront annoncées après leur création et leur vérification dans Google Play. Aucun tarif ni achat groupé n'est proposé ici.</p></details><details class="faq-item"><summary>Où sont les captures de PeakSolo ?</summary><p>Les captures des écrans validés seront ajoutées dans chaque langue. Cette présentation n'utilise pas de faux écran d'application.</p></details><p class="store-pending">Bientôt sur Google Play</p></div></section>'''


def peaksolo_privacy_body(email):
    # Keep the approved French legal original identical on every locale route.
    # Navigation remains localized; the body declares its original language.
    from pathlib import Path
    body = (Path(__file__).parent / 'content' / 'peaksolo-privacy.html').read_text(encoding='utf-8')
    return '<section class="section"><div class="container prose" lang="fr" dir="ltr" data-original-policy="peaksolo-20261118"><p class="meta">Version originale en français · French original</p>' + body + '</div></section>'


SUMMARIES = {
    'convertair-privacy.html': [
        'Vos documents sont traités sur votre téléphone.',
        "Vous choisissez les exports, partages et impressions.",
        "Google Play et RevenueCat gèrent les achats et les vérifications Premium ; aucun document ne leur est envoyé par ces chemins.",
        "Des composants Google Play interviennent dans la capture et les avis ; leurs limites sont détaillées ci-dessous.",
        "Les données d'achat et les statistiques de ventes sont distinctes du contenu de vos documents.",
    ],
    'doccipher-privacy.html': [
        'Vos documents sont conservés dans un coffre chiffré sur votre appareil.',
        "Vous choisissez où exporter vos documents et sauvegardes.",
        "Google Play et RevenueCat gèrent les achats et les vérifications Premium ; aucun document ne leur est envoyé par ces chemins.",
        "Les rappels utilisent des informations limitées hors du coffre, sans titre ni contenu de document.",
        "Les protections d'urgence restent soumises aux validations indiquées dans cette politique.",
    ],
    'privacy.html': [
        "Ce site fonctionne sans compte ni cookie analytique.",
        "Le choix du thème et de la langue reste dans votre navigateur.",
        "Les formulaires testeurs préparent un fichier local, sans envoi automatique.",
        "Si vous nous écrivez, nous recevons les informations que vous choisissez de transmettre.",
        "L'hébergeur peut traiter les données techniques nécessaires à la consultation du site.",
    ],
}


def enrich_policy(body, filename):
    """Add a concise summary and native HTML navigation, preserving every detail."""
    if filename not in SUMMARIES:
        return body
    toc = []
    def heading(match):
        n = len(toc) + 1
        attrs, text = match.groups()
        if 'id=' in attrs:
            return match.group(0)
        key = f'policy-{n:02d}'
        toc.append(f'<li><a href="#{key}">{text}</a></li>')
        return f'<h2{attrs} id="{key}">{text}</h2>'
    # Keep the preserved English appendix and its anchors intact.
    parts = body.split('<div lang="en"', 1)
    parts[0] = re.sub(r'<h2([^>]*)>(.*?)</h2>', heading, parts[0], flags=re.S)
    body = '<div lang="en"'.join(parts)
    summary = '<aside class="privacy-summary"><h2>En bref</h2><ul>' + ''.join(f'<li>{escape(text)}</li>' for text in SUMMARIES[filename]) + '</ul></aside>'
    summary += '<details class="privacy-toc"><summary>Dans cette page</summary><ol>' + ''.join(toc) + '</ol></details>'
    return re.sub(r'(<p class="lede">.*?</p>)', lambda m: m.group(0) + summary, body, count=1, flags=re.S)
