#!/usr/bin/env python3
"""Fabrique les captures WebP et les vidéos MP4 des pages produit.

À lancer volontairement sur la machine source (dépôts des apps voisins),
comme `build_site.py --import-assets`. Dépendances : Pillow et ffmpeg.
Les dépôts des apps sont seulement LUS. La génération du site et la CI n'ont
pas besoin de ce script : elles utilisent les fichiers produits, versionnés.

    python .\\make_media.py            # tout régénérer
    python .\\make_media.py --check    # vérifier la présence des sources
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

import product_pages as P

FPS = 30
SEGMENT_SECONDS = 3.4
FADE_SECONDS = 0.7
ZOOM = {"scroll": 1.12, "drift": 1.06}

# Les captures HGQ de développement montrent les indicateurs de toucher
# d'Android (disques gris). On les efface, sans rien changer d'autre à
# l'écran : chaque disque est rempli par interpolation horizontale entre
# ses bords, sur des fonds unis. (centre x, centre y, rayon, recentrer,
# dernière ligne touchée ou None), en pixels de la capture source.
TOUCH_DOTS = {
    "21-28-33-109": [(726, 1882, 54, True, None), (264, 2014, 54, True, None), (495, 1886, 48, False, 1922)],
    "22-06-05-486": [(540, 1678, 54, True, None), (306, 1840, 54, True, None)],
    "22-08-11-253": [(378, 2086, 54, True, None), (600, 1870, 54, True, None), (786, 1852, 54, True, None)],
}


def recentre(px, size, cx: int, cy: int, win: int = 80) -> tuple[int, int]:
    width, height = size
    samples = []
    for y in range(max(0, cy - win), min(height, cy + win), 2):
        for x in range(max(0, cx - win), min(width, cx + win), 2):
            r, g, b = px[x, y]
            samples.append((x, y, (r + g + b) / 3, max(r, g, b) - min(r, g, b)))
    base = sorted(v[2] for v in samples)[len(samples) // 4]
    points = [(x, y) for x, y, mean, sat in samples if sat < 20 and base + 18 < mean < base + 110]
    if len(points) < 50:
        return cx, cy
    return sum(p[0] for p in points) // len(points), sum(p[1] for p in points) // len(points)


def erase_touch_dots(image: Image.Image, source: Path) -> Image.Image:
    dots = next((v for k, v in TOUCH_DOTS.items() if k in source.name), None)
    if not dots:
        return image
    px = image.load()
    for cx, cy, radius, refine, ymax in dots:
        if refine:
            cx, cy = recentre(px, image.size, cx, cy)
        last = cy + radius if ymax is None else min(cy + radius, ymax)
        for y in range(cy - radius, last + 1):
            dx = int((radius * radius - (y - cy) ** 2) ** 0.5)
            x0, x1 = cx - dx - 8, cx + dx + 8
            left, right = px[x0, y], px[x1, y]
            for x in range(cx - dx, cx + dx + 1):
                t = (x - x0) / (x1 - x0)
                px[x, y] = tuple(int(left[i] * (1 - t) + right[i] * t) for i in range(3))
    return image


def load_screen(key: str) -> Image.Image:
    app, source = P.SCREENS[key]
    top, bottom = P.APP_SCREEN[app]["crop"]
    image = Image.open(source).convert("RGB")
    if image.size != P.APP_SCREEN[app]["source_size"]:
        raise SystemExit(f"TAILLE_SOURCE_INATTENDUE={source}:{image.size}")
    image = erase_touch_dots(image, source)
    w, h = image.size
    return image.crop((0, top, w, h - bottom))


def make_screen(key: str) -> None:
    app, _ = P.SCREENS[key]
    target = P.SITE / key
    target.parent.mkdir(parents=True, exist_ok=True)
    image = load_screen(key).resize(P.screen_size(app, P.SCREEN_WIDTH), Image.LANCZOS)
    image.save(target, "WEBP", quality=80, method=6)


def make_video(key: str, segments: list[tuple[str, str]], ffmpeg: str, tmp: Path) -> None:
    app = P.SCREENS[segments[0][0]][0]
    out_w, out_h = P.screen_size(app, P.VIDEO_WIDTH)
    # Travail en 2x puis réduction : le défilement reste fluide (demi-pixel).
    work_w, work_h = out_w * 2, out_h * 2
    args = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    filters = []
    for index, (screen_key, mode) in enumerate(segments):
        zoom = ZOOM[mode]
        base = load_screen(screen_key)
        scaled_w = int(round(work_w * zoom / 2) * 2)
        scaled_h = int(round(base.height * scaled_w / base.width / 2) * 2)
        frame = tmp / f"{Path(key).stem}-{index}.png"
        base.resize((scaled_w, scaled_h), Image.LANCZOS).save(frame)
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{SEGMENT_SECONDS}", "-i", str(frame)]
        ease = f"(0.5-0.5*cos(PI*t/{SEGMENT_SECONDS}))"
        filters.append(
            f"[{index}:v]crop=w={work_w}:h={work_h}:x=(iw-ow)/2:y=(ih-oh)*{ease},"
            f"scale={out_w}:{out_h}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p[s{index}]"
        )
    last = "s0"
    for index in range(1, len(segments)):
        offset = index * (SEGMENT_SECONDS - FADE_SECONDS)
        filters.append(f"[{last}][s{index}]xfade=transition=fade:duration={FADE_SECONDS}:offset={offset:.2f}[x{index}]")
        last = f"x{index}"
    target = P.SITE / key
    target.parent.mkdir(parents=True, exist_ok=True)
    args += [
        "-filter_complex", ";".join(filters), "-map", f"[{last}]",
        "-c:v", "libx264", "-preset", "veryslow", "-crf", "31", "-profile:v", "main",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", "-map_metadata", "-1", str(target),
    ]
    subprocess.run(args, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    missing = [str(src) for _, src in P.SCREENS.values() if not src.is_file()]
    if missing:
        raise SystemExit("SOURCES_ABSENTES=" + ",".join(missing))
    if args.check:
        print(f"SOURCES_OK={len(P.SCREENS)}")
        return
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("FFMPEG_ABSENT")
    for key in P.SCREENS:
        make_screen(key)
    for key, (source, size) in P.ICONS.items():
        Image.open(P.SITE / source).convert("RGBA").resize(size, Image.LANCZOS).save(P.SITE / key, "WEBP", quality=88, method=6)
    with tempfile.TemporaryDirectory(prefix="bb16-media-") as tmp:
        for key, segments in P.VIDEOS.items():
            make_video(key, segments, ffmpeg, Path(tmp))
    for key in P.MEDIA_FILES:
        print(f"{(P.SITE / key).stat().st_size:>8} {key}")


if __name__ == "__main__":
    main()
