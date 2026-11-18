"""Pinned, first-party HGQ audio used by the progressive web warm-up."""

from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = {
    "assets/audio/hgq/quartier-arcade.ogg": "043a52059b8de84becca0c25f7f892195e41d7d871828d4924896ea9c130d30d",
    "assets/audio/hgq/fight.ogg": "3d299ba3846ce21b08b1b1d29146b94ce6c664250ec4c5fa6f56634f1ef7b05b",
    "assets/audio/hgq/gameover.ogg": "1639ca0ad602063eb23194385431add28cba0a146071ffffd8ce3ba7421e220e",
}
MUSIC_LABEL = "Quartier Arcade"


def validate_assets():
    for name, expected in FILES.items():
        path = ROOT / name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("HGQ_WARMUP_AUDIO_CHANGED=" + name)


def render():
    validate_assets()
    return (
        '<div class="hgq-warmup-audio" hidden aria-hidden="true">'
        '<audio data-warmup-audio="music" data-src="assets/audio/hgq/quartier-arcade.ogg" '
        'preload="none" loop></audio>'
        '<audio data-warmup-audio="fight" data-src="assets/audio/hgq/fight.ogg" '
        'preload="none"></audio>'
        '<audio data-warmup-audio="gameover" data-src="assets/audio/hgq/gameover.ogg" '
        'preload="none"></audio>'
        '</div>'
    )
