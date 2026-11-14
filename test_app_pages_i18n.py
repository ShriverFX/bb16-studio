"""Source/catalogue boundary tests; no server or app SDK required."""
import copy
import json
import unittest
from unittest.mock import patch
import app_pages_i18n as app
import brand_media as media
import build_site
import site_i18n as i

class SparseProductCatalogueTests(unittest.TestCase):
    def test_routes_are_only_actual_app_languages_and_preserved_variants(self):
        self.assertEqual(set(app.page_locales('hgq')),set(media.APP_LANGUAGES['hgq']))
        self.assertEqual(set(app.page_locales('peaksolo')),set(media.APP_LANGUAGES['peaksolo'])|{'pt-BR','zh-Hans','zh-Hant'})
        self.assertEqual(len(app.extra_files()),14)
        self.assertEqual(len(set(app.extra_files())),14)
        self.assertFalse(any('privacy' in name or 'legal' in name or 'index' in name for name in app.extra_files()))
        self.assertFalse(app.available('he','peaksolo-privacy.html'))
        self.assertTrue(app.available('he','peaksolo.html'))
        self.assertFalse(app.available('de','hgq.html'))

    def test_complete_catalogues_and_no_global_catalogue_expansion(self):
        config=build_site.read_config();sources=build_site.pages(dict(config,base_path='/'))
        frozen=json.loads((i.ROOT/'locales/source.json').read_text(encoding='utf-8'))
        self.assertEqual(i.extract(sources),frozen)
        self.assertEqual(len(i.LOCALES),22)
        self.assertEqual(len(i.PAGES),14)
        units=app.frozen_sources(sources)
        for key in ('hgq','peaksolo'):
            for locale in app.page_locales(key):
                if locale=='fr':continue
                with self.subTest(app=key,locale=locale):
                    data=app.catalogue(key,locale,units[key])
                    self.assertEqual(set(data),set(units[key]))
                    self.assertTrue(app.ui(locale)['language'])

    def test_scoped_validation_rejects_missing_empty_changed_link_number_and_french(self):
        units={'one':{'source':'Lire <a href="/privacy.html">la politique</a>.','markup':True}}
        good={'one':'Read <a href="/privacy.html">the policy</a>.'}
        app.validate_values('en',good,units)
        for value,error in [({},'KEYS'),({'one':''},'EMPTY'),({'one':good['one'].replace('/privacy.html','https://example.org')},'MARKUP')]:
            with self.subTest(error=error),self.assertRaisesRegex(ValueError,error):app.validate_values('en',value,units)
        number={'one':{'source':'© 2026 BB16 Studio','markup':False}}
        with self.assertRaisesRegex(ValueError,'NUMBER'):app.validate_values('en',{'one':'© 2027 BB16 Studio'},number)
        source='Cette présentation du projet décrit les limites de votre application avant sa publication officielle.'
        with self.assertRaisesRegex(ValueError,'UNTRANSLATED'):
            app.validate_values('en',{'one':source},{'one':{'source':source,'markup':False}})

    def test_source_and_unknown_locale_fail_closed(self):
        config=build_site.read_config();sources=build_site.pages(dict(config,base_path='/'))
        changed=dict(sources);changed['peaksolo.html']=changed['peaksolo.html'].replace('Un projet, trois repères.','Un projet modifié sans revue.')
        with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):app.frozen_sources(changed)
        with self.assertRaisesRegex(ValueError,'UNKNOWN_APP'):app.page_locales('other')
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_APP_PAGE'):
            app.render('hgq','de',sources,config,{})

class SparseProductRouteMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=build_site.read_config()
        sources=build_site.pages(dict(cls.config,base_path='/'))
        cls.documents=i.build(sources,cls.config)
        cls.documents.update(app.build(sources,cls.config))

    def test_missing_route_fails_before_filesystem_fallback(self):
        changed=dict(self.documents);changed.pop('he/peaksolo.html')
        with self.assertRaisesRegex(ValueError,'ROUTES_MISSING'):
            app.validate_pages(changed,self.config)

    def test_canonical_hreflang_direction_and_prelaunch_mutations_are_rejected(self):
        original=self.documents['hgq.html']
        cases=[
            (original.replace('rel="canonical" href="https://bb16studio.com/hgq.html"','rel="canonical" href="https://example.org/hgq.html"'),'CANONICAL'),
            (original.replace('hreflang="en"','hreflang="de"',1),'HREFLANG'),
            (original.replace('dir="ltr"','dir="rtl"',1),'LANGUAGE_DIRECTION'),
            (original.replace('class="status pending"','class="status"',1),'PRELAUNCH_BOUNDARY'),
        ]
        for text,error in cases:
            with self.subTest(error=error),self.assertRaisesRegex(ValueError,error):
                app.validate_pages({**self.documents,'hgq.html':text},self.config)

    def test_hgq_showcase_has_no_unverified_video_or_account_media(self):
        for locale in app.page_locales('hgq'):
            name = 'hgq.html' if locale == 'fr' else locale + '/hgq.html'
            with self.subTest(locale=locale):
                text = self.documents[name]
                self.assertEqual(text.count('name="hgq-warmup"'), 4)
                self.assertEqual(text.count('class="hgq-answer is-correct"'), 1)
                for color in ('blue', 'green', 'yellow', 'red'):
                    self.assertIn(f'data-pad="{color}"', text)
                    self.assertIn(f'src="/assets/apps/hgq-pad-{color}.webp"', text)
                self.assertEqual(text.count('<video'), 1)
                self.assertIn('src="/assets/video/hgq/pokemon-solo-fr.mp4"', text)
                illustrative = text.replace('</main>', '<video src="/assets/video/brand/hgq-presentation-fr.mp4"></video></main>')
                with self.assertRaisesRegex(ValueError, 'HGQ_RUNTIME_CAPTURE_REQUIRED'):
                    app.validate_pages({**self.documents, name: illustrative}, self.config)
                bad = text.replace('</main>', '<img src="/assets/screens/hgq/connexion.webp"></main>')
                with self.assertRaisesRegex(ValueError, 'HGQ_ACCOUNT_MEDIA_FORBIDDEN'):
                    app.validate_pages({**self.documents, name: bad}, self.config)

    def test_rtl_locales_and_untranslated_legal_links_are_explicit(self):
        for locale in ('he','fa','ur','ar'):
            with self.subTest(locale=locale):
                nodes=list(i.walk(i.parse(self.documents[locale+'/peaksolo.html'])))
                html=next(n for n in nodes if n.tag=='html')
                self.assertEqual(html.get('dir'),'rtl')
                if locale not in i.LOCALES:
                    policy=next(n for n in nodes if n.tag=='a' and n.get('href')=='/peaksolo-privacy.html')
                    self.assertEqual(policy.get('hreflang'),'fr')
                    self.assertTrue(any(n.get('lang')=='fr' for n in i.walk(policy)))

if __name__=='__main__':unittest.main()
