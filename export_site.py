#!/usr/bin/env python3
"""Assemble and verify the exact static-site publication allowlist."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from build_site import ASSETS as CORE_ASSETS
from product_pages import MEDIA_FILES, RETIRED_MEDIA
from validate_site import validate_custom_domain


SITE = Path(__file__).resolve().parent
ROOT_FILES = (
    "CNAME",
    "app-ads.txt",
    "404.html",
    "apps.html",
    "contact.html",
    "convertair-privacy.html",
    "convertair-test.html",
    "convertair.html",
    "data-deletion.html",
    "doccipher-privacy.html",
    "doccipher-test.html",
    "doccipher.html",
    "google7f580d7c20e79216.html",
    "hgq.html",
    "hgq-privacy.html",
    "hgq-account-deletion.html",
    "index.html",
    "legal.html",
    "privacy.html",
    "product.js",
    "robots.txt",
    "sitemap.xml",
    "studio.html",
    "styles.css",
    "support.html",
    "theme.js",
)
ASSET_FILES = tuple(sorted(set(CORE_ASSETS) | set(MEDIA_FILES)))
ASSET_RULES = {
    "assets/apps": frozenset({".png", ".webp"}),
    "assets/branding": frozenset({".jpg", ".png", ".webp"}),
    "assets/screens": frozenset({".webp"}),
    "assets/video": frozenset({".mp4"}),
}
HTML_LINK = re.compile(r'''(?:href|src|data-src|data-dark|data-light)="([^"]+)"''')
CSS_URL = re.compile(r'''url\(\s*["']?([^"')]+)''', re.IGNORECASE)
CSS_IMPORT = re.compile(
    r'''@import\s+(?:url\(\s*)?["']?([^"')\s;]+)''', re.IGNORECASE
)


def publication_files() -> list[Path]:
    validate_custom_domain(json.loads((SITE / "site.config.json").read_text(encoding="utf-8")))
    relative_names = list(ROOT_FILES) + list(ASSET_FILES)
    retired = sorted(set(relative_names) & RETIRED_MEDIA)
    if retired:
        raise SystemExit("RETIRED_MEDIA_EXPORT=" + ",".join(retired))
    for name in relative_names:
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise SystemExit(f"UNSAFE_EXPORT_ENTRY={name}")
        if relative.parts and relative.parts[0] == "assets":
            folder = "/".join(relative.parts[:2])
            suffixes = ASSET_RULES.get(folder)
            if suffixes is None or relative.suffix.lower() not in suffixes:
                raise SystemExit(f"EXPORT_ASSET_NOT_ALLOWED={name}")
    files = [SITE / Path(*PurePosixPath(name).parts) for name in relative_names]
    missing = [path.relative_to(SITE).as_posix() for path in files if not path.is_file()]
    if missing:
        raise SystemExit("MISSING_EXPORT_FILE=" + ",".join(missing))
    symlinks = [
        path.relative_to(SITE).as_posix()
        for path in files
        if path.is_symlink()
    ]
    if symlinks:
        raise SystemExit("EXPORT_SYMLINK_FORBIDDEN=" + ",".join(symlinks))
    return sorted(set(files), key=lambda path: path.relative_to(SITE).as_posix())


def local_target(
    raw_link: str, base_path: str, source: Path, export_root: Path
) -> Path | None:
    link = html.unescape(raw_link.strip())
    if not link or link.startswith(("#", "mailto:", "tel:", "data:")):
        return None
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc:
        return None
    path = parsed.path
    if "\\" in path:
        raise SystemExit(f"EXPORT_LINK_BACKSLASH={source.name}:{link}")
    if path.startswith(base_path):
        path = path[len(base_path) :]
    elif path.startswith("/"):
        raise SystemExit(f"EXPORT_BAD_ABSOLUTE_LINK={source.name}:{link}")
    else:
        parent = PurePosixPath(source.parent.relative_to(export_root).as_posix())
        path = (parent / path).as_posix()
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise SystemExit(f"EXPORT_LINK_TRAVERSAL={source.name}:{link}")
    if not relative.parts:
        return None
    return Path(*relative.parts)


def css_resource_links(css: str) -> list[str]:
    return sorted(set(CSS_URL.findall(css) + CSS_IMPORT.findall(css)))


def css_local_target(
    raw_link: str, base_path: str, source: Path, export_root: Path
) -> Path | None:
    link = html.unescape(raw_link.strip())
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc or link.startswith("//"):
        raise SystemExit(f"EXPORT_EXTERNAL_CSS_RESOURCE={source.name}:{link}")
    return local_target(link, base_path, source, export_root)


def validate_export(output: Path, expected: list[Path], base_path: str) -> tuple[int, str]:
    expected_names = [path.relative_to(SITE).as_posix() for path in expected]
    actual_names = sorted(
        path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()
    )
    if actual_names != expected_names:
        missing = sorted(set(expected_names) - set(actual_names))
        extra = sorted(set(actual_names) - set(expected_names))
        raise SystemExit(
            "EXPORT_MANIFEST_MISMATCH="
            + json.dumps({"missing": missing, "extra": extra}, ensure_ascii=True)
        )

    checked_links = 0
    for relative_name in actual_names:
        source = output / relative_name
        if source.suffix == ".html":
            links = HTML_LINK.findall(source.read_text(encoding="utf-8"))
        elif source.suffix == ".css":
            links = css_resource_links(source.read_text(encoding="utf-8"))
        else:
            continue
        for link in links:
            if source.suffix == ".css":
                target = css_local_target(link, base_path, source, output)
            else:
                target = local_target(link, base_path, source, output)
            if target is None:
                continue
            checked_links += 1
            candidate = (output / target).resolve()
            try:
                candidate.relative_to(output.resolve())
            except ValueError:
                raise SystemExit(f"EXPORT_LINK_OUTSIDE_ROOT={relative_name}:{link}")
            if not candidate.is_file():
                raise SystemExit(f"EXPORT_BROKEN_LOCAL_LINK={relative_name}:{link}")

    digest = hashlib.sha256()
    for relative_name in actual_names:
        digest.update(relative_name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256((output / relative_name).read_bytes()).digest())
    return checked_links, digest.hexdigest()


def resolve_output(name: str) -> Path:
    """Return the sole allowed disposable export directory."""
    if name != "_site":
        raise SystemExit(f"UNSAFE_EXPORT_OUTPUT={name}")
    output = (SITE / name).resolve()
    if output.parent != SITE or output.name != "_site":
        raise SystemExit(f"UNSAFE_EXPORT_OUTPUT={output}")
    return output


def validate_disposable_output(output: Path, expected: list[Path]) -> None:
    """Refuse to remove an existing _site containing anything unexpected."""
    if not output.exists():
        return
    if not output.is_dir() or output.is_symlink():
        raise SystemExit(f"EXPORT_OUTPUT_NOT_DISPOSABLE={output}")
    expected_names = {path.relative_to(SITE).as_posix() for path in expected}
    expected_dirs = {
        parent.as_posix()
        for name in expected_names
        for parent in PurePosixPath(name).parents
        if parent.as_posix() != "."
    }
    for path in sorted(output.rglob("*")):
        relative = path.relative_to(output).as_posix()
        if path.is_symlink():
            raise SystemExit(f"EXPORT_OUTPUT_NOT_DISPOSABLE={relative}")
        if path.is_dir():
            if relative not in expected_dirs:
                raise SystemExit(f"EXPORT_OUTPUT_NOT_DISPOSABLE={relative}")
        elif relative not in expected_names:
            raise SystemExit(f"EXPORT_OUTPUT_NOT_DISPOSABLE={relative}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="_site",
        help="Répertoire de sortie réservé ; seule la valeur _site est acceptée",
    )
    args = parser.parse_args()

    output = resolve_output(args.output)

    config = json.loads((SITE / "site.config.json").read_text(encoding="utf-8"))
    base_path = str(config.get("base_path", "/"))
    if not base_path.startswith("/") or not base_path.endswith("/"):
        raise SystemExit(f"BAD_BASE_PATH={base_path}")

    files = publication_files()
    validate_disposable_output(output, files)
    if output.exists():
        shutil.rmtree(output)
    for source in files:
        relative = source.relative_to(SITE)
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    checked_links, digest = validate_export(output, files, base_path)
    print(f"EXPORT_ROOT={output}")
    print(f"EXPORTED_FILES={len(files)}")
    print(f"LOCAL_RESOURCE_LINKS={checked_links}")
    print(f"EXPORT_SHA256={digest}")
    print("EXPORT_VALIDATION_OK")


if __name__ == "__main__":
    main()
