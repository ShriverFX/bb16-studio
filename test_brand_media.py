"""Negative tests for localized brand selection and explicit script/region gaps."""
import unittest
import json
import tempfile
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import brand_media as b
import peaksolo_runtime_media as runtime
import site_i18n as i

def nodes(text):return list(i.walk(i.parse(text)))
def rooted(text):
 return text.replace('src="assets/','src="/assets/').replace('poster="assets/','poster="/assets/').replace('href="assets/','href="/assets/')

class BrandMediaLocaleTests(unittest.TestCase):
 def test_english_page_cannot_silently_get_french_video(self):
  text=runtime.render('en') + rooted(b.peaksolo_media_section('en'))
  b.validate_media_nodes(nodes(text),'peaksolo','en')
  with self.assertRaisesRegex(ValueError,'WRONG_SOURCE'):
   b.validate_media_nodes(nodes(text.replace('peaksolo-presentation-en.mp4','peaksolo-presentation-fr.mp4')),'peaksolo','en')

 def test_region_and_script_gaps_are_explicit_links_not_french_fallback(self):
  for locale,destination in [('pt-BR','/pt/peaksolo.html#presentation-video'),('zh-Hant','/zh-Hans/peaksolo.html#presentation-video')]:
   text=runtime.render(locale) + rooted(b.peaksolo_media_section(locale));b.validate_media_nodes(nodes(text),'peaksolo',locale)
   self.assertNotIn('<video',rooted(b.peaksolo_media_section(locale)));self.assertIn(destination,text)
   with self.assertRaisesRegex(ValueError,'EXPLICIT_ALTERNATE'):
    b.validate_media_nodes(nodes(text.replace(destination,'/peaksolo.html#presentation-video')),'peaksolo',locale)

 def test_chinese_simplified_media_keeps_script_identity(self):
  for locale in ('zh','zh-Hans'):
   text=runtime.render(locale) + rooted(b.peaksolo_media_section(locale));self.assertIn('lang="zh-Hans"',text)
   b.validate_media_nodes(nodes(text),'peaksolo',locale)

 def test_hgq_cannot_publish_a_brand_teaser(self):
  with self.assertRaisesRegex(ValueError,'HGQ_RUNTIME_CAPTURE_REQUIRED'):
   b.brand_teaser('hgq','ja')
  text='<video src="/assets/video/brand/hgq-presentation-ja.mp4"></video>'
  with self.assertRaisesRegex(ValueError,'HGQ_RUNTIME_CAPTURE_REQUIRED'):
   b.validate_media_nodes(nodes(text),'hgq','ja')

 def test_all_app_languages_have_product_routes_instead_of_media_only_links(self):
  import app_pages_i18n as app
  self.assertEqual(b.PS_EXTRA_LANGUAGES,())
  text=runtime.render('fr') + rooted(b.peaksolo_media_section('fr'));result=b.validate_media_nodes(nodes(text),'peaksolo')
  self.assertEqual(result['media_only_links'],[])
  self.assertEqual(len([n for n in nodes(text) if n.tag=='video' and n.get('data-peaksolo-runtime') is None]),1)
  self.assertEqual(set(b.PS_PAGE_MEDIA.values()),set(b.APP_LANGUAGES['peaksolo']))
  self.assertTrue(set(b.APP_LANGUAGES['peaksolo']).issubset(app.page_locales('peaksolo')))

 def test_unknown_locale_fails_without_default_french_master(self):
  with self.assertRaises(KeyError):b.brand_teaser('peaksolo','zz')
  with self.assertRaisesRegex(ValueError,'NO_EXPLICIT'):
   b.peaksolo_media_section('unsupported')

 def test_decorate_is_repeatable_from_sources_and_does_not_change_units(self):
  import build_site
  config=build_site.read_config();sources=build_site.pages(config)
  original=i.extract(sources)
  frozen=__import__('json').loads((i.ROOT/'locales/source.json').read_text(encoding='utf-8'))
  self.assertEqual(original,frozen)
  first=i.build(sources,config,preview_locales=['fr','en','ar','pt-BR','zh-Hant'])
  second=i.build(sources,config,preview_locales=['fr','en','ar','pt-BR','zh-Hant'])
  self.assertEqual(first,second)
  for locale in ['fr','en','ar','pt-BR','zh-Hant']:
   name=('' if locale=='fr' else locale+'/')+'peaksolo.html'
   self.assertIn('id="presentation-video"',first[name])
   b.validate_media_nodes(nodes(first[name]),'peaksolo',locale)

class PeakSoloRuntimeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir=i.ROOT)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        root_patch = patch.object(runtime, 'ROOT', self.root)
        self.addCleanup(root_patch.stop)
        root_patch.start()

    def write_capture_fixture(self, count=1):
        # Minimal container headers exercise verification only. They never leave this fixture.
        clips = []
        for index in range(1, count + 1):
            stem = f'runtime-demo-{index}-fr'
            paths = [
                (f'assets/video/peaksolo/{stem}.mp4', b'\x00\x00\x00\x18ftypfixture'),
                (f'assets/screens/peaksolo/{stem}.webp', b'RIFF0000WEBPfixture'),
            ]
            for name, payload in paths:
                target = self.root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            clips.append({
                'title_fr': 'Suivi du solde',
                'title_en': 'Balance overview',
                'video_sha256': sha256(paths[0][1]).hexdigest(),
                'poster_sha256': sha256(paths[1][1]).hexdigest(),
            })
        manifest = self.root / runtime.MANIFEST
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({
            'schema': 1,
            'language': 'fr',
            'media_kind': 'RUNTIME_CAPTURE',
            'synthetic_data': True,
            'clips': clips,
        }), encoding='utf-8')

    def test_no_manifest_hides_section_and_rejects_injected_runtime(self):
        self.assertEqual(runtime.render('fr'), '')
        self.assertEqual(runtime.files(), [])
        b.validate_media_nodes(nodes(rooted(b.peaksolo_media_section('fr'))), 'peaksolo')
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_COMPOSITION_CHANGED'):
            runtime.validate(nodes('<video data-peaksolo-runtime="unverified"></video>'), 'fr', '/')

    def test_verified_runtime_and_brand_players_have_separate_proofs(self):
        self.write_capture_fixture(2)
        self.assertEqual(len(runtime.files()), 4)
        for locale in ('fr', 'en', 'ar', 'pt-BR'):
            with self.subTest(locale=locale):
                text = runtime.render(locale) + rooted(b.peaksolo_media_section(locale))
                b.validate_media_nodes(nodes(text), 'peaksolo', locale)
                self.assertEqual(text.count('data-media-kind="RUNTIME_CAPTURE"'), 2)
                self.assertIn('lang="fr" data-peaksolo-runtime=', text)
                self.assertNotIn('autoplay', text)
                with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_PLAYER_CHANGED'):
                    b.validate_media_nodes(nodes(text.replace('preload="none"', 'preload="auto"', 1)),
                                           'peaksolo', locale)

    def test_media_hash_and_missing_poster_fail_closed(self):
        self.write_capture_fixture()
        poster = self.root / 'assets/screens/peaksolo/runtime-demo-1-fr.webp'
        poster.write_bytes(b'RIFF0000WEBPtampered')
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_MEDIA_INVALID'):
            runtime.render('fr')
        poster.unlink()
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_MEDIA_MISSING'):
            runtime.files()


    def test_public_manifest_refuses_extra_metadata(self):
        self.write_capture_fixture()
        manifest = self.root / runtime.MANIFEST
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['additional_metadata'] = 'fixture'
        manifest.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'PEAKSOLO_RUNTIME_MANIFEST_INVALID'):
            runtime.files()

if __name__=='__main__':unittest.main()
