"""Verify complete static localization, resource locale, routing and source fidelity."""
from pathlib import Path
import json
import re
from difflib import SequenceMatcher
from urllib.parse import urlsplit
import site_i18n as i

def validate_catalog_content(locale, data, units):
    problems=[]
    for key,value in data.items():
        src=re.sub('<[^>]*>',' ',units[key]['source'])
        dst=re.sub('<[^>]*>',' ',value)
        expected_numbers=re.findall(r'\d+',src)
        # These two dated policy notices say 1 October 2026 in the French source.
        # East Asian year-month-day notation must not be distorted for a test.
        if key in {'b60764210cd2','0cad9695e49a'} and locale in {'ja','ko','zh','zh-Hans','zh-Hant'}:
            assert expected_numbers==['1','2026'], 'Refresh the dated policy contract'
            expected_numbers=['2026','10','1']
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
    if problems: raise ValueError(f'I18N_CONTENT:{locale}:{problems}')

def product_weight(nodes, html_path, base):
    from validate_site import HEADER_LOGOS, PAGE_INITIAL_MAX, PAGE_IMAGES_MAX, PAGE_VIDEOS_MAX, VIDEO_MAX
    def relative(value): return urlsplit(value).path[len(base):]
    def size(name): return (i.ROOT/name).stat().st_size
    shared=set(); images={}; videos=set(); headers=set()
    for n in nodes:
        if n.tag=='script' and n.get('src'): shared.add(relative(n.get('src')))
        if n.tag=='link' and n.get('rel')=='stylesheet': shared.add(relative(n.get('href')))
        if n.tag=='img':
            target=relative(n.get('src'))
            images[target]=images.get(target,False) or n.get('loading')!='lazy'
            for attr in ('src','data-dark','data-light'):
                if n.get(attr) and relative(n.get(attr)) in HEADER_LOGOS: headers.add(relative(n.get(attr)))
        if n.tag=='video' and n.get('data-src'): videos.add(relative(n.get('data-src')))
    for target in images:
        if target.endswith('.webp'): assert (i.ROOT/target).read_bytes()[8:12]==b'WEBP', target
    for target in videos:
        assert (i.ROOT/target).read_bytes()[4:8]==b'ftyp' and size(target)<=VIDEO_MAX, target
    initial=html_path.stat().st_size+sum(map(size,shared|headers))+sum(size(t) for t,eager in images.items() if eager and t not in headers)
    image_bytes=sum(size(t) for t in images if t not in headers)
    video_bytes=sum(map(size,videos))
    assert initial<=PAGE_INITIAL_MAX and image_bytes<=PAGE_IMAGES_MAX and video_bytes<=PAGE_VIDEOS_MAX, (html_path,initial,image_bytes,video_bytes)
    return {'initial_bytes':initial,'image_bytes':image_bytes,'video_bytes':video_bytes}

def validate():
    config=json.loads((i.ROOT/'site.config.json').read_text(encoding='utf-8'))
    base=config['base_path']
    units=json.loads((i.ROOT/'locales'/'source.json').read_text(encoding='utf-8'))
    results=[]
    for locale in i.LOCALES:
        if locale!='fr': validate_catalog_content(locale,i.catalog(locale,units),units)
        for name in i.PAGES:
            path=i.ROOT/name if locale=='fr' else i.ROOT/locale/name
            tree=i.parse(path.read_text(encoding='utf-8'))
            nodes=list(i.walk(tree))
            html=next(n for n in nodes if n.tag=='html')
            assert html.get('lang')==locale, (locale,name,'language')
            assert html.get('dir')==('rtl' if locale=='ar' else 'ltr'), (locale,name,'direction')
            ids=[n.get('id') for n in nodes if n.get('id')]
            assert len(ids)==len(set(ids)), (locale,name,'duplicate-id')
            canonical=[n.get('href') for n in nodes if n.tag=='link' and n.get('rel')=='canonical']
            assert canonical==[i.url(config,locale,name)], (locale,name,'canonical')
            alternate={n.get('hreflang'):n.get('href') for n in nodes if n.tag=='link' and n.get('rel')=='alternate'}
            assert set(alternate)==set(i.LOCALES)|{'x-default'}, (locale,name,'hreflang')
            assert all(alternate[code]==i.url(config,code,name) for code in i.LOCALES)
            picker=[n for n in nodes if n.tag=='details' and n.get('class')=='language-picker']
            assert len(picker)==1, (locale,name,'picker')
            links=[n for n in i.walk(picker[0]) if n.tag=='a']
            assert len(links)==22 and sum(n.get('aria-current')=='page' for n in links)==1
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
            if name in ('convertair.html','doccipher.html'):
                assert media, (locale,name,'no-media')
                assert all(html.get('data-'+key) for key in ('pause-all','resume-all','pause-one','play-one'))
                weights=product_weight(nodes,path,base)
            results.append({'locale':locale,'page':name,'resources':len(set(media)),**weights})
    for asset in i.localized_media(): assert (i.ROOT/asset).is_file(), asset
    return {'status':'PASS','locales':len(i.LOCALES),'translated_units_per_locale':len(units),
            'pages_checked':len(results),'localized_media_files':len(i.localized_media()),
            'max_product_initial_bytes':max(x.get('initial_bytes',0) for x in results),
            'native_linguistic_review':'NOT_OBSERVED','device_validation':'NOT_OBSERVED','pages':results}

if __name__=='__main__':
    result=validate()
    print(json.dumps({k:v for k,v in result.items() if k!='pages'},ensure_ascii=False))
