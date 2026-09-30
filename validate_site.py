#!/usr/bin/env python3
"""Small standard-library validation for the generated static site."""

from __future__ import annotations

import html
import re
import struct
import json
import hashlib
from pathlib import Path
from urllib.parse import urlsplit


SITE = Path(__file__).resolve().parent
PAGES = ["index.html", "studio.html", "apps.html", "convertair.html", "convertair-privacy.html", "doccipher.html", "doccipher-privacy.html", "hgq.html", "support.html", "contact.html", "privacy.html", "legal.html", "data-deletion.html", "404.html"]
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
    "convertair-privacy.html": PRIVACY_COMMON_REQUIRED + ["même si vous n'avez rien acheté", "even if you have bought nothing"],
    "doccipher-privacy.html": PRIVACY_COMMON_REQUIRED + ["USE_BIOMETRIC", "USE_FINGERPRINT", "WebDAV or Nextcloud synchronisation is not available"],
}
PRIVACY_FORBIDDEN = ["rien, de notre côté", "nothing on our side", "pas à vous", "not to you", "identifiant anonyme", "anonymous identifier", "identifiant d'achat anonyme", "anonymous purchase identifier", "leurs propres politiques", "under their own policies", "supprimant le coffre", "deleting the vault"]


# ---------------------------------------------------------------------------
# Pages produit premium (30 septembre 2026) : notation Store sans parrainage,
# prix décidés, honnêteté sur les fonctions à venir, médias légers et différés.
# ---------------------------------------------------------------------------
PRODUCT_PAGES = ["convertair.html", "doccipher.html", "hgq.html"]
PRODUCT_PRICES = {
    "convertair.html": ["9,99 €", "par mois", "49,99 €", "par an", "119,99 €", "au lancement, puis 159,99 €", "3 opérations par jour"],
    "doccipher.html": ["19,99 €", "paiement unique", "Jusqu'à 15 documents", "Pas d'abonnement"],
    "hgq.html": ["3,99 €", "par mois", "24,99 €", "par an"],
}
# Formulation bornée imposée par la décision DocCipher D-0051.
PANIC_REQUIRED = ["Bientôt · inclus dans Premium", "Effacer les coffres présents sur cet appareil. Vos sauvegardes externes ne sont pas supprimées.", "pas encore dans l'application", "il ne promet pas un effacement physique", "ne garantit pas qu'un observateur ignore son existence"]
OVERCLAIM_FORBIDDEN = ["militaire", "military", "déni plausible", "plausible deniability", "effacement définitif", "irrécupérable", "indétectable", "undetectable"]
REFERRAL_FORBIDDEN = ["code parrain", "parrainez", "referral", "?ref=", "&ref=", "utm_", "invitez vos amis", "récompense contre"]
TRACKER_FORBIDDEN = ["googletagmanager", "google-analytics", "gtag(", "fbq(", "plausible.io", "matomo", "hotjar", "clarity.ms", "<iframe"]
# Budgets en octets ; le budget initial inclut les logos des pages produit.
VIDEO_MAX = 250_000
PAGE_VIDEOS_MAX = 1_300_000
PAGE_IMAGES_MAX = 600_000
PAGE_INITIAL_MAX = 350_000
HEADER_LOGOS = {"assets/branding/bb16-studio-logo.jpg", "assets/branding/bb16-studio-logo-dark.png",
                "assets/branding/bb16-studio-logo-light-256.webp", "assets/branding/bb16-studio-logo-dark-256.webp"}


def _local(base_path: str, link: str) -> Path:
    return SITE / link[len(base_path):].split("?", 1)[0]


def validate_products(config: dict, base_path: str) -> None:
    listings = config.get("store_listings") or {}
    for key in ("convertair", "doccipher", "hgq"):
        listing = listings.get(key) or {}
        if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", str(listing.get("package", ""))) or not isinstance(listing.get("published"), bool):
            raise SystemExit(f"BAD_STORE_LISTING={key}")
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
    if "play.google.com/store/apps/details" in all_text and not any(l["published"] for l in listings.values()):
        raise SystemExit("STORE_LINK_WITHOUT_PUBLICATION")
    for page, required in PRODUCT_PRICES.items():
        missing = [phrase for phrase in required if phrase not in texts[page]]
        if missing:
            raise SystemExit(f"MISSING_PRICE={page}:" + "|".join(missing))
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
        if not any(guard in window for guard in ("dès leur sortie", "Pas encore", "Bientôt")):
            raise SystemExit("PANIC_CLAIMED_AS_AVAILABLE=" + window[:120])
    for page, text in texts.items():
        if page != "doccipher.html" and re.search(r"panique|coffre leurre", text, re.I):
            raise SystemExit("PANIC_OUTSIDE_DOCCIPHER=" + page)
    css = (SITE / "styles.css").read_text(encoding="utf-8")
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
        if not videos:
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


def main() -> None:
    config = json.loads((SITE / "site.config.json").read_text(encoding="utf-8"))
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
    bad_links = []
    duplicate_ids = []
    for page in PAGES:
        text = (SITE / page).read_text(encoding="utf-8")
        ids = re.findall(r'\sid="([^"]+)"', text)
        duplicate_ids.extend(f"{page}#{name}" for name in sorted(set(ids)) if ids.count(name) > 1)
        for link in re.findall(r'''(?:href|src)="([^"#]+)"''', text):
            if link.startswith(("mailto:", "https://", "http://")):
                continue
            if not link.startswith(base_path):
                bad_links.append(f"{page}->unprefixed:{link}")
                continue
            relative = link[len(base_path):].split("?", 1)[0]
            target = (SITE / relative).resolve()
            if not str(target).startswith(str(SITE.resolve())) or not target.is_file():
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
    print("SITE_VALIDATION_OK")
    print(f"PAGES={len(PAGES)}")
    print(f"ASSETS={len(ASSETS)}")
    print("CANONICAL_OK")
    print("NESTED_404_LINKS_OK")
    print("UNIQUE_IDS_OK")
    print("PRIVACY_TEXT_OK")


if __name__ == "__main__":
    main()
