"""Static localization. Standard library only; missing translations fail closed."""
from __future__ import annotations
from dataclasses import dataclass, field
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
LOCALES = {'fr':'Français','en':'English','de':'Deutsch','es':'Español','it':'Italiano',
 'pt':'Português','pt-BR':'Português (Brasil)','nl':'Nederlands','pl':'Polski',
 'ru':'Русский','uk':'Українська','tr':'Türkçe','ar':'العربية','hi':'हिन्दी',
 'id':'Bahasa Indonesia','ja':'日本語','ko':'한국어','th':'ไทย','vi':'Tiếng Việt',
 'zh':'中文','zh-Hans':'简体中文','zh-Hant':'繁體中文'}
PAGES = ('index.html','studio.html','apps.html','convertair.html','doccipher.html',
 'support.html','contact.html','privacy.html','legal.html','convertair-privacy.html',
 'doccipher-privacy.html','404.html')
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
BLOCK = set('div section article nav ul ol dl table header footer main p li h1 h2 h3 h4 details summary'.split())
UNITS = set('p li h1 h2 h3 h4 summary a button label title span figcaption legend option dt dd'.split())
ATTRS = {'alt','title','aria-label','placeholder'}

@dataclass
class Node:
    tag: str
    attrs: list = field(default_factory=list)
    children: list = field(default_factory=list)
    def get(self, key, default=None): return dict(self.attrs).get(key, default)
    def set(self, key, value):
        self.attrs = [(k,v) for k,v in self.attrs if k != key] + [(key,value)]
    def inner(self): return ''.join(render(x) for x in self.children)

def render(node):
    if isinstance(node, str): return escape(node, quote=False)
    if node.tag == '!raw': return node.get('value')
    if node.tag == 'root': return node.inner()
    attrs = ''.join(' '+k+('="'+escape(v, quote=True)+'"' if v is not None else '') for k,v in node.attrs)
    if node.tag in ('script','style'):
        return '<'+node.tag+attrs+'>'+''.join(node.children)+'</'+node.tag+'>'
    return '<'+node.tag+attrs+'>'+('' if node.tag in VOID else node.inner()+'</'+node.tag+'>')

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root=Node('root'); self.stack=[self.root]
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs); self.stack[-1].children.append(n)
        if tag not in VOID: self.stack.append(n)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag: self.stack=self.stack[:i]; return
    def handle_data(self,data): self.stack[-1].children.append(data)
    def handle_comment(self,data): self.stack[-1].children.append(Node('!raw',[('value','<!--'+data+'-->')]))
    def handle_decl(self,data): self.stack[-1].children.append(Node('!raw',[('value','<!'+data+'>')]))

def parse(text):
    p=Parser(); p.feed(text); p.close(); return p.root

def walk(node):
    if isinstance(node, Node):
        yield node
        for c in node.children: yield from walk(c)

def unit_id(value): return hashlib.sha256(value.encode()).hexdigest()[:12]

def needs_translation(value):
    plain=unescape(re.sub('<[^>]+>', '', value)).strip()
    return bool(plain and re.search(r'[A-Za-zÀ-ÿ]',plain) and
        plain not in {'BB16 Studio','BB16Studio','ConvertAir','DocCipher','HGQ','Hard Gamer Quiz',
                      'Instagram','TikTok','LinkedIn','Discord','X','Android','Google Play','YouTube',
                      'YouTube Shorts','Premium','Free','PDF','FAQ','OCR','01 / 04','01 / 03'} and
        not re.fullmatch(r'[^\s]+@[^\s]+|https?://\S+',plain))

def prepared(text, filename):
    tree=parse(text)
    if filename.endswith('-privacy.html'):
        for n in walk(tree):
            n.children=[c for c in n.children if not (isinstance(c,Node) and
                ((c.tag=='div' and c.get('lang')=='en') or c.tag=='hr'))]
            if n.tag=='a' and n.get('href')=='#english':
                n.set('href','/en/'+filename+'#main')
    return tree

def text_units(tree, callback):
    def visit(n):
        if not isinstance(n, Node) or n.tag in {'script','style','!raw'}: return
        for k,v in list(n.attrs):
            if v and k in ATTRS and needs_translation(v): n.set(k,callback(v,False))
            if n.tag=='meta' and k=='content' and n.get('name',n.get('property')) in {'description','og:title','og:description'}:
                n.set(k,callback(v,False))
        descendants=[x for c in n.children for x in walk(c)]
        if n.tag in UNITS and not any(x.tag in BLOCK for x in descendants):
            value=n.inner()
            if needs_translation(value):
                # Attributes within a translated phrase stay exactly as supplied.
                translated=callback(value,True)
                n.children=parse(translated).children
            return
        for i,c in enumerate(n.children):
            if isinstance(c,str) and needs_translation(c.strip()):
                core=c.strip(); n.children[i]=c.replace(core,callback(core,False))
            elif isinstance(c,Node): visit(c)
    visit(tree)

def extract(sources):
    units={}
    for filename in PAGES:
        def record(value, markup):
            key=unit_id(value)
            if key not in units: units[key]={'source':value,'markup':markup,'pages':[]}
            units[key]['pages']=sorted(set(units[key]['pages']+[filename]))
            return value
        text_units(prepared(sources[filename],filename),record)
    return units

def signature(fragment):
    """Translations may reorder inline elements but never add links or attributes."""
    return sorted((n.tag,tuple(sorted(n.attrs))) for n in walk(parse(fragment)) if n.tag!='root')

def catalog(locale, units):
    path=ROOT/'locales'/f'{locale}.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    if set(data)!=set(units):
        raise ValueError(f'I18N_KEYS:{locale}:missing={sorted(set(units)-set(data))}:extra={sorted(set(data)-set(units))}')
    for key,row in units.items():
        value=data[key]
        if not isinstance(value,str) or not value.strip(): raise ValueError(f'I18N_EMPTY:{locale}:{key}')
        if row['markup'] and signature(value)!=signature(row['source']):
            raise ValueError(f'I18N_MARKUP:{locale}:{key}')
        if not row['markup'] and '<' in value: raise ValueError(f'I18N_ATTRIBUTE_MARKUP:{locale}:{key}')
    return data

def localized_files():
    return [f'{locale}/{name}' for locale in LOCALES if locale!='fr' for name in PAGES]

def localized_media():
    import product_pages as p
    return [name.replace('/'+app+'/', '/'+app+'/'+locale+'/')
            for locale in LOCALES if locale!='fr'
            for name in list(p.SCREENS)+list(p.VIDEOS)
            for app in ('convertair','doccipher') if '/'+app+'/' in name]

def presentation_media():
    return [f'assets/{kind}/doccipher/'+('' if code=='fr' else code+'/')+'presentation-v2.'+ext
            for code in LOCALES for kind,ext in [('video','mp4'),('screens','webp')]]

def url(config, locale, filename):
    base=config.get('base_path','/')
    part=filename if locale=='fr' else f'{locale}/{filename}'
    if filename=='index.html': part='' if locale=='fr' else locale+'/'
    return (config.get('site_url') or '').rstrip('/')+base+part

def navigation(locale,filename,config,ui):
    base=config.get('base_path','/')
    links=[]
    for code,label in LOCALES.items():
        target=filename if code=='fr' else code+'/'+filename
        current=' aria-current="page"' if code==locale else ''
        links.append(f'<a href="{escape(base+target)}" lang="{code}" hreflang="{code}"{current}>{escape(label)}</a>')
    return parse('<details class="language-picker"><summary aria-label="'+escape(ui['language'],quote=True)+'"><span aria-hidden="true">◎</span> '+LOCALES[locale]+'</summary><nav class="language-list" aria-label="'+escape(ui['language'],quote=True)+'">'+''.join(links)+'</nav></details>').children[0]

def decorate(tree,locale,filename,config,ui):
    base=config.get('base_path','/')
    html=next(n for n in walk(tree) if n.tag=='html')
    html.set('lang',locale); html.set('dir','rtl' if locale=='ar' else 'ltr')
    for key in ('pause_all','resume_all','pause_one','play_one'): html.set('data-'+key.replace('_','-'),ui[key])
    head=next(n for n in walk(tree) if n.tag=='head')
    version=hashlib.sha256((ROOT/'i18n.css').read_bytes()+(ROOT/'locale.js').read_bytes()).hexdigest()[:12]
    head.children.append(Node('link',[('rel','stylesheet'),('href','/i18n.css?v='+version)]))
    head.children.append(Node('script',[('src','/locale.js?v='+version),('defer',None)]))
    for code in LOCALES:
        head.children.append(Node('link',[('rel','alternate'),('hreflang',code),('href',url(config,code,filename))]))
    head.children.append(Node('link',[('rel','alternate'),('hreflang','x-default'),('href',url(config,'fr',filename))]))
    for n in list(walk(tree)):
        if n.tag=='link' and n.get('rel')=='canonical': n.set('href',url(config,locale,filename))
        if n.tag=='meta' and n.get('property')=='og:url': n.set('content',url(config,locale,filename))
        if n.tag=='header':
            container=next((x for x in walk(n) if x.tag=='nav' and x.get('class')=='nav'),n)
            container.children.append(navigation(locale,filename,config,ui))
        # Keep bilingual source policies and deferred HGQ/test pages at their existing URLs.
        for attr in ('href','src','data-src','data-dark','data-light','poster'):
            value=n.get(attr)
            if not value or not value.startswith('/') or value.startswith('//'): continue
            relative=value.lstrip('/')
            leaf=relative.split('?',1)[0].split('#',1)[0]
            if locale!='fr' and attr=='href' and leaf in PAGES:
                relative=locale+'/'+relative
            elif locale!='fr' and relative.startswith(('assets/screens/convertair/','assets/screens/doccipher/',
                                      'assets/video/convertair/','assets/video/doccipher/')):
                bits=relative.split('/'); bits.insert(3,locale); relative='/'.join(bits)
            n.set(attr,base+relative)
            if locale!='fr' and n.tag=='a' and leaf.endswith('.html') and leaf not in PAGES and '/' not in leaf:
                n.set('hreflang','fr')
                n.children.append(Node('span',[('class','original-language'),('lang','fr')],[' · Français']))
        # Bilingual source contains an English jump link; here use the localized policy.
        if n.tag=='a' and n.get('href')==base+'en/'+filename+'#main':
            n.set('hreflang','en')
        if locale!='fr' and filename in ('convertair.html','doccipher.html') and n.tag=='section' and n.get('id')=='fonctions':
            intro=next((x for x in walk(n) if x.get('class')=='section-intro'),None)
            if intro:
                para=next((x for x in intro.children if isinstance(x,Node) and x.tag=='p'),None)
                if para: para.children=[ui['capture_note']]
        if locale!='fr' and filename in ('convertair.html','doccipher.html') and n.tag=='figcaption':
            n.children=[ui['capture_note']]
    if filename == 'doccipher.html':
        media = base+'assets/video/doccipher/'+('' if locale=='fr' else locale+'/')
        poster = base+'assets/screens/doccipher/'+('' if locale=='fr' else locale+'/')+'presentation-v2.webp'
        title = 'DocCipher · '+LOCALES[locale]
        player = parse('<section class="section" aria-labelledby="launch-video-title"><div class="container">'
            '<h2 id="launch-video-title">'+escape(title)+'</h2>'
            '<video data-launch-presentation controls playsinline preload="none" poster="'+escape(poster,quote=True)+'" '
            'aria-label="'+escape(title,quote=True)+'" style="display:block;width:100%;max-width:360px;max-height:75vh;margin:24px auto;background:#0b1220">'
            '<source src="'+escape(media+'presentation-v2.mp4',quote=True)+'" type="video/mp4"></video>'
            '<p class="section-note">'+escape(ui['capture_note'])+'</p></div></section>').children[0]
        main = next(n for n in walk(tree) if n.tag=='main')
        hero = next((i for i,n in enumerate(main.children) if isinstance(n,Node) and n.get('id')=='presentation'),None)
        main.children.insert(hero+1 if hero is not None else 0,player)
    return render(tree)

def build(sources, config, *, preview_locales=None):
    """sources have root-relative URLs. No source repo, service or JS translation required."""
    ui=json.loads((ROOT/'locales'/'ui.json').read_text(encoding='utf-8'))
    units=extract(sources)
    frozen=json.loads((ROOT/'locales'/'source.json').read_text(encoding='utf-8'))
    if units!=frozen: raise ValueError('I18N_SOURCE_CHANGED: refresh translations before building')
    result={}
    for locale in (preview_locales if preview_locales is not None else LOCALES):
        if locale not in LOCALES: raise ValueError('UNSUPPORTED_LOCALE:'+locale)
        data=catalog(locale,units) if locale!='fr' else None
        if data is not None:
            from validate_i18n import validate_catalog_content
            validate_catalog_content(locale,data,units)
        for filename in PAGES:
            if locale=='fr':
                tree=parse(sources[filename])
            else:
                tree=prepared(sources[filename],filename)
                text_units(tree,lambda value,markup:data[unit_id(value)])
            name=filename if locale=='fr' else locale+'/'+filename
            result[name]=decorate(tree,locale,filename,config,ui[locale])
    return result

if __name__=='__main__':
    import build_site
    config=build_site.read_config(); config['base_path']='/'
    units=extract(build_site.pages(config))
    (ROOT/'locales').mkdir(exist_ok=True)
    (ROOT/'locales'/'source.json').write_text(json.dumps(units,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'units':len(units),'words':sum(len(v['source'].split()) for v in units.values())}))
