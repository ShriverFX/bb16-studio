"""Fail-closed tests for the two attested PeakSolo Android captures."""

import json
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import brand_media as brand
import peaksolo_runtime_media as runtime
import site_i18n as i


def nodes(text):
    return list(i.walk(i.parse(text)))


class PeakSoloRuntimeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir=i.ROOT)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        root_patch = patch.object(runtime, 'ROOT', self.root)
        self.addCleanup(root_patch.stop)
        root_patch.start()

    def write_capture_fixture(self, count=2):
        """Minimal container headers exercise byte verification only."""
        clips = []
        for index in range(1, count + 1):
            stem = f'runtime-demo-{index}-fr'
            paths = [
                (f'assets/video/peaksolo/{stem}.mp4', b'\x00\x00\x00\x18ftypfixture' + bytes([index])),
                (f'assets/screens/peaksolo/{stem}.webp', b'RIFF0000WEBPfixture' + bytes([index])),
            ]
            for name, payload in paths:
                target = self.root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            clips.append({
                'title_fr': f'Capture réelle {index}',
                'title_en': f'Real capture {index}',
                'video_sha256': sha256(paths[0][1]).hexdigest(),
                'poster_sha256': sha256(paths[1][1]).hexdigest(),
            })
        manifest = self.root / runtime.MANIFEST
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({
            'schema': 1,
            'language': 'fr',
            'media_kind': 'RUNTIME_CAPTURE',
            'synthetic_data': True,
            'clips': clips,
        }), encoding='utf-8')

    def composition(self, locale='fr'):
        return runtime.hero_player(locale) + runtime.render(locale)

    def test_exactly_two_runtime_players_each_appear_once(self):
        self.write_capture_fixture()
        self.assertEqual(len(runtime.files()), 4)
        for locale in ('fr', 'en', 'ar', 'pt-BR', 'zh-Hant'):
            with self.subTest(locale=locale):
                hero = runtime.hero_player(locale)
                section = runtime.render(locale)
                text = hero + section
                result = brand.validate_media_nodes(nodes(text), 'peaksolo', locale)
                self.assertEqual(result, {'player_locales': ['fr'], 'media_only_links': []})
                self.assertEqual(text.count('data-media-kind="RUNTIME_CAPTURE"'), 2)
                self.assertEqual(text.count('data-peaksolo-runtime='), 2)
                self.assertIn('peaksolo-runtime-demo-1-fr', hero)
                self.assertNotIn('peaksolo-runtime-demo-2-fr', hero)
                self.assertNotIn('peaksolo-runtime-demo-1-fr', section)
                self.assertIn('peaksolo-runtime-demo-2-fr', section)
                self.assertIn('lang="fr" data-peaksolo-runtime=', text)
                self.assertNotIn('autoplay', text)
                self.assertNotIn('BRAND_TEASER', text)
                self.assertNotIn('presentation-video', text)

    def test_injection_preserves_hero_copy_and_places_first_player_on_right(self):
        self.write_capture_fixture()
        tree = i.parse(
            '<main><section class="product-hero planned-product" id="presentation">'
            '<div class="container"><div class="peaksolo-identity" data-reveal><img src="/logo.webp" alt=""></div>'
            '<p class="eyebrow">Suite BB16</p><h1>Titre légal</h1>'
            '<p class="hero-status"><span>En préparation</span></p>'
            '<p>Disponibilité non annoncée.</p><div class="actions">'
            '<a href="#fonctions">Projet</a><a href="/support.html">Support</a>'
            '</div></div></section><section class="section" id="presentation-video">'
            '<figure class="hero-device brand-teaser" data-media-kind="BRAND_TEASER"></figure>'
            '</section><section id="fonctions"><p>Après</p></section></main>'
        )
        container = next(node for node in i.walk(tree) if node.get('class') == 'container')
        original = container.inner()
        brand.inject_peaksolo(tree, 'fr')
        hero = next(node for node in i.walk(tree) if node.get('id') == 'presentation')
        container = next(node for node in hero.children if isinstance(node, i.Node))
        self.assertEqual(container.get('class'), 'container product-hero-grid')
        self.assertEqual(len(container.children), 2)
        copy, player = container.children
        self.assertEqual(copy.get('class'), 'product-hero-copy')
        self.assertEqual(copy.inner(), original.replace(' data-reveal', ''))
        identity = next(node for node in i.walk(copy) if node.get('class') == 'peaksolo-identity')
        self.assertIsNone(identity.get('data-reveal'))
        self.assertEqual(player.tag, 'figure')
        self.assertEqual(player.get('class'), 'hero-device')
        main = next(node for node in i.walk(tree) if node.tag == 'main')
        self.assertEqual([node.get('id') for node in main.children],
                         ['presentation', runtime.SECTION_ID, 'fonctions'])
        rendered = i.render(tree)
        self.assertEqual(rendered.count('data-peaksolo-runtime='), 2)
        self.assertNotIn('presentation-video', rendered)
        self.assertNotIn('brand-teaser', rendered)
        brand.validate_media_nodes(list(i.walk(tree)), 'peaksolo', 'fr')

    def test_all_peaksolo_locale_layouts_include_rtl_and_runtime_only(self):
        import app_pages_i18n as app

        self.write_capture_fixture()
        locales = app.page_locales('peaksolo')
        self.assertEqual(len(locales), 31)
        self.assertEqual(brand.language_tag('zh'), 'zh-Hans')
        self.assertEqual({code for code in locales if brand.direction(code) == 'rtl'},
                         {'ar', 'he', 'fa', 'ur'})
        for locale in locales:
            with self.subTest(locale=locale):
                tree = i.parse(
                    f'<html lang="{locale}" dir="{brand.direction(locale)}"><body><main>'
                    '<section class="product-hero planned-product" id="presentation">'
                    '<div class="container"><div class="peaksolo-identity" data-reveal>'
                    '<img src="/logo.webp" alt=""></div><h1>PeakSolo</h1>'
                    '<p>Statut conservé.</p><a href="/support.html">Support</a></div></section>'
                    '</main></body></html>'
                )
                brand.inject_peaksolo(tree, locale)
                all_nodes = list(i.walk(tree))
                html = next(node for node in all_nodes if node.tag == 'html')
                hero_grid = next(node for node in all_nodes
                                 if node.get('class') == 'container product-hero-grid')
                brand.validate_media_nodes(all_nodes, 'peaksolo', locale)
                self.assertEqual(html.get('dir'), brand.direction(locale))
                self.assertEqual(len(hero_grid.children), 2)
                rendered = i.render(tree)
                self.assertEqual(rendered.count('data-peaksolo-runtime='), 2)
                self.assertNotIn('BRAND_TEASER', rendered)
                self.assertNotIn('data-reveal', rendered)

    def test_brand_teasers_and_unattested_video_are_rejected(self):
        self.write_capture_fixture()
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_CAPTURE_REQUIRED'):
            brand.brand_teaser('peaksolo', 'fr')
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_CAPTURE_REQUIRED'):
            brand.peaksolo_media_section('fr')
        old = '<video src="/assets/video/brand/peaksolo-presentation-fr.mp4"></video>'
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_CAPTURE_REQUIRED'):
            brand.validate_media_nodes(nodes(self.composition() + old), 'peaksolo', 'fr')
        extra = '<video src="/unattested.mp4"></video>'
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_UNATTESTED_VIDEO'):
            brand.validate_media_nodes(nodes(self.composition() + extra), 'peaksolo', 'fr')

    def test_missing_or_partial_manifest_fails_closed(self):
        self.assertEqual(runtime.hero_player('fr'), '')
        self.assertEqual(runtime.render('fr'), '')
        self.assertEqual(runtime.files(), [])
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_COMPOSITION_CHANGED'):
            brand.validate_media_nodes(nodes(''), 'peaksolo', 'fr')
        self.write_capture_fixture(count=1)
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_CLIP_COUNT'):
            runtime.load()

    def test_playback_attributes_hashes_and_manifest_schema_fail_closed(self):
        self.write_capture_fixture()
        changed = self.composition().replace('preload="none"', 'preload="auto"', 1)
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_PLAYER_CHANGED'):
            brand.validate_media_nodes(nodes(changed), 'peaksolo', 'fr')

        poster = self.root / 'assets/screens/peaksolo/runtime-demo-1-fr.webp'
        poster.write_bytes(b'RIFF0000WEBPtampered')
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_MEDIA_INVALID'):
            runtime.render('fr')

        self.write_capture_fixture()
        manifest = self.root / runtime.MANIFEST
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['additional_metadata'] = 'fixture'
        manifest.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_MANIFEST_INVALID'):
            runtime.files()


if __name__ == '__main__':
    unittest.main()
