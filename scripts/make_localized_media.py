"""Explicit import of real localized screenshots; never translates/retouches pixels.

Source repositories are read-only. Normal builds use the committed derivatives.
Animations are presentation clips of still screenshots, not runtime recordings.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import product_pages as p
import make_media as media
import site_i18n

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app',choices=['convertair','doccipher'])
    parser.add_argument('--locales',nargs='+')
    parser.add_argument('--output-root',type=Path,required=True,help='Existing app capture directory; read only')
    parser.add_argument('--evidence-dir',type=Path,required=True)
    args=parser.parse_args()
    locales=args.locales or [x for x in site_i18n.LOCALES if x!='fr']
    if not all(x in site_i18n.LOCALES and x!='fr' for x in locales): raise SystemExit('INVALID_LOCALE')
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg: raise SystemExit('FFMPEG_NOT_FOUND')
    sources={k:v for k,v in p.SCREENS.items() if v[0]==args.app}
    videos={k:v for k,v in p.VIDEOS.items() if '/'+args.app+'/' in k}
    args.evidence_dir.mkdir(parents=True,exist_ok=True)
    manifest_path=args.evidence_dir/f'media-{args.app}.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'app':args.app,'files':{}}
    manifest['proof']='HISTORICAL_EMULATOR_INTEGRATION_CAPTURE_DERIVATIVES' if args.app=='convertair' else 'HOST_WIDGET_CAPTURE_DERIVATIVES'
    manifest['not_proven']=['current physical device','current Store behavior','interaction video']
    for locale in locales:
        mapping={k:k.replace('/'+args.app+'/', '/'+args.app+'/'+locale+'/') for k in sources}
        for original,(app,source) in sources.items():
            local_source=args.output_root/locale/source.name
            if not local_source.is_file(): raise SystemExit('MISSING_SOURCE:'+str(local_source))
            key=mapping[original]
            p.SCREENS[key]=(app,local_source)
            digest=sha(local_source)
            old=manifest['files'].get(key,{})
            target=ROOT/key
            if old.get('source_sha256')!=digest or not target.exists() or old.get('sha256')!=sha(target):
                media.make_screen(key)
            manifest['files'][key]={'source':str(local_source),'source_sha256':digest,'sha256':sha(target),'bytes':target.stat().st_size,'locale':locale}
        # Only disposable files inside the explicitly named evidence directory.
        with tempfile.TemporaryDirectory(prefix='frames-',dir=args.evidence_dir) as temporary:
            for original,segments in videos.items():
                key=original.replace('/'+args.app+'/', '/'+args.app+'/'+locale+'/')
                translated=[(mapping[source],mode) for source,mode in segments]
                fingerprints=[manifest['files'][source]['source_sha256'] for source,_ in translated]
                old=manifest['files'].get(key,{})
                target=ROOT/key
                if old.get('source_hashes')!=fingerprints or not target.exists() or old.get('sha256')!=sha(target):
                    media.make_video(key,translated,ffmpeg,Path(temporary))
                manifest['files'][key]={'source_hashes':fingerprints,'sha256':sha(target),'bytes':target.stat().st_size,'locale':locale,'kind':'animated_stills'}
        manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f'MEDIA_LOCALE_OK={args.app}:{locale}',flush=True)
    print('MEDIA_FILES='+str(len(manifest['files'])),flush=True)

if __name__=='__main__': main()
