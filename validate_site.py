#!/usr/bin/env python3
"""Small standard-library validation for the generated static site."""

from __future__ import annotations

import re
import struct
import json
from pathlib import Path
from urllib.parse import urlsplit


SITE = Path(__file__).resolve().parent
PAGES = ["index.html", "studio.html", "apps.html", "convertair.html", "doccipher.html", "hgq.html", "support.html", "contact.html", "privacy.html", "legal.html", "data-deletion.html", "404.html"]
ASSETS = ["assets/branding/convertair-presentation.png", "assets/branding/doccipher-presentation.png", "assets/apps/convertair-icon-512.png", "assets/apps/doccipher-icon-512.png"]


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
    missing = [p for p in PAGES + ASSETS + ["styles.css", "sitemap.xml", "robots.txt"] if not (SITE / p).is_file()]
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
    if f'href="{base_path}index.html"' not in nested_404 or f'href="{base_path}styles.css"' not in nested_404:
        raise SystemExit("BAD_NESTED_404_LINKS")
    for asset in ASSETS:
        raw = (SITE / asset).read_bytes()
        if raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
            raise SystemExit(f"BAD_PNG={asset}")
        width, height = struct.unpack(">II", raw[16:24])
        expected = (1254, 1254) if asset.endswith("presentation.png") else (512, 512)
        if (width, height) != expected:
            raise SystemExit(f"BAD_DIMENSIONS={asset}:{width}x{height}")
    css = (SITE / "styles.css").read_text(encoding="utf-8")
    if "overflow-x" in css and "overflow-x: hidden" in css:
        raise SystemExit("UNSAFE_HORIZONTAL_CLIP=styles.css")
    all_text = "\n".join((SITE / p).read_text(encoding="utf-8") for p in PAGES)
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
