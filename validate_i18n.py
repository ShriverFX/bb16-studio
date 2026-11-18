"""Verify complete static localization, resource locale, routing and source fidelity."""
from pathlib import Path
import html
import json
import re
from difflib import SequenceMatcher
from urllib.parse import urlsplit
import site_i18n as i

CSS_URL = re.compile(r'''url\(\s*["']?([^"')]+)''', re.IGNORECASE)
CSS_IMPORT = re.compile(r'''@import\s+(?:url\(\s*)?["']?([^"')\s;]+)''', re.IGNORECASE)

# Reviewed disclosures: market versus language, Premium network checks,
# pseudonymous purchase data, offline cached rights and sales statistics.
COMMERCIAL_DISCLOSURES = {
    'convertair.html': ('e30028d064d6','17664717c594','db4c3354c759','5f7cc7fcc41a'),
    'doccipher.html': ('e30028d064d6','8518ccfab1cc','db4c3354c759','461daf8a5435'),
    'convertair-privacy.html': ('a47df237f0aa','387e0a375332'),
    'doccipher-privacy.html': ('a47df237f0aa','6b31336cc71f'),
}

def validate_commercial(locale, name, tree, units, translated, reference):
    nodes=list(i.walk(tree))
    def fail(reason): raise ValueError(f'COMMERCIAL:{locale}:{name}:{reason}')
    def price(cents): return f'{cents//100},{cents%100:02d} €'
    def localized(source):
        key=i.unit_id(source)
        if key not in units: fail('missing-price-source')
        return source if locale=='fr' else translated[key]
    if name in ('convertair.html','doccipher.html'):
        plans=[n for n in nodes if n.tag=='p' and n.get('class')=='plan-price']
        if name=='convertair.html':
            ref=reference['convertair']
            expected=[
                f'{price(ref["annual_cents"])}<span class="plan-unit">par an</span>',
                f'{price(ref["lifetime_launch_cents"])}<span class="plan-unit">au lancement, puis {price(ref["lifetime_standard_cents"])}</span>',
            ]
        else:
            expected=[f'{price(reference["doccipher"]["lifetime_cents"])}<span class="plan-unit">paiement unique</span>']
        if len(plans)!=len(expected)+1: fail('unexpected-plan-count')
        for plan,source in zip(plans[1:],expected):
            if plan.inner()!=i.parse(localized(source)).inner(): fail('price-or-billing-period')
    html=i.render(tree)
    for key in COMMERCIAL_DISCLOSURES.get(name,()):
        if key not in units: fail('missing-disclosure-source:'+key)
        value=units[key]['source'] if locale=='fr' else translated[key]
        if i.parse(value).inner() not in html: fail('missing-disclosure:'+key)

def validate_reviewed_zh_hant_text(data, units):
    """Reject lossy encoding in the finite74 reviewed cells, keep real questions."""
    review=json.loads((i.ROOT/'content/zh-Hant-review-20261102.json').read_text(encoding='utf-8'))
    keys=set(review['reviewed_keys'])
    if len(keys)!=74:
        raise ValueError('ZH_HANT_REVIEW_SCOPE_CHANGED')
    for key,value in data.items():
        if key not in keys:continue
        text=html.unescape(re.sub('<[^>]*>',' ',value)).strip()
        source=html.unescape(re.sub('<[^>]*>',' ',units[key]['source'])).strip()
        real_ascii_question=(text.count('?')==1 and text.endswith('?') and source.endswith('?'))
        if '\ufffd' in text or ('?' in text and not real_ascii_question):
            raise ValueError('ZH_HANT_ENCODING_DAMAGED='+key)


def validate_catalog_content(locale, data, units):
    if locale=='zh-Hant':validate_reviewed_zh_hant_text(data,units)
    problems=[]
    for key,value in data.items():
        src=re.sub('<[^>]*>',' ',units[key]['source'])
        dst=re.sub('<[^>]*>',' ',value)
        expected_numbers=re.findall(r'\d+',src)
        # East Asian year-month-day notation includes a numeric month. Bind it
        # to the actual source date, not an obsolete translation key or day.
        months=('janvier','février','mars','avril','mai','juin','juillet','août',
                'septembre','octobre','novembre','décembre')
        policy_date=re.match(r'Dernière mise à jour : (\d+)(?:er)? ('+'|'.join(months)+r') (\d{4})\b',src)
        if policy_date:
            day,month_name,year=policy_date.groups()
            month=str(months.index(month_name)+1)
        if policy_date and locale in {'ja','ko','zh','zh-Hans','zh-Hant'}:
            expected_numbers=[year,month,day]
        if policy_date and locale=='vi' and 'tháng ' in dst:
            expected_numbers=[day,month,year]
        if expected_numbers!=re.findall(r'\d+',dst):
            problems.append((key,'changed-number-price-or-date'))
        # A language prefix or a handful of word replacements is not translation.
        if re.match(r'^(?:PT-BR|EN|DE|ES|IT|NL|English|Deutsch|Español|Italiano|Nederlands|Português|日本語|한국어|中文|ภาษาไทย|Tiếng Việt)\s*[:：]',dst):
            problems.append((key,'language-prefix-placeholder'))
        if len(src)>75 and SequenceMatcher(None,src.casefold(),dst.casefold()).ratio()>.88:
            if not (locale=='en' and not re.search(r'\b(?:vous|votre|les|une|des|avec|dans)\b',src,re.I)):
                problems.append((key,'almost-untranslated-paragraph'))
        if re.search(r'\b(?:vous pouvez|vos documents|sur votre appareil|cette page|dans le navigateur|ne joignez jamais|les données|votre coffre|écrivez-nous)\b',dst,re.I):
            problems.append((key,'residual-french'))
    rights_key='8bc9e3640a7d'
    rights=data.get(rights_key,'')
    for token in ('GPA.','RevenueCat','RevenueCat App User ID'):
        if token not in rights:
            problems.append((rights_key,'missing-immutable-rights-token:'+token))
    if re.search(r'(?i)\b(?:plug|socket|prise|stecker|enchufe|listing|file|fichier)\b',rights):
        problems.append((rights_key,'corrupted-revenuecat-record-wording'))
    retention_key='ab727a80ec51'
    retention=data.get(retention_key,'')
    for token in ('RevenueCat','BB16 Studio','Google Play'):
        if token not in retention:
            problems.append((retention_key,'missing-retention-token:'+token))
    review_access_tokens={
        '22a8b87a0c8b': ('ConvertAir','D1','Cloudflare','Google Play'),
        'cf6065bf88fa': ('Cloudflare',),
        '6cca0139b842': ('RevenueCat','ML Kit','android.permission.INTERNET'),
        '461f0ef7c388': ('ConvertAir','13'),
    }
    for key,tokens in review_access_tokens.items():
        if key not in units:
            continue
        value=data.get(key,'')
        for token in tokens:
            if token not in value:
                problems.append((key,'missing-review-access-token:'+token))
        for forbidden in ('CAR1_','CONVERTAIR_REVIEW_ACCESS_URL'):
            if forbidden in value:
                problems.append((key,'forbidden-review-access-secret-or-config:'+forbidden))
        if locale in {'ja','ko','zh','zh-Hans','zh-Hant'} and '?' in value:
            problems.append((key,'ascii-question-mark-in-cjk-review-access'))
    recording_words=('recording','aufnahme','grabación','रिकॉर्डिंग','rekaman','registrazione',
                     '録音','録画','녹음','opname','nagranie','gravação','录音','錄音','การบันทึก')
    for key,value in ((retention_key,retention),(rights_key,rights)):
        if any(word in value.casefold() for word in recording_words):
            problems.append((key,'recording-instead-of-data'))
    reviewed_locale_phrases={
        'ar': {rights_key: ('تقييد المعالجة','ستشرح لك BB16 Studio هذا القيد')},
        'ko': {retention_key: ('해당 데이터를 삭제하거나 앱을 제거할 때까지',)},
    }
    for key,phrases in reviewed_locale_phrases.get(locale,{}).items():
        for phrase in phrases:
            if phrase not in data.get(key,''):
                problems.append((key,'missing-reviewed-locale-semantics:'+phrase))
    reviewed_locale_forbidden={
        'ar': {rights_key: ('أو التحديد أو قابلية النقل',)},
        'ko': {retention_key: ('기기를 삭제하거나 앱을 제거할 때까지',)},
    }
    for key,phrases in reviewed_locale_forbidden.get(locale,{}).items():
        for phrase in phrases:
            if phrase in data.get(key,''):
                problems.append((key,'forbidden-reviewed-locale-semantics:'+phrase))
    if locale=='en':
        expected={
            retention_key: ('which data concerns you','does not promise erasure it cannot verify'),
            '387e0a375332': ('a device identifier for features provided through Google Play services',
                             'does not list document, image or recognised-text content'),
            rights_key: ('which RevenueCat data concerns you',
                         'will not claim to have erased data it could not identify as yours'),
        }
        for key,phrases in expected.items():
            for phrase in phrases:
                if phrase not in data.get(key,''):
                    problems.append((key,'missing-reviewed-english-semantics:'+phrase))
    if problems: raise ValueError(f'I18N_CONTENT:{locale}:{problems}')

def product_weight(nodes, html_path, base):
    from validate_site import HEADER_LOGOS, PAGE_INITIAL_MAX, PAGE_IMAGES_MAX, PAGE_VIDEOS_MAX, VIDEO_MAX
    import hgq_runtime_media
    def relative(value): return urlsplit(value).path[len(base):]
    def size(name): return (i.ROOT/name).stat().st_size
    shared=set(); stylesheets=set(); images={}; videos=set(); headers=set()
    for n in nodes:
        if n.tag=='script' and n.get('src'): shared.add(relative(n.get('src')))
        if n.tag=='link' and n.get('rel')=='stylesheet':
            stylesheet=relative(n.get('href'))
            shared.add(stylesheet)
            stylesheets.add(stylesheet)
        if n.tag=='img':
            target=relative(n.get('src'))
            images[target]=images.get(target,False) or n.get('loading')!='lazy'
            for attr in ('src','data-dark','data-light'):
                if n.get(attr) and relative(n.get(attr)) in HEADER_LOGOS: headers.add(relative(n.get(attr)))
        if n.tag=='video' and n.get('data-src'): videos.add(relative(n.get('data-src')))
        if n.tag=='video' and n.get('src'):
            videos.add(relative(n.get('src')))
            if n.get('poster'):images[relative(n.get('poster'))]=True
    # CSS-referenced local resources are part of the initial page budget too.
    # In particular this keeps the bundled Manrope fonts visible to the 350 kB gate.
    css_resources=set()
    for stylesheet in tuple(stylesheets):
        css_path=i.ROOT/stylesheet
        assert css_path.is_file(), stylesheet
        css=css_path.read_text(encoding='utf-8')
        for raw in CSS_URL.findall(css)+CSS_IMPORT.findall(css):
            link=html.unescape(raw.strip())
            parsed=urlsplit(link)
            assert not parsed.scheme and not parsed.netloc and not link.startswith('//'), (stylesheet,link)
            target=parsed.path
            if target.startswith(base): target=target[len(base):]
            else: target=str((Path(stylesheet).parent/target).as_posix())
            target=str(Path(target))
            assert target and '..' not in Path(target).parts and (i.ROOT/target).is_file(), (stylesheet,link)
            css_resources.add(target)
    shared |= css_resources
    for target in images:
        if target.endswith('.webp'): assert (i.ROOT/target).read_bytes()[8:12]==b'WEBP', target
    for target in videos:
        limit = hgq_runtime_media.VIDEO_MAX if target in hgq_runtime_media.FILES else VIDEO_MAX
        assert (i.ROOT/target).read_bytes()[4:8]==b'ftyp' and size(target)<=limit, target
    presentations=[relative(n.get('src')) for n in nodes if n.tag=='source' and n.get('src','').endswith('/presentation-v2.mp4')]
    if html_path.name=='doccipher.html':
        assert len(presentations)==1, (html_path,'missing-localized-presentation')
    for target in presentations:
        assert (i.ROOT/target).read_bytes()[4:8]==b'ftyp' and size(target)<=400_000, target
        videos.add(target)
    initial=html_path.stat().st_size+sum(map(size,shared|headers))+sum(size(t) for t,eager in images.items() if eager and t not in headers)
    image_bytes=sum(size(t) for t in images if t not in headers)
    video_bytes=sum(map(size,videos))
    video_limit = hgq_runtime_media.PAGE_VIDEOS_MAX if html_path.name == 'hgq.html' else PAGE_VIDEOS_MAX
    assert initial<=PAGE_INITIAL_MAX and image_bytes<=PAGE_IMAGES_MAX and video_bytes<=video_limit, (html_path,initial,image_bytes,video_bytes)
    return {'initial_bytes':initial,'image_bytes':image_bytes,'video_bytes':video_bytes}

def validate():
    config=json.loads((i.ROOT/'site.config.json').read_text(encoding='utf-8'))
    base=config['base_path']
    units=json.loads((i.ROOT/'locales'/'source.json').read_text(encoding='utf-8'))
    reference=json.loads((i.ROOT/'content'/'commercial-reference.json').read_text(encoding='utf-8'))
    results=[]
    for locale in i.LOCALES:
        translated={} if locale=='fr' else i.catalog(locale,units)
        if locale!='fr': validate_catalog_content(locale,translated,units)
        for name in i.PAGES:
            path=i.ROOT/name if locale=='fr' else i.ROOT/locale/name
            tree=i.parse(path.read_text(encoding='utf-8'))
            nodes=list(i.walk(tree))
            if name in COMMERCIAL_DISCLOSURES:
                validate_commercial(locale,name,tree,units,translated,reference)
            html=next(n for n in nodes if n.tag=='html')
            assert html.get('lang')==locale, (locale,name,'language')
            assert html.get('dir')==('rtl' if locale=='ar' else 'ltr'), (locale,name,'direction')
            ids=[n.get('id') for n in nodes if n.get('id')]
            assert len(ids)==len(set(ids)), (locale,name,'duplicate-id')
            canonical=[n.get('href') for n in nodes if n.tag=='link' and n.get('rel')=='canonical']
            assert canonical==[i.url(config,locale,name)], (locale,name,'canonical')
            alternate={n.get('hreflang'):n.get('href') for n in nodes if n.tag=='link' and n.get('rel')=='alternate'}
            page_locales=i.page_locales(name)
            assert set(alternate)==set(page_locales)|{'x-default'}, (locale,name,'hreflang')
            assert all(alternate[code]==i.url(config,code,name) for code in page_locales)
            picker=[n for n in nodes if n.tag=='details' and n.get('class')=='language-picker']
            assert len(picker)==1, (locale,name,'picker')
            links=[n for n in i.walk(picker[0]) if n.tag=='a']
            assert len(links)==len(page_locales) and sum(n.get('aria-current')=='page' for n in links)==1
            media=[]
            for n in nodes:
                for attr in ('href','src','data-src','data-light','data-dark','poster'):
                    value=n.get(attr)
                    if not value or value.startswith(('#','mailto:','https:','http:')): continue
                    assert value.startswith(base) and not value.startswith('//'), (locale,name,value)
                    target=urlsplit(value).path[len(base):]
                    if not target: continue
                    assert not any(x=='..' for x in Path(target).parts) and '\\' not in target
                    assert (i.ROOT/target).is_file(), (locale,name,'missing',value)
                    if re.match(r'assets/(screens|video)/(convertair|doccipher)/',target):
                        if locale!='fr': assert target.split('/')[3]==locale, (locale,name,'wrong-media-locale',value)
                        media.append(target)
            weights={}
            if name=='peaksolo.html':
                import brand_media
                brand_media.validate_media_nodes(nodes,'peaksolo',locale,base)
            if name in ('convertair.html','doccipher.html','peaksolo.html','peaksolo-privacy.html'):
                if name in ('convertair.html','doccipher.html'):
                    assert media, (locale,name,'no-media')
                    assert all(html.get('data-'+key) for key in ('pause-all','resume-all','pause-one','play-one'))
                weights=product_weight(nodes,path,base)
            results.append({'locale':locale,'page':name,'resources':len(set(media)),**weights})
    for asset in i.localized_media(): assert (i.ROOT/asset).is_file(), asset
    import app_pages_i18n
    sparse=app_pages_i18n.validate_pages(config=config)
    seen={(row['locale'],row['page']) for row in results}
    results.extend(row for row in sparse['pages'] if (row['locale'],row['page']) not in seen)
    return {'status':'PASS','locales':len(i.LOCALES),'translated_units_per_locale':len(units),
            'pages_checked':len(results),'commercial_pages_checked':len(i.LOCALES)*len(COMMERCIAL_DISCLOSURES),'localized_media_files':len(i.localized_media()),
            'max_product_initial_bytes':max(x.get('initial_bytes',0) for x in results),
            'app_product_pages':sparse['product_pages'],'app_product_languages':sparse['app_languages'],
            'extra_product_routes':sparse['new_product_routes'],
            'native_linguistic_review':'NOT_OBSERVED','device_validation':'NOT_OBSERVED','pages':results}

if __name__=='__main__':
    result=validate()
    print(json.dumps({k:v for k,v in result.items() if k!='pages'},ensure_ascii=False))
