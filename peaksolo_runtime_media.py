"""Verified Android QA recordings for the PeakSolo product pages."""

import json
from hashlib import sha256
from html import escape
from pathlib import Path

from site_i18n import walk

ROOT = Path(__file__).resolve().parent
MANIFEST = 'content/peaksolo-runtime-media.json'
SECTION_ID = 'peaksolo-runtime'
MANIFEST_KEYS = {'schema', 'language', 'media_kind', 'synthetic_data', 'clips'}
CLIP_KEYS = {'title_fr', 'title_en', 'video_sha256', 'poster_sha256'}

def load():
    manifest = ROOT / MANIFEST
    if not manifest.exists():
        return []
    data = json.loads(manifest.read_text(encoding='utf-8'))
    if (not isinstance(data, dict)
            or data.keys() != MANIFEST_KEYS
            or data.get('schema') != 1
            or data.get('language') != 'fr'
            or data.get('media_kind') != 'RUNTIME_CAPTURE'
            or data.get('synthetic_data') is not True):
        raise ValueError('PEAKSOLO_RUNTIME_MANIFEST_INVALID')
    clips = data.get('clips')
    if not isinstance(clips, list) or not 1 <= len(clips) <= 2:
        raise ValueError('PEAKSOLO_RUNTIME_CLIP_COUNT')

    verified = []
    for index, clip in enumerate(clips, 1):
        if (not isinstance(clip, dict) or clip.keys() != CLIP_KEYS
                or not all(isinstance(clip.get(key), str) and 1 <= len(clip[key].strip()) <= 96
                           for key in ('title_fr', 'title_en'))):
            raise ValueError('PEAKSOLO_RUNTIME_CLIP_INVALID')
        stem = f'runtime-demo-{index}-fr'
        video = f'assets/video/peaksolo/{stem}.mp4'
        poster = f'assets/screens/peaksolo/{stem}.webp'
        for path, key, offset, signature in (
            (video, 'video_sha256', 4, b'ftyp'), (poster, 'poster_sha256', 8, b'WEBP'),
        ):
            asset = ROOT / path
            if not asset.is_file() or not asset.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError('PEAKSOLO_RUNTIME_MEDIA_MISSING=' + path)
            payload = asset.read_bytes()
            if (sha256(payload).hexdigest() != clip.get(key)
                    or payload[offset:offset + 4] != signature):
                raise ValueError('PEAKSOLO_RUNTIME_MEDIA_INVALID=' + path)
        verified.append({**clip, 'id': f'peaksolo-{stem}', 'video': video, 'poster': poster})
    return verified


def files():
    return [clip[key] for clip in load() for key in ('video', 'poster')]


def copy_for(locale):
    if locale == 'en':
        return 'en', 'PeakSolo on Android', 'French Android recording with sample data.'
    return 'fr', 'PeakSolo sur Android', 'Capture Android en français avec des données fictives.'


def caption(clip, locale):
    lang, _, note = copy_for(locale)
    return escape(f'{clip[f"title_{lang}"].strip()}. {note}', quote=False)


def render(locale):
    clips = load()
    if not clips:
        return ''
    lang, heading, _ = copy_for(locale)
    figures = ''.join(
        '<figure class="hero-device" data-media-kind="RUNTIME_CAPTURE">'
        f'<video src="/{clip["video"]}" poster="/{clip["poster"]}" controls playsinline '
        'preload="none" width="360" height="640" lang="fr" '
        f'data-peaksolo-runtime="{clip["id"]}" aria-describedby="{clip["id"]}-caption" '
        'style="max-width:100%;height:auto"></video>'
        f'<figcaption id="{clip["id"]}-caption">{caption(clip, locale)}</figcaption></figure>'
        for clip in clips
    )
    return (
        f'<section class="section" id="{SECTION_ID}" aria-labelledby="{SECTION_ID}-title" lang="{lang}" dir="ltr">'
        f'<div class="container"><h2 id="{SECTION_ID}-title">{heading}</h2>'
        '<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:24px">'
        f'{figures}</div></div></section>'
    )


def validate(nodes, locale, base):
    clips = load()
    videos = [node for node in nodes if node.get('data-peaksolo-runtime') is not None]
    figures = [node for node in nodes if node.get('data-media-kind') == 'RUNTIME_CAPTURE']
    sections = [node for node in nodes if node.get('id') == SECTION_ID]
    if len(videos) != len(clips) or len(figures) != len(clips) or len(sections) != (1 if clips else 0):
        raise ValueError('PEAKSOLO_RUNTIME_COMPOSITION_CHANGED')
    if not clips:
        return
    members = list(walk(sections[0]))
    lang, heading, _ = copy_for(locale)
    titles = [node for node in members if node.get('id') == SECTION_ID + '-title']
    if (sections[0].tag != 'section' or sections[0].get('lang') != lang
            or sections[0].get('dir') != 'ltr'
            or sections[0].get('aria-labelledby') != SECTION_ID + '-title'
            or len(titles) != 1 or titles[0].tag != 'h2' or titles[0].inner() != heading
            or any(not any(item is node for item in members) for node in [*figures, *videos])):
        raise ValueError('PEAKSOLO_RUNTIME_SECTION_CHANGED')
    for clip, figure, video in zip(clips, figures, videos):
        captions = [node for node in walk(figure) if node.tag == 'figcaption']
        attrs = dict(video.attrs)
        if (figure.tag != 'figure' or video.tag != 'video'
                or not any(item is video for item in figure.children)
                or video.get('data-peaksolo-runtime') != clip['id']
                or video.get('src') != base + clip['video']
                or video.get('poster') != base + clip['poster']
                or video.get('lang') != 'fr' or video.get('preload') != 'none'
                or video.get('width') != '360' or video.get('height') != '640'
                or video.get('aria-describedby') != clip['id'] + '-caption'
                or not {'controls', 'playsinline'} <= attrs.keys()
                or {'autoplay', 'loop', 'data-src'} & attrs.keys()
                or len(captions) != 1 or captions[0].get('id') != clip['id'] + '-caption'
                or captions[0].inner() != caption(clip, locale)):
            raise ValueError('PEAKSOLO_RUNTIME_PLAYER_CHANGED=' + clip['id'])
