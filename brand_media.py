"""Fail-closed media composition for HGQ and PeakSolo product pages."""
import hgq_runtime_media
import peaksolo_runtime_media

APP_LANGUAGES={
 'hgq':('fr','en','es','pt','ja','ko'),
 'peaksolo':('fr','en','es','pt','de','it','nl','ru','uk','pl','ro','sv','cs','el','tr','ar','he','fa','ur','hi','bn','id','ms','vi','th','ja','ko','zh'),
}
AUTONYMS={'fr':'Français','en':'English','es':'Español','pt':'Português','de':'Deutsch','it':'Italiano','nl':'Nederlands','ru':'Русский','uk':'Українська','pl':'Polski','ro':'Română','sv':'Svenska','cs':'Čeština','el':'Ελληνικά','tr':'Türkçe','ar':'العربية','he':'עברית','fa':'فارسی','ur':'اردو','hi':'हिन्दी','bn':'বাংলা','id':'Bahasa Indonesia','ms':'Bahasa Melayu','vi':'Tiếng Việt','th':'ไทย','ja':'日本語','ko':'한국어','zh':'简体中文'}
PS_PAGE_MEDIA={code:code for code in APP_LANGUAGES['peaksolo']}
PS_PAGE_MEDIA['zh-Hans']='zh'
PS_EXPLICIT_ALTERNATES={'pt-BR':('pt','pt'),'zh-Hant':('zh-Hans','zh')}
LOCALIZED_BRAND_TEASERS={app:{code:{'video':f'assets/video/brand/{app}-presentation-{code}.mp4','poster':f'assets/branding/{app}-presentation-{code}.webp'} for code in codes} for app,codes in APP_LANGUAGES.items()}
BRAND_TEASERS={app:spec['fr'] for app,spec in LOCALIZED_BRAND_TEASERS.items()}
RETIRED_HGQ_MEDIA = frozenset(path for media in LOCALIZED_BRAND_TEASERS['hgq'].values() for path in media.values())
RETIRED_PEAKSOLO_MEDIA = frozenset(
 path for media in LOCALIZED_BRAND_TEASERS['peaksolo'].values() for path in media.values()
)
# PeakSolo now publishes only attested Android runtime captures. Its former
# illustrated masters remain in the repository but are no longer exported.
MEDIA_FILES=[]

def language_tag(code):return 'zh-Hans' if code=='zh' else code
def direction(code):return 'rtl' if code in {'ar','he','fa','ur'} else 'ltr'

def brand_teaser(key,locale='fr'):
 raise ValueError(key.upper()+'_RUNTIME_CAPTURE_REQUIRED')

def peaksolo_media_section(site_locale):
 raise ValueError('PEAKSOLO_RUNTIME_CAPTURE_REQUIRED')

def inject_peaksolo(tree,site_locale):
 import site_i18n as i
 if site_locale not in set(PS_PAGE_MEDIA) | set(PS_EXPLICIT_ALTERNATES):
  raise ValueError('PEAKSOLO_RUNTIME_UNSUPPORTED_LOCALE='+site_locale)
 hero_player=peaksolo_runtime_media.hero_player(site_locale)
 runtime_section=peaksolo_runtime_media.render(site_locale)
 if not hero_player or not runtime_section:
  raise ValueError('PEAKSOLO_RUNTIME_CAPTURE_REQUIRED')
 # Remove the previously generated illustrated section before rebuilding the
 # product composition. This also makes injection safe on checked-in pages.
 for parent in i.walk(tree):
  parent.children=[child for child in parent.children
                   if not (isinstance(child,i.Node) and child.tag=='section'
                           and child.get('id')=='presentation-video')]
 for parent in i.walk(tree):
  for pos,child in enumerate(parent.children):
   if (isinstance(child,i.Node) and child.tag=='section' and child.get('id')=='presentation'
       and child.get('class')=='product-hero planned-product'):
    containers=[node for node in child.children if isinstance(node,i.Node)
                and node.tag=='div' and node.get('class')=='container']
    if len(containers)!=1:raise ValueError('PEAKSOLO_HERO_CONTAINER_CHANGED')
    container=containers[0]
    original=list(container.children)
    container.set('class','container product-hero-grid')
    copy=i.Node('div',[('class','product-hero-copy')],original)
    for node in i.walk(copy):
     if (node.get('class')=='peaksolo-identity'
         and any(name=='data-reveal' for name,_ in node.attrs)):
      node.attrs=[(name,value) for name,value in node.attrs if name!='data-reveal']
    container.children=[copy,i.parse(hero_player).children[0]]
    parent.children[pos+1:pos+1]=i.parse(runtime_section).children
    return
 raise ValueError('PEAKSOLO_MEDIA_ANCHOR_MISSING')

def validate_media_nodes(nodes,key,site_locale='fr',base_path='/'):
 if key=='hgq':
  if site_locale not in APP_LANGUAGES['hgq']:raise ValueError('BRAND_MEDIA_UNSUPPORTED_PAGE_LOCALE='+site_locale)
  if any(any(
      any(path in (n.get(attr) or '') for path in RETIRED_HGQ_MEDIA)
      for attr in ('src','href','poster','data-src')) for n in nodes):
   raise ValueError('HGQ_RUNTIME_CAPTURE_REQUIRED')
  hgq_runtime_media.validate(nodes,site_locale,base_path)
  return {'player_locales':['fr'], 'media_only_links':[]}
 if key!='peaksolo':raise ValueError('BRAND_MEDIA_UNKNOWN_APP='+key)
 if site_locale not in set(PS_PAGE_MEDIA) | set(PS_EXPLICIT_ALTERNATES):
  raise ValueError('PEAKSOLO_RUNTIME_UNSUPPORTED_LOCALE='+site_locale)
 if any(any(path in (node.get(attr) or '') for path in RETIRED_PEAKSOLO_MEDIA)
        for node in nodes for attr in ('src','href','poster','data-src')):
  raise ValueError('PEAKSOLO_RUNTIME_CAPTURE_REQUIRED')
 if any(node.get('data-media-kind')=='BRAND_TEASER'
        or 'brand-teaser' in (node.get('class') or '').split()
        or node.get('data-brand-link') is not None
        or node.get('data-brand-fallback') is not None
        for node in nodes):
  raise ValueError('PEAKSOLO_BRAND_MEDIA_FORBIDDEN')
 other_videos=[node for node in nodes if node.tag=='video'
               and node.get('data-peaksolo-runtime') is None]
 if other_videos:raise ValueError('PEAKSOLO_UNATTESTED_VIDEO')
 peaksolo_runtime_media.validate(nodes,site_locale,base_path)
 return {'player_locales':['fr'],'media_only_links':[]}
