"""Explicit locale selection for real brand masters; never app runtime proof.

Captions are reused from the reviewed multilingual media package and injected
after page translation. Sparse product routes cover each app language; regional
and script media gaps remain explicit links rather than silent fallback.
"""
from pathlib import Path
from html import escape,unescape
import hashlib,json
import hgq_runtime_media
import peaksolo_runtime_media

SITE=Path(__file__).resolve().parent
APP_LANGUAGES={
 'hgq':('fr','en','es','pt','ja','ko'),
 'peaksolo':('fr','en','es','pt','de','it','nl','ru','uk','pl','ro','sv','cs','el','tr','ar','he','fa','ur','hi','bn','id','ms','vi','th','ja','ko','zh'),
}
AUTONYMS={'fr':'Français','en':'English','es':'Español','pt':'Português','de':'Deutsch','it':'Italiano','nl':'Nederlands','ru':'Русский','uk':'Українська','pl':'Polski','ro':'Română','sv':'Svenska','cs':'Čeština','el':'Ελληνικά','tr':'Türkçe','ar':'العربية','he':'עברית','fa':'فارسی','ur':'اردو','hi':'हिन्दी','bn':'বাংলা','id':'Bahasa Indonesia','ms':'Bahasa Melayu','vi':'Tiếng Việt','th':'ไทย','ja':'日本語','ko':'한국어','zh':'简体中文'}
PS_PAGE_MEDIA={code:code for code in APP_LANGUAGES['peaksolo']}
PS_PAGE_MEDIA['zh-Hans']='zh'
PS_EXPLICIT_ALTERNATES={'pt-BR':('pt','pt'),'zh-Hant':('zh-Hans','zh')}
PS_EXTRA_LANGUAGES=tuple(code for code in APP_LANGUAGES['peaksolo'] if code not in set(PS_PAGE_MEDIA.values()))
LOCALIZED_BRAND_TEASERS={app:{code:{'video':f'assets/video/brand/{app}-presentation-{code}.mp4','poster':f'assets/branding/{app}-presentation-{code}.webp'} for code in codes} for app,codes in APP_LANGUAGES.items()}
BRAND_TEASERS={app:spec['fr'] for app,spec in LOCALIZED_BRAND_TEASERS.items()}
RETIRED_HGQ_MEDIA = frozenset(path for media in LOCALIZED_BRAND_TEASERS['hgq'].values() for path in media.values())
MEDIA_FILES=[path for media in LOCALIZED_BRAND_TEASERS['peaksolo'].values() for path in media.values()]
FRENCH_CAPTION='Présentation de marque de PeakSolo.'

def language_tag(code):return 'zh-Hans' if code=='zh' else code
def direction(code):return 'rtl' if code in {'ar','he','fa','ur'} else 'ltr'
def evidence():return json.loads((SITE/'content/brand-teaser-provenance-20261102.json').read_text(encoding='utf-8'))
def caption(code):return FRENCH_CAPTION if code=='fr' else evidence()['caption_labels'][code]
def caption_id(app,code):return app+'-brand-caption'+('' if code=='fr' else '-'+code)

def brand_teaser(key,locale='fr'):
 if key=='hgq':raise ValueError('HGQ_RUNTIME_CAPTURE_REQUIRED')
 spec=LOCALIZED_BRAND_TEASERS[key][locale]  # Unknown locale fails instead of French fallback.
 ident=caption_id(key,locale);tag=language_tag(locale)
 fallback='Votre navigateur ne permet pas de lire cette vidéo.' if locale=='fr' else ('HGQ' if key=='hgq' else 'PeakSolo')+' · '+AUTONYMS[locale]
 return f'<figure class="hero-device brand-teaser" data-media-kind="BRAND_TEASER" data-media-locale="{locale}" lang="{tag}" dir="{direction(locale)}"><video src="{spec["video"]}" poster="{spec["poster"]}" controls playsinline preload="none" width="360" height="640" style="max-width:100%;height:auto" aria-describedby="{ident}" lang="{tag}" data-media-locale="{locale}">{escape(fallback)}</video><figcaption id="{ident}" lang="{tag}">{escape(caption(locale),quote=False)}</figcaption></figure>'

def peaksolo_media_section(site_locale):
 if site_locale in PS_PAGE_MEDIA:
  body=brand_teaser('peaksolo',PS_PAGE_MEDIA[site_locale])
 elif site_locale in PS_EXPLICIT_ALTERNATES:
  page,code=PS_EXPLICIT_ALTERNATES[site_locale]
  body=f'<p><a href="/{page}/peaksolo.html#presentation-video" hreflang="{language_tag(code)}" lang="{language_tag(code)}" data-brand-fallback="{code}">PeakSolo · {escape(AUTONYMS[code])}</a></p>'
 else:raise ValueError('NO_EXPLICIT_BRAND_MEDIA_LOCALE='+site_locale)
 if site_locale=='fr':
  # Kept for compatibility if a reviewed language ever has media before a page.
  # Current supported languages all have a route; this collection is empty.
  for code in PS_EXTRA_LANGUAGES:
   spec=LOCALIZED_BRAND_TEASERS['peaksolo'][code];label='PeakSolo · '+AUTONYMS[code]
   body+=f'<details class="faq-item brand-language"><summary lang="{language_tag(code)}" dir="{direction(code)}">{escape(AUTONYMS[code])}</summary><a href="{spec["video"]}" lang="{language_tag(code)}" data-brand-link="{code}" data-media-kind="BRAND_TEASER"><img src="{spec["poster"]}" width="180" height="320" loading="lazy" decoding="async" alt="{escape(label,quote=True)}"><span>{escape(label)}</span></a></details>'
 return '<section class="section" id="presentation-video" aria-label="PeakSolo"><div class="container">'+body+'</div></section>'

def inject_peaksolo(tree,site_locale):
 import site_i18n as i
 teaser=peaksolo_media_section(site_locale).replace('src="assets/','src="/assets/').replace('poster="assets/','poster="/assets/').replace('href="assets/','href="/assets/')
 fragment=peaksolo_runtime_media.render(site_locale)+teaser
 for parent in i.walk(tree):
  for pos,child in enumerate(parent.children):
   if isinstance(child,i.Node) and child.tag=='section' and child.get('id')=='presentation':
    parent.children[pos+1:pos+1]=i.parse(fragment).children;return
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
 proof=evidence()
 if not (proof.get('media_kind')=='BRAND_TEASER' and proof.get('runtime_capture') is False and proof.get('runtime') is False and proof.get('class')=='BRAND_TEASER'):
  raise ValueError('BAD_BRAND_MEDIA_CLASSIFICATION')
 if set(proof['files'])!=set(MEDIA_FILES) | RETIRED_HGQ_MEDIA:raise ValueError('BRAND_MEDIA_PROVENANCE_COVERAGE')
 # A matching URL alone is not sufficient; the bytes must match reviewed media.
 for name in MEDIA_FILES:
  row=proof['files'][name];p=SITE/name
  if p.stat().st_size!=row['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('BRAND_MEDIA_HASH_CHANGED='+name)
 expected=[PS_PAGE_MEDIA[site_locale]] if site_locale in PS_PAGE_MEDIA else []
 peaksolo_runtime_media.validate(nodes,site_locale,base_path)
 videos=[n for n in nodes if n.tag=='video' and n.get('data-peaksolo-runtime') is None]
 if len(videos)!=len(expected):raise ValueError('BRAND_MEDIA_VIDEO_COUNT='+key+':'+site_locale)
 actual=[]
 for video in videos:
  code=video.get('data-media-locale');actual.append(code)
  if code not in expected:raise ValueError('BRAND_MEDIA_WRONG_LOCALE='+str(code))
  spec=LOCALIZED_BRAND_TEASERS[key][code];attrs=dict(video.attrs)
  if video.get('src')!=base_path+spec['video'] or video.get('poster')!=base_path+spec['poster']:raise ValueError('BRAND_MEDIA_WRONG_SOURCE='+code)
  if 'autoplay' in attrs or 'loop' in attrs or 'controls' not in attrs or 'playsinline' not in attrs or video.get('preload')!='none':raise ValueError('BRAND_MEDIA_PLAYBACK='+code)
  if video.get('lang')!=language_tag(code) or video.get('aria-describedby')!=caption_id(key,code):raise ValueError('BRAND_MEDIA_LANGUAGE_CAPTION='+code)
  caps=[n for n in nodes if n.tag=='figcaption' and n.get('id')==caption_id(key,code)]
  if len(caps)!=1 or unescape(caps[0].inner())!=caption(code):raise ValueError('BRAND_MEDIA_CAPTION_CHANGED='+code)
 if set(actual)!=set(expected) or len(actual)!=len(set(actual)):raise ValueError('BRAND_MEDIA_DUPLICATE_OR_MISSING_LOCALE')
 figures=[n for n in nodes if n.tag=='figure' and n.get('class')=='hero-device brand-teaser']
 if len(figures)!=len(expected) or any(n.get('data-media-kind')!='BRAND_TEASER' for n in figures):raise ValueError('BAD_BRAND_MEDIA_CLASSIFICATION')
 if key=='peaksolo':
  links=[n for n in nodes if n.tag=='a' and n.get('data-brand-link')]
  extras=list(PS_EXTRA_LANGUAGES) if site_locale=='fr' else []
  if sorted(n.get('data-brand-link') for n in links)!=sorted(extras):raise ValueError('BRAND_MEDIA_EXTRA_LANGUAGES')
  for link in links:
   code=link.get('data-brand-link');spec=LOCALIZED_BRAND_TEASERS['peaksolo'][code]
   if link.get('href')!=base_path+spec['video'] or link.get('lang')!=language_tag(code) or link.get('data-media-kind')!='BRAND_TEASER':raise ValueError('BRAND_MEDIA_EXTRA_LINK='+code)
  alternates=[n for n in nodes if n.tag=='a' and n.get('data-brand-fallback')]
  if site_locale in PS_EXPLICIT_ALTERNATES:
   page,code=PS_EXPLICIT_ALTERNATES[site_locale]
   if len(alternates)!=1 or alternates[0].get('href')!=base_path+page+'/peaksolo.html#presentation-video' or alternates[0].get('lang')!=language_tag(code):raise ValueError('BRAND_MEDIA_EXPLICIT_ALTERNATE')
  elif alternates:raise ValueError('BRAND_MEDIA_UNEXPECTED_FALLBACK')
 return {'player_locales':expected,'media_only_links':list(PS_EXTRA_LANGUAGES) if key=='peaksolo' and site_locale=='fr' else []}
