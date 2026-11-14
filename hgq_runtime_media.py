"""Verified French gameplay excerpt from the Android QA application."""

from hashlib import sha256
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIDEO = 'assets/video/hgq/pokemon-solo-fr.mp4'
POSTER = 'assets/screens/hgq/pokemon-solo-fr.webp'
FILES = {
    VIDEO: 'bb4f0acfc4ca12ffd942d969cd0f3c12aaf0c671e205aae651ad71a688c4de1c',
    POSTER: '2c9f588d75381d213a45c1b2745bbbdbd23596a1f77ca891c727a9e6000777d3',
}
CAPTIONS = {
    'fr': 'Partie solo Pokémon sur Android, en français.',
    'en': 'Pokémon solo gameplay on Android, in French.',
    'es': 'Partida individual de Pokémon en Android, en francés.',
    'pt': 'Partida a solo de Pokémon no Android, em francês.',
    'ja': 'Android版のポケモン・ソロプレイ（フランス語）。',
    'ko': '안드로이드 포켓몬 솔로 플레이 영상입니다. 프랑스어로 진행됩니다.',
}


def render(locale):
    caption = escape(CAPTIONS[locale])
    return (
        '<section class="section" id="gameplay"><div class="container">'
        '<figure class="hero-device" data-media-kind="RUNTIME_CAPTURE">'
        f'<video src="{VIDEO}" poster="{POSTER}" controls playsinline '
        'preload="none" width="360" height="640" lang="fr" '
        'aria-describedby="hgq-gameplay-caption" style="max-width:100%;height:auto"></video>'
        f'<figcaption id="hgq-gameplay-caption">{caption}</figcaption>'
        '</figure></div></section>'
    )


def validate(nodes, locale, base):
    videos = [node for node in nodes if node.tag == 'video']
    captures = [node for node in nodes if node.get('data-media-kind')]
    captions = [node for node in nodes if node.get('id') == 'hgq-gameplay-caption']
    if len(videos) != 1 or len(captures) != 1 or len(captions) != 1:
        raise ValueError('HGQ_RUNTIME_CAPTURE_REQUIRED')
    video = videos[0]
    attrs = dict(video.attrs)
    if (captures[0].get('data-media-kind') != 'RUNTIME_CAPTURE'
            or captures[0].tag != 'figure'
            or any(node.tag == 'source' for node in nodes)
            or video.get('src') != base + VIDEO
            or video.get('poster') != base + POSTER
            or video.get('lang') != 'fr'
            or video.get('aria-describedby') != 'hgq-gameplay-caption'
            or video.get('preload') != 'none'
            or not {'controls', 'playsinline'} <= attrs.keys()
            or {'autoplay', 'loop'} & attrs.keys()
            or captions[0].inner() != escape(CAPTIONS[locale])):
        raise ValueError('HGQ_RUNTIME_CAPTURE_REQUIRED')
    for path, expected in FILES.items():
        asset = ROOT / path
        if not asset.is_file() or sha256(asset.read_bytes()).hexdigest() != expected:
            raise ValueError('HGQ_RUNTIME_CAPTURE_HASH_CHANGED=' + path)
