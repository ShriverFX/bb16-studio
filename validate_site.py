#!/usr/bin/env python3
"""Small standard-library validation for the generated static site."""

from __future__ import annotations

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
    missing = [p for p in PAGES + ASSETS + ["styles.css", "theme.js", "sitemap.xml", "robots.txt"] if not (SITE / p).is_file()]
    if missing:
        raise SystemExit("MISSING=" + ",".join(missing))
    bad_links = []
    for page in PAGES:
        text = (SITE / page).read_text(encoding="utf-8")
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
    doccipher = (SITE / "doccipher.html").read_text(encoding="utf-8")
    doccipher_privacy = (SITE / "doccipher-privacy.html").read_text(encoding="utf-8")
    if f'href="{base_path}doccipher-privacy.html"' not in doccipher:
        raise SystemExit("MISSING_DOCCIPHER_PRIVACY_LINK")
    if "bb16studio@gmail.com" not in doccipher_privacy or "mailto:bb16studio@gmail.com" not in doccipher_privacy:
        raise SystemExit("BAD_DOCCIPHER_PRIVACY_CONTACT")
    if "WebDAV or Nextcloud synchronisation is not available" not in doccipher_privacy:
        raise SystemExit("MISSING_DOCCIPHER_CURRENT_SCOPE")
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
    print("SITE_VALIDATION_OK")
    print(f"PAGES={len(PAGES)}")
    print(f"ASSETS={len(ASSETS)}")
    print("CANONICAL_OK")
    print("NESTED_404_LINKS_OK")


if __name__ == "__main__":
    main()
