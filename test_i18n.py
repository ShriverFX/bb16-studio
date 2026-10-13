import unittest
import site_i18n as i
from validate_i18n import validate_catalog_content

class LocalizationTests(unittest.TestCase):
    def test_policy_date_accepts_correct_local_order_not_another_date(self):
        units={'b60764210cd2':{'source':'Dernière mise à jour : 1 octobre 2026','markup':False}}
        validate_catalog_content('ja',{'b60764210cd2':'最終更新日：2026年10月1日'},units)
        with self.assertRaisesRegex(ValueError,'changed-number-price-or-date'):
            validate_catalog_content('ja',{'b60764210cd2':'最終更新日：2026年11月1日'},units)

    def test_security_delay_and_price_cannot_change_during_translation(self):
        units={'x':{'source':'Au moins 90 jours. Prix : 19,99 €.', 'markup':False}}
        validate_catalog_content('en',{'x':'At least 90 days. Price: €19.99.'},units)
        for value in ('At least 9 days. Price: €19.99.','At least 90 days. Price: €1.99.'):
            with self.assertRaisesRegex(ValueError,'changed-number-price-or-date'):
                validate_catalog_content('en',{'x':value},units)

    def test_french_disguised_as_english_is_rejected(self):
        source='Vous pouvez conserver vos documents dans votre coffre. Cette page décrit les données de votre appareil.'
        units={'x':{'source':source,'markup':False}}
        with self.assertRaisesRegex(ValueError,'I18N_CONTENT'):
            validate_catalog_content('en',{'x':'English: '+source},units)
        with self.assertRaisesRegex(ValueError,'I18N_CONTENT'):
            validate_catalog_content('en',{'x':source.replace('données','data')},units)
        validate_catalog_content('en',{'x':'You can keep your documents in your vault. This page describes the data on your device.'},units)

    def test_html_translation_signature_allows_reordering_not_new_links(self):
        source='Voir <a href="/privacy.html">la politique</a> et <strong>les limites</strong>.'
        translated='Read <strong>the limits</strong> and <a href="/privacy.html">the policy</a>.'
        self.assertEqual(i.signature(source),i.signature(translated))
        self.assertNotEqual(i.signature(source),i.signature(translated.replace('/privacy.html','https://example.org')))

    def test_inline_phrase_is_one_translation_unit(self):
        tree=i.parse('<p>Lire <a href="/contact.html">le support</a>.</p>')
        seen=[]
        i.text_units(tree,lambda text,markup: seen.append((text,markup)) or text)
        self.assertEqual(seen,[('Lire <a href="/contact.html">le support</a>.',True)])

    def test_locale_urls_respect_subdirectory_and_french_roots(self):
        config={'site_url':'https://example.org','base_path':'/studio/'}
        self.assertEqual(i.url(config,'fr','index.html'),'https://example.org/studio/')
        self.assertEqual(i.url(config,'ar','index.html'),'https://example.org/studio/ar/')
        self.assertEqual(i.url(config,'pt-BR','convertair.html'),'https://example.org/studio/pt-BR/convertair.html')

    def test_catalogue_includes_scripts_and_region_without_alias_fallback(self):
        self.assertEqual(len(i.LOCALES),22)
        self.assertTrue({'zh','zh-Hans','zh-Hant','pt','pt-BR'}.issubset(i.LOCALES))
        self.assertEqual(len(i.localized_files()),21*12)
        self.assertEqual(len(set(i.localized_media())),21*26)

if __name__=='__main__': unittest.main()
