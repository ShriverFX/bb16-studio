#!/usr/bin/env python3
"""Small standard-library validation for the generated static site."""

from __future__ import annotations

import html
import re
import struct
import json
import hashlib
from product_pages import RETIRED_MEDIA
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


SITE = Path(__file__).resolve().parent
PAGES = ["index.html", "studio.html", "apps.html", "convertair.html", "convertair-privacy.html", "doccipher.html", "doccipher-privacy.html", "hgq.html", "hgq-privacy.html", "hgq-account-deletion.html", "support.html", "contact.html", "privacy.html", "legal.html", "data-deletion.html", "404.html"]
FEEDBACK_PAGES = ("convertair-test.html", "doccipher-test.html")
ASSETS = ["assets/branding/convertair-presentation.png", "assets/branding/doccipher-presentation.png", "assets/apps/convertair-icon-512.png", "assets/apps/doccipher-icon-512.png", "assets/branding/bb16-studio-logo.jpg", "assets/apps/hgq-logo.png", "assets/branding/bb16-studio-logo-dark.png"]
ORIGINAL_LOGOS = {
    "assets/branding/bb16-studio-logo.jpg": "ed2f01e3180471184daa5f6513df0a01c489ccd5f0523bca3ca99512e6c6700d",
    "assets/apps/hgq-logo.png": "531f93ab06abc92be87e4f1aaa102271f57c536f05f1f41bc825096e85fe5a9c",
}
# Privacy-policy statements that were once false or missing (site audit and
# round-2 review of 22 September 2026). Each page is bilingual, so both halves
# are pinned.
# The legal-basis/retention/rights phrases below close the P2 found in round 2:
# RevenueCat is contacted even by installs that never bought anything, but
# those three sections used to cover only buyers.
PRIVACY_COMMON_REQUIRED = ["GPA.", "sous-traitant", "processor", "pseudonyme", "pseudonymous", "le pays de votre compte Google Play", "the country of your Google Play account", "contrat d'utilisation de l'application", "performance of the contract for using the app", "modèle de votre appareil", "model of your device", "sans numéro de commande", "no order number needed"]
PRIVACY_REQUIRED = {
    "convertair-privacy.html": PRIVACY_COMMON_REQUIRED + [
        "même si vous n'avez rien acheté",
        "even if you have bought nothing",
        "version Android de ConvertAir annoncée pour Google Play",
        "L'application n'y est pas encore disponible",
        "Android version of ConvertAir announced for Google Play",
        "The app is not available there yet",
        "troisième résultat réussi réellement affiché",
        "jamais faite au démarrage, pendant un traitement, après une erreur ou après un lot partiellement réussi",
        "séparées d'au moins 60 jours",
        "si le service est indisponible ou échoue, l'application reste silencieuse",
        "services Google Play installés sur l'appareil",
        "ConvertAir ne reçoit ni note ni commentaire",
        "Aucun document, image, texte reconnu ou contenu saisi n'est transmis par cet appel",
        "geste manuel séparé",
        "il n'utilise ni le compteur de succès ni le délai de 60 jours",
        "third successful result actually shown",
        "never makes this request at startup, during processing, after an error or after a partially successful batch",
        "at least 60 days apart",
        "if the service is unavailable or fails, the app stays silent",
        "Google Play services installed on the device",
        "ConvertAir receives neither a rating nor a comment",
        "No document, image, recognised text or user-entered content is sent by this call",
        "separate manual gesture",
        "it uses neither the success counter nor the 60-day delay",
    ],
    "doccipher-privacy.html": PRIVACY_COMMON_REQUIRED + [
        "USE_BIOMETRIC",
        "USE_FINGERPRINT",
        "WebDAV or Nextcloud synchronisation is not available",
        "version Android de DocCipher annoncée pour Google Play",
        "L'application n'y est pas encore disponible",
        "Android version of DocCipher announced for Google Play",
        "The app is not available there yet",
        "Code de panique et coffre leurre prévus au lancement",
        "PIN distinct saisi deux fois, deux consentements",
        "confirmation de l'action irréversible",
        "Seule la saisie exacte du PIN de panique armé déclenche ensuite",
        "suppression logique des fichiers, clés locales, caches et miniatures des coffres choisis",
        "ne garantit pas l'écrasement physique du stockage",
        "Les sauvegardes exportées, copies cloud et autres sauvegardes externes ne sont pas supprimées",
        "coffre local séparé, avec son propre PIN, ses propres clés et son propre contenu",
        "documentée publiquement",
        "API officielle Google Play In-App Review",
        "après la protection réussie d'un document ou la réussite d'une sauvegarde",
        "jamais faite au démarrage, pendant un traitement, après un échec ni depuis les écrans de code de panique ou de coffre leurre",
        "délai local d'au moins 90 jours",
        "DocCipher ne reçoit ni la note, ni le commentaire, ni le score",
        "Aucun document, coffre, PIN ou texte saisi ne passe par ce canal",
        "Panic PIN and decoy vault planned for launch",
        "distinct PIN entered twice, two consent steps",
        "confirmation of the irreversible action",
        "Only entering the exact armed panic PIN then triggers",
        "logical deletion of the selected vaults' files, local keys, caches and thumbnails",
        "does not guarantee physical overwriting of storage",
        "Exported backups, cloud copies and other external backups are not deleted",
        "separate local vault with its own PIN, keys and content",
        "publicly documented",
        "official Google Play In-App Review API",
        "after a document has been protected successfully or a backup has completed successfully",
        "never requests a review at startup, during processing, after a failure or from the panic-PIN or decoy-vault screens",
        "local delay of at least 90 days",
        "DocCipher receives neither the rating, the comment nor the score",
        "No document, vault, PIN or user-entered text passes through this channel",
    ],
}
# Technical J0 disclosures; no runtime or contractual assurance is inferred.
PRIVACY_J0_TECHNICAL_REQUIRED = {'convertair-privacy.html': ['Lors de ces traitements documentaires locaux',
                             'During this local document processing',
                             "Le SDK d'achats Android peut demander à Google Block Store",
                             'The Android purchase SDK may ask Google Block Store',
                             "distinct de la sauvegarde des fichiers de l'application",
                             'separate from the disabled backup of app files'],
 'doccipher-privacy.html': ['déclare exactement sept entrées',
                            'declares exactly seven manifest entries',
                            'RECEIVE_BOOT_COMPLETED</code> — reprogrammer les rappels locaux après '
                            'redémarrage',
                            'RECEIVE_BOOT_COMPLETED</code> — reschedule local reminders after a '
                            'restart',
                            'POST_NOTIFICATIONS</code> — afficher les rappels locaux, avec '
                            'autorisation système quand elle est requise',
                            'POST_NOTIFICATIONS</code> — display local reminders, with system '
                            'permission when required',
                            'Rappels locaux et données hors coffre',
                            'Local reminders and data outside the vault',
                            'Il ne contient ni titre de document, ni nom, ni numéro, ni catégorie',
                            'The plan contains no document title, name, number or category',
                            'Aux démarrages suivants, ce repère peut provoquer la configuration du '
                            'SDK',
                            'At later starts, this marker may configure the SDK',
                            'Un repère illisible est traité comme présent',
                            'An unreadable marker is treated as present',
                            'il ne garantit ni une requête à chaque lancement ni une réponse '
                            'réseau',
                            'it guarantees neither a request at every launch nor a network '
                            'response',
                            "Le SDK d'achats Android peut demander à Google Block Store",
                            'The Android purchase SDK may ask Google Block Store',
                            "distinct de la sauvegarde des fichiers de l'application",
                            'separate from the disabled backup of app files']}
for _page, _phrases in PRIVACY_J0_TECHNICAL_REQUIRED.items():
    PRIVACY_REQUIRED[_page].extend(_phrases)

PRIVACY_FORBIDDEN = ["rien, de notre côté", "nothing on our side", "pas à vous", "not to you", "identifiant anonyme", "anonymous identifier", "identifiant d'achat anonyme", "anonymous purchase identifier", "leurs propres politiques", "under their own policies", "supprimant le coffre", "deleting the vault"]
COMING_SOON_PRIVACY_FORBIDDEN = [
    "distribuée sur Google Play",
    "distributed on Google Play",
    "manifeste de la version publiée",
    "published build's manifest",
]


# ---------------------------------------------------------------------------
# Pages produit premium (1er octobre 2026) : notation Store sans parrainage,
# prix décidés, annonce Coming soon bornée, médias légers et différés.
# ---------------------------------------------------------------------------
PRODUCT_PAGES = ["convertair.html", "doccipher.html", "hgq.html"]
HGQ_CANONICAL_BODY_SHA256 = {
    "hgq-privacy.html": "e110dcc065b74dfb5b006869959f0d14600b699279883d074b85eb9e6b66c5fa",
    "hgq-account-deletion.html": "fa2f35888322c626fe38973c818904a331a12926a6f9268c5e5c075c10c37aee",
}


def validate_current_media_and_hgq_legal(texts: dict[str, str]) -> None:
    for page, text in texts.items():
        if any(path in text for path in RETIRED_MEDIA):
            raise SystemExit("RETIRED_MEDIA_REFERENCE=" + page)
    for page, expected in HGQ_CANONICAL_BODY_SHA256.items():
        match = re.search(r"<!-- HGQ_CANONICAL_BEGIN -->(.*?)<!-- HGQ_CANONICAL_END -->", texts[page], re.S)
        if not match or hashlib.sha256(match.group(1).encode("utf-8")).hexdigest() != expected:
            raise SystemExit("HGQ_CANONICAL_BODY_CHANGED=" + page)
    hgq = texts["hgq.html"]
    for link in ("hgq-privacy.html", "hgq-account-deletion.html"):
        if f'href="/{link}"' not in hgq and f'href="{link}"' not in hgq:
            raise SystemExit("HGQ_DEDICATED_LEGAL_LINK_MISSING=" + link)
    if "<video" in hgq:
        raise SystemExit("HGQ_UNATTESTED_VIDEO=hgq.html")

PRODUCT_PRICES = {
    "convertair.html": ["9,99 €", "par mois", "49,99 €", "par an", "119,99 €", "au lancement, puis 159,99 €", "3 opérations par jour"],
    "doccipher.html": ["19,99 €", "paiement unique", "Jusqu'à 15 documents", "Pas d'abonnement"],
    "hgq.html": ["3,99 €", "par mois", "24,99 €", "par an"],
}
# Formulation bornée imposée par la décision DocCipher D-0051.
PANIC_REQUIRED = [
    "Prévu dès le lancement · inclus dans Premium",
    "implémentation locale est en validation",
    "code PIN distinct saisi deux fois, deux consentements",
    "confirmation de l'action irréversible",
    "Seule la saisie exacte du PIN de panique armé déclenche cette action",
    "Vous choisissez certains coffres ou tous les coffres",
    "effacement logique des fichiers, clés locales, caches et miniatures",
    "Effacer les coffres présents sur cet appareil. Vos sauvegardes externes ne sont pas supprimées.",
    "ne promet pas un effacement physique",
    "coffre local séparé, avec son propre PIN, ses propres clés et son propre contenu",
    "La fonction est documentée publiquement",
    "ne garantit pas qu'un observateur ignore son existence",
    "droit Premium à vie inclut ces deux fonctions sans supplément",
]
CONVERTAIR_REVIEW_REQUIRED = [
    "Des services Store bornés",
    "Après un résultat réussi affiché",
    "l'API officielle Google Play peut proposer un avis",
    "Aucun contenu de document ne passe par ces chemins",
]
OVERCLAIM_FORBIDDEN = ["militaire", "military", "déni plausible", "plausible deniability", "effacement définitif", "irrécupérable", "indétectable", "undetectable"]
REFERRAL_FORBIDDEN = ["code parrain", "parrainez", "referral", "?ref=", "&ref=", "utm_", "invitez vos amis", "récompense contre"]
TRACKER_FORBIDDEN = ["googletagmanager", "google-analytics", "gtag(", "fbq(", "plausible.io", "matomo", "hotjar", "clarity.ms", "<iframe"]
CSS_URL = re.compile(r'''url\(\s*["']?([^"')]+)''', re.IGNORECASE)
CSS_IMPORT = re.compile(
    r'''@import\s+(?:url\(\s*)?["']?([^"')\s;]+)''', re.IGNORECASE
)
# Budgets en octets ; le budget initial inclut les logos des pages produit.
VIDEO_MAX = 250_000
PAGE_VIDEOS_MAX = 1_300_000
PAGE_IMAGES_MAX = 600_000
PAGE_INITIAL_MAX = 350_000
HEADER_LOGOS = {"assets/branding/bb16-studio-logo.jpg", "assets/branding/bb16-studio-logo-dark.png",
                "assets/branding/bb16-studio-logo-light-256.webp", "assets/branding/bb16-studio-logo-dark-256.webp"}


def _local(base_path: str, link: str) -> Path:
    return SITE / link[len(base_path):].split("?", 1)[0]


def validate_css_resources(css: str) -> None:
    for link in sorted(set(CSS_URL.findall(css) + CSS_IMPORT.findall(css))):
        parsed = urlsplit(html.unescape(link.strip()))
        if parsed.scheme or parsed.netloc or link.startswith("//"):
            raise SystemExit("EXTERNAL_CSS_RESOURCE=" + link)
        if "\\" in parsed.path:
            raise SystemExit("BAD_CSS_RESOURCE_PATH=" + link)


def validate_products(config: dict, base_path: str) -> None:
    listings = config.get("store_listings") or {}
    for key in ("convertair", "doccipher", "hgq"):
        listing = listings.get(key) or {}
        if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", str(listing.get("package", ""))) or not isinstance(listing.get("published"), bool):
            raise SystemExit(f"BAD_STORE_LISTING={key}")
    for key in ("convertair", "doccipher", "hgq"):
        if listings[key]["published"]:
            raise SystemExit(f"COMING_SOON_MARKED_PUBLISHED={key}")
    # Texte décodé : l'apostrophe échappée (&#x27;) ne doit pas masquer un contrôle.
    texts = {page: html.unescape((SITE / page).read_text(encoding="utf-8")) for page in PAGES}
    all_text = "\n".join(texts.values())
    lowered = all_text.lower()
    for token in REFERRAL_FORBIDDEN + TRACKER_FORBIDDEN:
        if token.lower() in lowered:
            raise SystemExit("FORBIDDEN_REFERRAL_OR_TRACKER=" + token)
    for page, text in texts.items():
        external = re.findall(r'''(?:src|data-src|poster)="(https?:[^"]+)"''', text) + re.findall(r'''<link[^>]+rel="(?:stylesheet|preload|modulepreload)"[^>]+href="(https?:[^"]+)"''', text)
        if external:
            raise SystemExit(f"EXTERNAL_RESOURCE={page}:" + ",".join(external))
    for page in PRODUCT_PAGES + ["index.html"]:
        text = texts[page]
        if 'id="noter"' not in text or "Notez-nous sur le Store" not in text or "pas de parrainage" not in text:
            raise SystemExit(f"MISSING_STORE_RATING={page}")
    for key, listing in listings.items():
        url = f"https://play.google.com/store/apps/details?id={listing['package']}"
        pages_for_key = [f"{key}.html", "index.html"]
        if listing["published"]:
            missing = [p for p in pages_for_key if f'href="{url}"' not in texts[p]]
            if missing:
                raise SystemExit(f"MISSING_STORE_LINK={key}:" + ",".join(missing))
        else:
            if url in all_text:
                raise SystemExit(f"UNPUBLISHED_STORE_LINK={key}")
            if "Bientôt sur Google Play" not in texts[f"{key}.html"]:
                raise SystemExit(f"MISSING_STORE_PENDING={key}")
    for page in ("index.html", "apps.html"):
        for key, name in (("convertair", "ConvertAir"), ("doccipher", "DocCipher")):
            card = re.search(
                rf'<article class="card[^>]*>.*?{name}.*?</article>', texts[page], re.S
            )
            if not card or "Bientôt sur Android" not in card.group(0):
                raise SystemExit(f"MISSING_COMING_SOON={page}:{key}")
    for key in ("convertair", "doccipher"):
        if "Bientôt sur Android" not in texts[f"{key}.html"]:
            raise SystemExit(f"MISSING_PRODUCT_COMING_SOON={key}")
    if "play.google.com/store/apps/details" in all_text and not any(l["published"] for l in listings.values()):
        raise SystemExit("STORE_LINK_WITHOUT_PUBLICATION")
    for page, required in PRODUCT_PRICES.items():
        missing = [phrase for phrase in required if phrase not in texts[page]]
        if missing:
            raise SystemExit(f"MISSING_PRICE={page}:" + "|".join(missing))
    missing_convertair_review = [
        phrase
        for phrase in CONVERTAIR_REVIEW_REQUIRED
        if phrase not in texts["convertair.html"]
    ]
    if missing_convertair_review:
        raise SystemExit(
            "MISSING_CONVERTAIR_REVIEW_CLAIM=" + "|".join(missing_convertair_review)
        )
    for token in OVERCLAIM_FORBIDDEN:
        if token.lower() in lowered:
            raise SystemExit("OVERCLAIM=" + token)
    doccipher = texts["doccipher.html"]
    soon = re.search(r'<section class="section" id="bientot">.*?</section>', doccipher, re.S)
    if not soon or any(phrase not in soon.group(0) for phrase in PANIC_REQUIRED):
        raise SystemExit("MISSING_PANIC_SOON_BLOCK")
    outside = doccipher.replace(soon.group(0), "")
    for match in re.finditer(r"panique|leurre", outside, re.I):
        window = outside[max(0, match.start() - 200): match.end() + 200]
        if not any(guard in window for guard in ("prévus dès le lancement", "validation", "Bientôt")):
            raise SystemExit("PANIC_CLAIMED_AS_AVAILABLE=" + window[:120])
    for page, text in texts.items():
        if page not in {"doccipher.html", "doccipher-privacy.html"} and re.search(r"panique|coffre leurre", text, re.I):
            raise SystemExit("PANIC_OUTSIDE_DOCCIPHER=" + page)
    css = (SITE / "styles.css").read_text(encoding="utf-8")
    validate_css_resources(css)
    script = (SITE / "product.js").read_text(encoding="utf-8")
    if "prefers-reduced-motion" not in css or "prefers-reduced-motion" not in script:
        raise SystemExit("MISSING_REDUCED_MOTION")
    shared = sum((SITE / name).stat().st_size for name in ("styles.css", "theme.js", "product.js"))
    for page in PRODUCT_PAGES:
        text = texts[page]
        if 'class="product-page"' not in text or 'class="product-nav"' not in text:
            raise SystemExit(f"MISSING_PRODUCT_LAYOUT={page}")
        frames = re.findall(r'<div class="phone[^"]*" data-phone><div class="screen">', text)
        all_frames = re.findall(r'<div\b[^>]*\bclass="phone(?:\s[^"]*)?"[^>]*>', text)
        if not frames or len(frames) != len(all_frames):
            raise SystemExit(f"UNSHARED_PHONE_FRAME={page}")
        if "--screen-ratio" in text:
            raise SystemExit(f"APP_DEPENDENT_PHONE_GEOMETRY={page}")
        if f'src="{base_path}product.js?' not in text:
            raise SystemExit(f"MISSING_PRODUCT_SCRIPT={page}")
        videos = re.findall(r"<video[^>]*>", text)
        if page == "hgq.html" and videos:
            raise SystemExit("HGQ_UNATTESTED_VIDEO=" + page)
        if not videos and page != "hgq.html":
            raise SystemExit(f"MISSING_VIDEOS={page}")
        for tag in videos:
            if re.search(r"\ssrc=|autoplay|poster=", tag) or not all(a in tag for a in ('preload="none"', " muted", " playsinline", 'aria-hidden="true"', "data-src=")):
                raise SystemExit(f"BAD_VIDEO_TAG={page}:{tag}")
        video_files = sorted(set(re.findall(r'data-src="([^"]+\.mp4)"', text)))
        video_bytes = 0
        for link in video_files:
            raw = _local(base_path, link).read_bytes()
            if raw[4:8] != b"ftyp":
                raise SystemExit(f"BAD_MP4={link}")
            if len(raw) > VIDEO_MAX:
                raise SystemExit(f"VIDEO_TOO_HEAVY={link}:{len(raw)}")
            video_bytes += len(raw)
        image_bytes = 0
        eager_bytes = 0
        header_bytes = 0
        seen = set()
        for tag in re.findall(r"<img[^>]+>", text):
            link = re.search(r'src="([^"]+)"', tag).group(1)
            rel = link[len(base_path):]
            if link in seen:
                continue
            seen.add(link)
            size = _local(base_path, link).stat().st_size
            if rel.endswith(".webp") and _local(base_path, link).read_bytes()[8:12] != b"WEBP":
                raise SystemExit(f"BAD_WEBP={link}")
            if rel in HEADER_LOGOS:
                header_bytes += size
                continue
            image_bytes += size
            if 'loading="lazy"' not in tag:
                eager_bytes += size
        # Product pages count both local header derivatives in their initial budget.
        initial = len(text.encode("utf-8")) + shared + eager_bytes + header_bytes
        if video_bytes > PAGE_VIDEOS_MAX or image_bytes > PAGE_IMAGES_MAX or initial > PAGE_INITIAL_MAX:
            raise SystemExit(f"PAGE_TOO_HEAVY={page}:initial={initial},images={image_bytes},videos={video_bytes}")
        print(f"WEIGHT {page}: initial={initial} images={image_bytes} videos={video_bytes} ({len(video_files)}) header_logos={header_bytes}")
    print("PRODUCT_PAGES_OK")


class FeedbackMarkup(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, dict(attrs)))


def validate_feedback_markup(text: str, page: str) -> None:
    markup = FeedbackMarkup()
    markup.feed(text)
    robots = [attrs.get("content", "") for tag, attrs in markup.elements
              if tag == "meta" and attrs.get("name") == "robots"]
    if not any(set(value.lower().split(",")) >= {"noindex", "nofollow"}
               for value in robots):
        raise SystemExit(f"FEEDBACK_INDEXING_NOT_DISABLED={page}")
    ids = [attrs["id"] for _, attrs in markup.elements if attrs.get("id")]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"FEEDBACK_DUPLICATE_IDS={page}")
    if not any(tag == "form" for tag, _ in markup.elements):
        raise SystemExit(f"FEEDBACK_FORM_MISSING={page}")
    for tag, attrs in markup.elements:
        if (tag == "form" and attrs.get("action")) or tag == "iframe":
            raise SystemExit(f"FEEDBACK_COLLECTION_FORBIDDEN={page}")
        if tag == "input" and attrs.get("type", "").lower() in {"file", "password"}:
            raise SystemExit(f"FEEDBACK_SENSITIVE_INPUT_FORBIDDEN={page}")
        if (tag == "script" and attrs.get("src")) or (tag == "img" and attrs.get("src")):
            raise SystemExit(f"FEEDBACK_EXTERNAL_RESOURCE_FORBIDDEN={page}")
    if re.search(r"\b(?:fetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon\s*\(|eval\s*\()", text):
        raise SystemExit(f"FEEDBACK_NETWORK_OR_EVAL_FORBIDDEN={page}")
    for css in re.findall(r"<style[^>]*>(.*?)</style>", text, re.DOTALL):
        validate_css_resources(css)


def validate_custom_domain(config: dict) -> None:
    domain = config.get("custom_domain")
    if domain is None:
        return
    if not isinstance(domain, str) or not re.fullmatch(
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", domain
    ):
        raise SystemExit("BAD_CUSTOM_DOMAIN")
    if config.get("site_url") != "https://" + domain or config.get("base_path") != "/":
        raise SystemExit("CUSTOM_DOMAIN_ORIGIN_OR_BASE_MISMATCH")
    try:
        cname = (SITE / "CNAME").read_text(encoding="utf-8")
    except OSError:
        raise SystemExit("CUSTOM_DOMAIN_CNAME_MISSING") from None
    if cname != domain + "\n":
        raise SystemExit("CUSTOM_DOMAIN_CNAME_MISMATCH")


def main() -> None:
    config = json.loads((SITE / "site.config.json").read_text(encoding="utf-8"))
    validate_custom_domain(config)
    site_url = config.get("site_url")
    base_path = config.get("base_path", "/")
    if not base_path.startswith("/") or not base_path.endswith("/"):
        raise SystemExit("BAD_BASE_PATH=" + str(base_path))
    if site_url:
        parsed = urlsplit(site_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/"):
            raise SystemExit("BAD_SITE_URL=" + str(site_url))
    missing = [p for p in PAGES + ASSETS + ["styles.css", "theme.js", "product.js", "sitemap.xml", "robots.txt"] if not (SITE / p).is_file()]
    if missing:
        raise SystemExit("MISSING=" + ",".join(missing))
    validate_current_media_and_hgq_legal({page: (SITE / page).read_text(encoding="utf-8") for page in PAGES})
    bad_links = []
    duplicate_ids = []
    for page in PAGES:
        text = (SITE / page).read_text(encoding="utf-8")
        ids = re.findall(r'\sid="([^"]+)"', text)
        duplicate_ids.extend(f"{page}#{name}" for name in sorted(set(ids)) if ids.count(name) > 1)
        for link in re.findall(r'''(?:href|src|data-src|data-dark|data-light)="([^"#]+)"''', text):
            if link.startswith(("mailto:", "https://", "http://")):
                continue
            if not link.startswith(base_path):
                bad_links.append(f"{page}->unprefixed:{link}")
                continue
            relative = link[len(base_path):].split("?", 1)[0]
            if "\\" in relative:
                bad_links.append(f"{page}->backslash:{link}")
                continue
            target = (SITE / relative).resolve()
            try:
                target.relative_to(SITE.resolve())
            except ValueError:
                bad_links.append(f"{page}->outside:{link}")
                continue
            if not target.is_file():
                bad_links.append(f"{page}->{link}")
        if "styles.css" not in text:
            bad_links.append(f"{page}->styles.css missing")
    if bad_links:
        raise SystemExit("BAD_LINKS=" + ",".join(bad_links))
    if duplicate_ids:
        raise SystemExit("DUPLICATE_IDS=" + ",".join(duplicate_ids))
    doccipher = (SITE / "doccipher.html").read_text(encoding="utf-8")
    doccipher_privacy = (SITE / "doccipher-privacy.html").read_text(encoding="utf-8")
    if f'href="{base_path}doccipher-privacy.html"' not in doccipher:
        raise SystemExit("MISSING_DOCCIPHER_PRIVACY_LINK")
    if "bb16studio@gmail.com" not in doccipher_privacy or "mailto:bb16studio@gmail.com" not in doccipher_privacy:
        raise SystemExit("BAD_DOCCIPHER_PRIVACY_CONTACT")
    if "WebDAV or Nextcloud synchronisation is not available" not in doccipher_privacy:
        raise SystemExit("MISSING_DOCCIPHER_CURRENT_SCOPE")
    for page, required in PRIVACY_REQUIRED.items():
        text = (SITE / page).read_text(encoding="utf-8")
        missing_text = [phrase for phrase in required if phrase not in text]
        if missing_text:
            raise SystemExit(f"MISSING_PRIVACY_TEXT={page}:" + "|".join(missing_text))
        stale_text = [phrase for phrase in PRIVACY_FORBIDDEN if phrase in text]
        if stale_text:
            raise SystemExit(f"FORBIDDEN_PRIVACY_TEXT={page}:" + "|".join(stale_text))
        availability_overclaims = [
            phrase for phrase in COMING_SOON_PRIVACY_FORBIDDEN if phrase in text
        ]
        if availability_overclaims:
            raise SystemExit(
                f"PRIVACY_STORE_AVAILABILITY_OVERCLAIM={page}:"
                + "|".join(availability_overclaims)
            )
    if site_url:
        for page in PAGES:
            text = (SITE / page).read_text(encoding="utf-8")
            expected = site_url.rstrip("/") + base_path + ("" if page == "index.html" else page)
            canonical = re.search(r'<link rel="canonical" href="([^"]+)"', text)
            if not canonical or canonical.group(1) != expected:
                raise SystemExit(f"BAD_CANONICAL={page}:{canonical.group(1) if canonical else 'missing'}")
        if not all(f"<loc>{site_url.rstrip('/')}{base_path}" in (SITE / "sitemap.xml").read_text(encoding="utf-8") for _ in [0]):
            raise SystemExit("BAD_SITEMAP_CANONICAL")
    nested_404 = (SITE / "404.html").read_text(encoding="utf-8")
    if f'href="{base_path}index.html"' not in nested_404 or not re.search(r'href="' + re.escape(base_path + 'styles.css') + r'(?:\?[^\"]*)?"', nested_404):
        raise SystemExit("BAD_NESTED_404_LINKS")
    for asset in ASSETS:
        raw = (SITE / asset).read_bytes()
        if asset in ORIGINAL_LOGOS and hashlib.sha256(raw).hexdigest() != ORIGINAL_LOGOS[asset]:
            raise SystemExit(f"ORIGINAL_LOGO_CHANGED={asset}")
        if asset.endswith(".jpg"):
            if not raw.startswith(b"\xff\xd8\xff"):
                raise SystemExit(f"BAD_JPEG={asset}")
            continue
        if raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
            raise SystemExit(f"BAD_PNG={asset}")
        width, height = struct.unpack(">II", raw[16:24])
        expected = (709, 784) if asset.endswith("hgq-logo.png") else (1254, 1254) if asset.endswith(("presentation.png", "logo-dark.png")) else (512, 512)
        if (width, height) != expected:
            raise SystemExit(f"BAD_DIMENSIONS={asset}:{width}x{height}")
        if asset.endswith("logo-dark.png") and raw[25] != 6:
            raise SystemExit(f"MISSING_RGBA={asset}")
    css = (SITE / "styles.css").read_text(encoding="utf-8")
    if "overflow-x" in css and "overflow-x: hidden" in css:
        raise SystemExit("UNSAFE_HORIZONTAL_CLIP=styles.css")
    all_text = "\n".join((SITE / p).read_text(encoding="utf-8") for p in PAGES)
    unresolved = sorted(set(re.findall(r"\{[A-Za-z_][A-Za-z0-9_]*\}", all_text)))
    if unresolved:
        raise SystemExit("UNRESOLVED_PLACEHOLDERS=" + ",".join(unresolved))
    forbidden = ["BEGIN " + "PRIVATE KEY", "AI" + "za", "service" + "Account", "google-services" + ".json", "key" + ".properties", "shriverfx" + "@gmail.com", "support" + "@hgq.app", "legal" + "@hgq.app", "preuves de release", "phase courante reste ouverte", "URL publique non configurée", "non prouvé"]
    leaked = [token for token in forbidden if token in all_text]
    if leaked:
        raise SystemExit("FORBIDDEN_PUBLIC_TEXT=" + ",".join(leaked))
    validate_products(config, base_path)
    for page in FEEDBACK_PAGES:
        validate_feedback_markup((SITE / page).read_text(encoding="utf-8"), page)
    print("SITE_VALIDATION_OK")
    print(f"PAGES={len(PAGES)}")
    print(f"ASSETS={len(ASSETS)}")
    print("CANONICAL_OK")
    print("NESTED_404_LINKS_OK")
    print("UNIQUE_IDS_OK")
    print("PRIVACY_TEXT_OK")
    print(f"LOCAL_FEEDBACK_PAGES_OK={len(FEEDBACK_PAGES)}")


if __name__ == "__main__":
    main()
