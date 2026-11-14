"""Sparse product-page locales; global site and legal coverage stay unchanged.

Missing translations fail closed. Only supported app product routes are added.
Masters remain brand presentations, never proof of application runtime.
"""
from pathlib import Path
import json
import re
from urllib.parse import urlsplit
from difflib import SequenceMatcher
import brand_media as media
import hgq_showcase
import site_i18n as i

ROOT=Path(__file__).resolve().parent
CATALOGUES=ROOT/'locales'/'app-pages'

def page_locales(app):
    if app=='hgq':
        return {code:media.AUTONYMS[code] for code in media.APP_LANGUAGES[app]}
    if app=='peaksolo':
        result=dict(i.LOCALES)
        result.update({code:media.AUTONYMS[code] for code in media.APP_LANGUAGES[app] if code not in result})
        return result  # Includes three pre-existing region/script URLs.
    raise ValueError('UNKNOWN_APP_PAGE='+app)

def extra_files():
    return [code+'/'+app+'.html' for app in ('hgq','peaksolo') for code in page_locales(app)
            if code!='fr' and not (app+'.html' in i.PAGES and code in i.LOCALES)]

def available(locale,filename):
    if filename in ('hgq.html','peaksolo.html'):
        return locale in page_locales(filename[:-5])
    return locale in i.LOCALES and filename in i.PAGES

def prepared(text,app):
    tree=i.prepared(text,app+'.html')
    for parent in list(i.walk(tree)):
        parent.children=[child for child in parent.children if not (isinstance(child,i.Node) and
            ((child.tag=='figure' and 'brand-teaser' in child.get('class','').split()) or
             (child.tag=='details' and 'brand-language' in child.get('class','').split())))]
    return tree

def extract(sources):
    result={}
    for app in ('hgq','peaksolo'):
        units={}
        def record(value,markup):
            units[i.unit_id(value)]={'source':value,'markup':markup,'pages':[app+'.html']}
            return value
        i.text_units(prepared(sources[app+'.html'],app),record)
        result[app]=units
    return result

def frozen_sources(sources):
    units=extract(sources)
    frozen=json.loads((CATALOGUES/'source.json').read_text(encoding='utf-8'))
    if units!=frozen:raise ValueError('APP_PAGE_SOURCE_CHANGED: review scoped translations before building')
    return units

def validate_values(locale,data,units):
    """Product-fragment checks, without inventing unrelated legal-policy units.

    The global validator still checks its complete 517-unit legal catalogue.
    Here the source contract contains only the two preparatory product pages.
    """
    if set(data)!=set(units):raise ValueError('APP_PAGE_KEYS='+locale)
    for key,row in units.items():
        value=data[key]
        if not isinstance(value,str) or not value.strip() or '\ufffd' in value:
            raise ValueError('APP_PAGE_EMPTY_OR_ENCODING='+locale+':'+key)
        if row['markup'] and i.signature(value)!=i.signature(row['source']):
            raise ValueError('APP_PAGE_MARKUP='+locale+':'+key)
        if not row['markup'] and '<' in value:raise ValueError('APP_PAGE_ATTRIBUTE_MARKUP='+locale+':'+key)
        src=re.sub('<[^>]*>',' ',row['source']);dst=re.sub('<[^>]*>',' ',value)
        if re.findall(r'\d+',src)!=re.findall(r'\d+',dst):raise ValueError('APP_PAGE_NUMBER='+locale+':'+key)
        if re.match(r'^(?:EN|DE|ES|IT|NL|PT-BR|English|Deutsch|Español|Português|日本語|한국어|中文)\s*[:：]',dst):
            raise ValueError('APP_PAGE_LANGUAGE_PREFIX='+locale+':'+key)
        if len(src)>75 and SequenceMatcher(None,src.casefold(),dst.casefold()).ratio()>.88:
            raise ValueError('APP_PAGE_UNTRANSLATED_PARAGRAPH='+locale+':'+key)

def catalogue(app,locale,units):
    if locale=='fr':return None
    shared=json.loads((ROOT/'locales'/f'{locale}.json').read_text(encoding='utf-8')) if locale in i.LOCALES else {}
    required=set(units)-set(shared)
    path=CATALOGUES/app/(locale+'.json')
    own=json.loads(path.read_text(encoding='utf-8')) if required else {}
    if set(own)!=required:raise ValueError('APP_PAGE_OWN_KEYS='+app+':'+locale)
    result={key:shared[key] if key in shared else own[key] for key in units}
    validate_values(locale,result,units)
    return result

def ui(locale):
    shared=json.loads((ROOT/'locales/ui.json').read_text(encoding='utf-8'))
    extra=json.loads((CATALOGUES/'ui.json').read_text(encoding='utf-8'))
    values=shared.get(locale,extra.get(locale))
    if values is None:raise ValueError('APP_PAGE_UI_MISSING='+locale)
    for key in ('language','pause_all','resume_all','pause_one','play_one'):
        if not isinstance(values.get(key),str) or not values[key].strip():raise ValueError('APP_PAGE_UI_EMPTY='+locale+':'+key)
    return values

def inject_hgq(tree,locale):
    for parent in i.walk(tree):
        for index, child in enumerate(parent.children):
            if isinstance(child,i.Node) and child.get('id')=='hgq-showcase':
                fragment = hgq_showcase.render(locale).replace('src="assets/','src="/assets/').replace('poster="assets/','poster="/assets/')
                parent.children[index:index+1] = i.parse(fragment).children
                return
    raise ValueError('HGQ_SHOWCASE_ANCHOR_MISSING')

def render(app,locale,sources,config,units):
    if locale not in page_locales(app):raise ValueError('UNSUPPORTED_APP_PAGE_LOCALE='+app+':'+locale)
    tree=prepared(sources[app+'.html'],app)
    data=catalogue(app,locale,units)
    if data is not None:i.text_units(tree,lambda value,markup:data[i.unit_id(value)])
    if app=='hgq':
        inject_hgq(tree,locale)
    return i.decorate(tree,locale,app+'.html',config,ui(locale))

def build(sources,config):
    units=frozen_sources(sources);result={}
    for app in ('hgq','peaksolo'):
        for locale in page_locales(app):
            if app=='peaksolo' and locale in i.LOCALES:continue
            name=app+'.html' if locale=='fr' else locale+'/'+app+'.html'
            result[name]=render(app,locale,sources,config,units[app])
    return result

def product_files():
    return [app+'.html' if code=='fr' else code+'/'+app+'.html'
            for app in ('hgq','peaksolo') for code in page_locales(app)]

def validate_pages(documents=None,config=None,*,html_root=None):
    """Validate actual product routes; optional document/root fixtures are local.

    Host HTML/media checks do not certify a device or native linguistic review.
    """
    if config is None:config=json.loads((ROOT/'site.config.json').read_text(encoding='utf-8'))
    if any((config.get('store_listings',{}).get(app) or {}).get('published') is True for app in ('hgq','peaksolo')):
        raise ValueError('APP_PAGE_UNRELEASED_REFERENCE_REQUIRED')
    html_root=Path(html_root) if html_root is not None else ROOT
    if documents is None:documents={name:(html_root/name).read_text(encoding='utf-8') for name in product_files()}
    missing=set(product_files())-set(documents)
    if missing:raise ValueError('APP_PAGE_ROUTES_MISSING='+','.join(sorted(missing)))
    base=config['base_path'];rows=[]
    for app in ('hgq','peaksolo'):
        for locale in page_locales(app):
            filename=app+'.html';name=filename if locale=='fr' else locale+'/'+filename
            text=documents[name];nodes=list(i.walk(i.parse(text)))
            html=next(n for n in nodes if n.tag=='html')
            if html.get('lang')!=locale or html.get('dir')!=media.direction(locale):raise ValueError('APP_PAGE_LANGUAGE_DIRECTION='+name)
            ids=[n.get('id') for n in nodes if n.get('id')]
            if len(ids)!=len(set(ids)):raise ValueError('APP_PAGE_DUPLICATE_ID='+name)
            canonical=[n.get('href') for n in nodes if n.tag=='link' and n.get('rel')=='canonical']
            if canonical!=[i.url(config,locale,filename)]:raise ValueError('APP_PAGE_CANONICAL='+name)
            alternate={n.get('hreflang'):n.get('href') for n in nodes if n.tag=='link' and n.get('rel')=='alternate'}
            expected={code:i.url(config,code,filename) for code in page_locales(app)}
            expected['x-default']=i.url(config,'fr',filename)
            if alternate!=expected:raise ValueError('APP_PAGE_HREFLANG='+name)
            pickers=[n for n in nodes if n.tag=='details' and n.get('class')=='language-picker']
            if len(pickers)!=1:raise ValueError('APP_PAGE_PICKER='+name)
            links=[n for n in i.walk(pickers[0]) if n.tag=='a']
            if {n.get('hreflang'):n.get('href') for n in links}!={code:base+(filename if code=='fr' else code+'/'+filename) for code in page_locales(app)} or len(links)!=len(page_locales(app)):
                raise ValueError('APP_PAGE_PICKER_ROUTES='+name)
            if sum(n.get('aria-current')=='page' for n in links)!=1:raise ValueError('APP_PAGE_PICKER_CURRENT='+name)
            status=[n for n in nodes if n.tag=='span' and n.get('class')=='status pending']
            if len(status)!=1 or re.search(r'play\.google\.com/store/apps/details|\d[\d.,\s]*[€$£]|[€$£]\s*\d',text):raise ValueError('APP_PAGE_PRELAUNCH_BOUNDARY='+name)
            if app=='hgq' and any(re.search(r'/hgq/(connexion|inscription|compte)\.', n.get(attr) or '')
                                 for n in nodes for attr in ('src','poster','data-src','href')):
                raise ValueError('HGQ_ACCOUNT_MEDIA_FORBIDDEN='+name)
            media.validate_media_nodes(nodes,app,locale,base)
            for n in nodes:
                for attr in ('href','src','poster','data-src','data-dark','data-light'):
                    value=n.get(attr)
                    if not value or value.startswith(('#','mailto:','http:','https:')):continue
                    if not value.startswith(base) or value.startswith('//'):raise ValueError('APP_PAGE_LOCAL_URL='+name)
                    target=urlsplit(value).path[len(base):]
                    if not target:continue
                    if '\\' in target or '..' in Path(target).parts:raise ValueError('APP_PAGE_PATH='+name)
                    if target not in documents and not (ROOT/target).is_file():raise ValueError('APP_PAGE_TARGET_MISSING='+target)
                    if locale not in i.LOCALES and n.tag=='a' and target.endswith('.html') and not available(locale,Path(target).name):
                        if n.get('hreflang')!='fr' or not any(x.get('lang')=='fr' for x in i.walk(n)):
                            raise ValueError('APP_PAGE_UNMARKED_FRENCH_DESTINATION='+name)
            from validate_i18n import product_weight
            weights=product_weight(nodes,html_root/name,base)
            rows.append({'locale':locale,'page':filename,'path':name,**weights})
    return {'status':'PASS','product_pages':len(rows),'app_languages':{'hgq':6,'peaksolo':28},'preserved_peaksolo_variants':3,'new_product_routes':len(extra_files()),'native_linguistic_review':'NOT_OBSERVED','device_validation':'NOT_OBSERVED','pages':rows}
