"""Local-only draft preview while translation/media batches are in progress.

Missing locales remain visibly absent; never used by build_site or export_site.
"""
from pathlib import Path
import argparse
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import build_site
import site_i18n
p=argparse.ArgumentParser()
p.add_argument('locales',nargs='+')
args=p.parse_args()
config=build_site.read_config()
sources=build_site.pages(dict(config,base_path='/'))
out=ROOT/'_apercu'/'i18n-draft'
for name,text in site_i18n.build(sources,config,preview_locales=args.locales).items():
    target=out/name; target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(text,encoding='utf-8')
print(json.dumps({'status':'LOCAL_PREVIEW_ONLY','directory':str(out),'locales':args.locales}))
