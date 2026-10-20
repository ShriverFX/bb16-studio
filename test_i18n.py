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

    def test_convertair_revenuecat_rights_tokens_and_meaning_are_guarded(self):
        units=json.loads((i.ROOT/'locales/source.json').read_text(encoding='utf-8'))
        key='8bc9e3640a7d'
        for locale in (code for code in i.LOCALES if code!='fr'):
            data=json.loads((i.ROOT/'locales'/f'{locale}.json').read_text(encoding='utf-8'))
            validate_catalog_content(locale,data,units)
            broken=dict(data)
            broken[key]=broken[key].replace('GPA.','IPK',1)
            with self.subTest(locale=locale,damage='order-prefix'), self.assertRaisesRegex(
                ValueError,'missing-immutable-rights-token:GPA'
            ):
                validate_catalog_content(locale,broken,units)
        english=json.loads((i.ROOT/'locales/en.json').read_text(encoding='utf-8'))
        for damage in (' find the plug',' deletion of an unidentified file'):
            broken=dict(english); broken[key]+=damage
            with self.subTest(damage=damage), self.assertRaisesRegex(
                ValueError,'corrupted-revenuecat-record-wording'
            ):
                validate_catalog_content('en',broken,units)
        broken=dict(english); broken['ab727a80ec51']+=' recording'
        with self.assertRaisesRegex(ValueError,'recording-instead-of-data'):
            validate_catalog_content('en',broken,units)
        for locale,key,good,bad in (
            ('ar',key,'تقييد المعالجة','التحديد'),
            ('ko','ab727a80ec51','해당 데이터를 삭제','기기를 삭제'),
        ):
            data=json.loads((i.ROOT/'locales'/f'{locale}.json').read_text(encoding='utf-8'))
            broken=dict(data); broken[key]=broken[key].replace(good,bad,1)
            with self.subTest(locale=locale,damage='reviewed-locale-semantics'), self.assertRaisesRegex(
                ValueError,'reviewed-locale-semantics'
            ):
                validate_catalog_content(locale,broken,units)

    def test_convertair_traditional_chinese_privacy_title_is_guarded(self):
        units=json.loads((i.ROOT/'locales/source.json').read_text(encoding='utf-8'))
        locale='zh-Hant'; key='4cd480f1d99c'
        data=json.loads((i.ROOT/'locales'/f'{locale}.json').read_text(encoding='utf-8'))
        self.assertEqual(data[key],'ConvertAir 隱私政策：本機文件、購買和 Google Play 元件。')
        broken=dict(data); broken[key]='ConvertAir ?私政策：本地文?、??和 Google Play ?件。'
        with self.assertRaisesRegex(ValueError,'missing-reviewed-locale-semantics'):
            validate_catalog_content(locale,broken,units)

    def test_convertair_guards_do_not_require_absent_units_in_partial_fixtures(self):
        units={'x': {'source':'Au moins 90 jours. Prix : 19,99 €.'}}
        validate_catalog_content('en',{'x':'At least 90 days. Price: €19.99.'},units)

    def test_convertair_review_access_tokens_and_age_scope_are_guarded(self):
        units=json.loads((i.ROOT/'locales/source.json').read_text(encoding='utf-8'))
        required={
            '22a8b87a0c8b': ('D1','Cloudflare','Google Play'),
            'cf6065bf88fa': ('Cloudflare',),
            '6cca0139b842': ('RevenueCat','ML Kit','android.permission.INTERNET'),
            '461f0ef7c388': ('ConvertAir','13'),
        }
        for locale in (code for code in i.LOCALES if code!='fr'):
            data=json.loads((i.ROOT/'locales'/f'{locale}.json').read_text(encoding='utf-8'))
            validate_catalog_content(locale,data,units)
            for key,tokens in required.items():
                for token in tokens:
                    broken=dict(data)
                    broken[key]=broken[key].replace(token,'',1)
                    with self.subTest(locale=locale,key=key,token=token), self.assertRaisesRegex(
                        ValueError,'missing-review-access-token|changed-number-price-or-date'
                    ):
                        validate_catalog_content(locale,broken,units)
        chinese=json.loads((i.ROOT/'locales/zh-Hant.json').read_text(encoding='utf-8'))
        broken=dict(chinese); broken['22a8b87a0c8b']+='?'
        with self.assertRaisesRegex(ValueError,'ascii-question-mark-in-cjk-review-access'):
            validate_catalog_content('zh-Hant',broken,units)

    def test_convertair_review_access_guards_ignore_unrelated_partial_fixtures(self):
        units={'x': {'source':'Au moins 90 jours. Prix : 19,99 €.'}}
        validate_catalog_content('en',{'x':'At least 90 days. Price: €19.99.'},units)

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
