"""Encoding regression checks without pretending to certify native fluency."""
import json,unittest
import site_i18n as i
from validate_i18n import validate_reviewed_zh_hant_text,validate_catalog_content

class TraditionalChineseRepairTests(unittest.TestCase):
 def test_reviewed_catalogue_matches_current_units_and_keeps_all_existing_guards(self):
  units=json.loads((i.ROOT/'locales/source.json').read_text(encoding='utf-8'))
  data=json.loads((i.ROOT/'locales/zh-Hant.json').read_text(encoding='utf-8'))
  self.assertEqual(set(data),set(units))
  validate_catalog_content('zh-Hant',data,units)

 def test_internal_lossy_question_mark_and_replacement_character_are_rejected(self):
  key='79a9890fc572';units={key:{'source':'Votre activité.<br>Vos repères.'}}
  for bad in ('您的??。<br>您的?索。','您的業務。<br>您的\ufffd索。'):
   with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'ZH_HANT_ENCODING_DAMAGED'):
    validate_reviewed_zh_hant_text({key:bad},units)

 def test_real_question_punctuation_is_retained(self):
  key='0343c9cfb6fd';units={key:{'source':'Où sont les captures de PeakSolo ?'}}
  for good in ('PeakSolo 的畫面截圖在哪裡？','PeakSolo 的畫面截圖在哪裡?'):
   validate_reviewed_zh_hant_text({key:good},units)
  with self.assertRaisesRegex(ValueError,'ZH_HANT_ENCODING_DAMAGED'):
   validate_reviewed_zh_hant_text({key:'PeakSolo 的截?圖在哪裡？'},units)

if __name__=='__main__':unittest.main()
