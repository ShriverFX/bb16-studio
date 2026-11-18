import unittest

import hgq_showcase
import hgq_warmup_media


class HgqWarmupTest(unittest.TestCase):
    def test_audio_is_pinned_first_party_and_never_autoplays(self):
        hgq_warmup_media.validate_assets()
        markup = hgq_warmup_media.render()
        self.assertEqual(markup.count('<audio '), 3)
        self.assertEqual(markup.count('preload="none"'), 3)
        self.assertEqual(markup.count('data-src="assets/audio/hgq/'), 3)
        self.assertNotIn(' autoplay', markup)
        self.assertNotIn(' src=', markup)
        self.assertIn('data-warmup-audio="music"', markup)
        self.assertIn(' loop', markup)

    def test_six_locales_keep_progressive_question_and_game_sequence(self):
        self.assertEqual(set(hgq_showcase.WARMUP_COPY), {'fr', 'en', 'es', 'pt', 'ja', 'ko'})
        for locale in hgq_showcase.WARMUP_COPY:
            with self.subTest(locale=locale):
                markup = hgq_showcase.render(locale)
                self.assertEqual(markup.count('data-warmup-answer '), 4)
                self.assertEqual(markup.count('data-correct="true"'), 1)
                self.assertEqual(markup.count('data-correct="false"'), 3)
                self.assertIn('data-warmup-start', markup)
                self.assertIn('data-warmup-start hidden', markup)
                self.assertIn('data-warmup-restart', markup)
                self.assertIn('data-warmup-sound', markup)
                self.assertIn('>FIGHT</div>', markup)
                self.assertIn('<strong>GAME OVER</strong>', markup)
                self.assertIn('Quartier Arcade', markup)
                # Without JavaScript the real question and all native details remain visible/usable.
                self.assertIn('<div data-warmup-question>', markup)
                self.assertNotIn('<div data-warmup-question hidden', markup)


if __name__ == '__main__':
    unittest.main()
