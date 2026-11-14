"""Negative tests for localized brand selection and explicit script/region gaps."""
import unittest
import brand_media as b
import site_i18n as i

def nodes(text):return list(i.walk(i.parse(text)))
def rooted(text):
 return text.replace('src="assets/','src="/assets/').replace('poster="assets/','poster="/assets/').replace('href="assets/','href="/assets/')

class BrandMediaLocaleTests(unittest.TestCase):
 def test_english_page_cannot_silently_get_french_video(self):
  text=rooted(b.peaksolo_media_section('en'))
  b.validate_media_nodes(nodes(text),'peaksolo','en')
  with self.assertRaisesRegex(ValueError,'WRONG_SOURCE'):
   b.validate_media_nodes(nodes(text.replace('peaksolo-presentation-en.mp4','peaksolo-presentation-fr.mp4')),'peaksolo','en')

 def test_region_and_script_gaps_are_explicit_links_not_french_fallback(self):
  for locale,destination in [('pt-BR','/pt/peaksolo.html#presentation-video'),('zh-Hant','/zh-Hans/peaksolo.html#presentation-video')]:
   text=rooted(b.peaksolo_media_section(locale));b.validate_media_nodes(nodes(text),'peaksolo',locale)
   self.assertNotIn('<video',text);self.assertIn(destination,text)
   with self.assertRaisesRegex(ValueError,'EXPLICIT_ALTERNATE'):
    b.validate_media_nodes(nodes(text.replace(destination,'/peaksolo.html#presentation-video')),'peaksolo',locale)

 def test_chinese_simplified_media_keeps_script_identity(self):
  for locale in ('zh','zh-Hans'):
   text=rooted(b.peaksolo_media_section(locale));self.assertIn('lang="zh-Hans"',text)
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
  text=rooted(b.peaksolo_media_section('fr'));result=b.validate_media_nodes(nodes(text),'peaksolo')
  self.assertEqual(result['media_only_links'],[])
  self.assertEqual(len([n for n in nodes(text) if n.tag=='video']),1)
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

if __name__=='__main__':unittest.main()
