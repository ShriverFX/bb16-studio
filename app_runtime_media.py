"""Pinned runtime captures for the standard ConvertAir and DocCipher pages."""

from __future__ import annotations

import json
import re
from hashlib import sha256
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "content/apps-runtime-media.json"
APP_KEYS = frozenset({"convertair", "doccipher"})
CLIP_KEYS = frozenset({
    "id", "media_kind", "capture_environment", "capture_scope", "synthetic_data",
    "language", "source_filename", "source_sha256", "source_review", "video",
    "video_sha256", "poster", "poster_sha256", "width", "height", "duration_seconds",
})


def _manifest() -> dict:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if data.keys() != {"schema", "apps"} or data.get("schema") != 1:
        raise ValueError("APP_RUNTIME_MANIFEST_INVALID")
    if not isinstance(data.get("apps"), dict) or set(data["apps"]) != APP_KEYS:
        raise ValueError("APP_RUNTIME_APPS_INVALID")
    return data


def load(app: str) -> list[dict]:
    if app not in APP_KEYS:
        raise KeyError(app)
    app_data = _manifest()["apps"][app]
    if not isinstance(app_data, dict) or set(app_data) != {"clips"}:
        raise ValueError("APP_RUNTIME_APP_INVALID=" + app)
    clips = app_data.get("clips")
    if not isinstance(clips, list) or len(clips) > 1:
        raise ValueError("APP_RUNTIME_CLIP_COUNT=" + app)
    verified = []
    for clip in clips:
        if not isinstance(clip, dict) or set(clip) != CLIP_KEYS:
            raise ValueError("APP_RUNTIME_CLIP_INVALID=" + app)
        if (not all(isinstance(clip[key], str) and clip[key]
                    for key in CLIP_KEYS - {"synthetic_data", "width", "height", "duration_seconds"})
                or clip["media_kind"] != "RUNTIME_CAPTURE"
                or clip["capture_environment"] not in {"ANDROID_EMULATOR", "ANDROID_DEVICE"}
                or clip["capture_scope"] not in {"REUSED_DEMONSTRATION", "CURRENT_DEMONSTRATION"}
                or clip["synthetic_data"] is not True
                or clip["language"] != "fr"
                or not isinstance(clip["width"], int) or not isinstance(clip["height"], int)
                or clip["width"] <= 0 or clip["height"] <= 0
                or not isinstance(clip["duration_seconds"], (int, float))
                or not 0 < clip["duration_seconds"] <= 30):
            raise ValueError("APP_RUNTIME_PROOF_INVALID=" + app)
        safe_id = re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", clip["id"])
        expected_video = f"assets/video/{app}/runtime-{clip['id']}-fr.mp4"
        expected_poster = f"assets/screens/{app}/runtime-{clip['id']}-fr.webp"
        if (not safe_id
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.mp4", clip["source_filename"])
                or any(not re.fullmatch(r"[0-9a-f]{64}", clip[key])
                       for key in ("source_sha256", "video_sha256", "poster_sha256"))
                or clip["video"] != expected_video
                or clip["poster"] != expected_poster):
            raise ValueError("APP_RUNTIME_PATH_OR_SOURCE_INVALID=" + app)
        for key, hash_key, offset, signature in (
            ("video", "video_sha256", 4, b"ftyp"),
            ("poster", "poster_sha256", 8, b"WEBP"),
        ):
            path = ROOT / clip[key]
            if not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError("APP_RUNTIME_MEDIA_MISSING=" + clip[key])
            payload = path.read_bytes()
            if payload[offset:offset + 4] != signature or sha256(payload).hexdigest() != clip[hash_key]:
                raise ValueError("APP_RUNTIME_MEDIA_INVALID=" + clip[key])
        verified.append(dict(clip))
    return verified


def files() -> list[str]:
    return [clip[key] for app in sorted(APP_KEYS) for clip in load(app) for key in ("video", "poster")]


def render(app: str, aria_label: str, caption: str, *, base: str = "") -> str:
    clips = load(app)
    if not clips:
        return ""
    clip = clips[0]
    player_id = f"{app}-runtime-{clip['id']}"
    return (
        f'<figure class="hero-device app-runtime" data-media-kind="RUNTIME_CAPTURE" '
        f'data-capture-scope="{clip["capture_scope"]}">'
        f'<video src="{base}{clip["video"]}" poster="{base}{clip["poster"]}" controls playsinline '
        f'preload="none" width="{clip["width"]}" height="{clip["height"]}" lang="fr" '
        f'data-app-runtime="{player_id}" aria-label="{escape(aria_label, quote=True)}" '
        f'aria-describedby="{player_id}-caption"></video>'
        f'<figcaption id="{player_id}-caption">{escape(caption)}</figcaption></figure>'
    )


def validate(nodes, app: str, base: str = "") -> None:
    clips = load(app)
    players = [node for node in nodes if node.get("data-app-runtime") is not None]
    figures = [node for node in nodes
               if node.get("data-media-kind") == "RUNTIME_CAPTURE"
               and "app-runtime" in (node.get("class") or "").split()]
    if len(players) != len(clips):
        raise ValueError("APP_RUNTIME_PLAYER_COUNT=" + app)
    if len(figures) != len(clips) or any(
            figure.get("data-capture-scope") != clip["capture_scope"]
            for figure, clip in zip(figures, clips)):
        raise ValueError("APP_RUNTIME_FIGURE_COUNT=" + app)
    for clip in clips:
        player_id = f"{app}-runtime-{clip['id']}"
        matches = [node for node in players if node.get("data-app-runtime") == player_id]
        if len(matches) != 1:
            raise ValueError("APP_RUNTIME_PLAYER_MISSING=" + player_id)
        video = matches[0]
        attrs = dict(video.attrs)
        if (video.get("src") != base + clip["video"]
                or video.get("poster") != base + clip["poster"]
                or video.get("preload") != "none" or video.get("lang") != "fr"
                or video.get("width") != str(clip["width"])
                or video.get("height") != str(clip["height"])
                or not {"controls", "playsinline"} <= attrs.keys()
                or {"autoplay", "loop", "muted"} & attrs.keys()):
            raise ValueError("APP_RUNTIME_PLAYER_INVALID=" + player_id)
