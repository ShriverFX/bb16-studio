import unittest
import json
import site_i18n as i
from validate_i18n import validate_catalog_content, validate_commercial

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

    def test_updated_policy_date_rejects_stale_day(self):
        units={'new':{'source':'Dernière mise à jour : 14 octobre 2026','markup':False}}
        for locale,good,bad in (
            ('ja','最終更新日：2026年10月14日','最終更新日：2026年10月1日'),
            ('vi','Cập nhật: 14 tháng 10 năm 2026','Cập nhật: 1 tháng 10 năm 2026'),
        ):
            validate_catalog_content(locale,{'new':good},units)
            with self.assertRaisesRegex(ValueError,'changed-number-price-or-date'):
                validate_catalog_content(locale,{'new':bad},units)

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

    def test_commercial_gate_rejects_old_price_period_and_missing_disclosure(self):
        units=json.loads((i.ROOT/'locales/source.json').read_text(encoding='utf-8'))
        ref=json.loads((i.ROOT/'content/commercial-reference.json').read_text(encoding='utf-8'))
        for locale in ('fr','en','ar','ja'):
            translated={} if locale=='fr' else i.catalog(locale,units)
            folder=i.ROOT if locale=='fr' else i.ROOT/locale
            for name in ('convertair.html','doccipher.html'):
                text=(folder/name).read_text(encoding='utf-8')
                validate_commercial(locale,name,i.parse(text),units,translated,ref)
                tree=i.parse(text)
                price=next(n for n in i.walk(tree) if n.tag=='p' and n.get('class')=='plan-price' and '19' in n.inner())
                price.children=i.parse(price.inner().replace('19','119',1)).children
                with self.subTest(locale=locale,name=name), self.assertRaisesRegex(ValueError,'price-or-billing-period'):
                    validate_commercial(locale,name,tree,units,translated,ref)
                tree=i.parse(text)
                unit=next(n for n in i.walk(tree) if n.get('class')=='plan-unit')
                unit.children=['per month']
                with self.assertRaisesRegex(ValueError,'price-or-billing-period'):
                    validate_commercial(locale,name,tree,units,translated,ref)
                key='db4c3354c759'
                disclosure=units[key]['source'] if locale=='fr' else translated[key]
                edited=i.render(i.parse(text)).replace(i.parse(disclosure).inner(),'')
                with self.assertRaisesRegex(ValueError,'missing-disclosure'):
                    validate_commercial(locale,name,i.parse(edited),units,translated,ref)

if __name__=='__main__': unittest.main()
