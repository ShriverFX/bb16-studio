from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app_runtime_media as media
import product_pages
import site_i18n


def nodes(markup: str):
    return list(site_i18n.walk(site_i18n.parse(markup)))


class AppRuntimeMediaTests(unittest.TestCase):
    def test_convertair_player_is_a_pinned_real_capture(self):
        from validate_site import VIDEO_MAX
        clip = media.load("convertair")[0]
        self.assertEqual(clip["media_kind"], "RUNTIME_CAPTURE")
        self.assertEqual(clip["capture_environment"], "ANDROID_EMULATOR")
        self.assertEqual(clip["capture_scope"], "REUSED_DEMONSTRATION")
        self.assertTrue(clip["synthetic_data"])
        self.assertEqual(clip["source_sha256"], "47fda9698962b5596d22cc99b2caf83d63651cf6d093d7a301bee83b2fae9f86")
        self.assertLess((media.ROOT / clip["video"]).stat().st_size, VIDEO_MAX)
        text = media.render("convertair", "Écran de fusion", "Capture réelle de ConvertAir", base="/")
        media.validate(nodes(text), "convertair", "/")
        self.assertIn('controls playsinline preload="none"', text)
        self.assertNotIn("autoplay", text)
        self.assertNotIn(" loop", text)
        self.assertNotIn(" muted", text)

    def test_doccipher_fails_closed_to_no_runtime_player(self):
        self.assertEqual(media.load("doccipher"), [])
        self.assertEqual(media.render("doccipher", "DocCipher", "Capture réelle de DocCipher"), "")
        media.validate([], "doccipher")

    def test_hash_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "content").mkdir()
            manifest = json.loads(media.MANIFEST_PATH.read_text(encoding="utf-8"))
            clip = manifest["apps"]["convertair"]["clips"][0]
            for key in ("video", "poster"):
                target = root / clip[key]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((media.ROOT / clip[key]).read_bytes())
            (root / "content/apps-runtime-media.json").write_text(
                json.dumps(manifest), encoding="utf-8")
            (root / clip["video"]).write_bytes(b"corrupt")
            with patch.object(media, "ROOT", root), patch.object(
                    media, "MANIFEST_PATH", root / "content/apps-runtime-media.json"):
                with self.assertRaisesRegex(ValueError, "APP_RUNTIME_MEDIA_INVALID"):
                    media.load("convertair")

    def test_manifest_rejects_nested_paths_and_unsafe_ids(self):
        data = json.loads(media.MANIFEST_PATH.read_text(encoding="utf-8"))
        for field, value in (
            ("id", "../merge"),
            ("video", "assets/video/convertair/runtime-merge-fr.mp4/extra"),
            ("source_filename", "private/path/source.mp4"),
        ):
            broken = json.loads(json.dumps(data))
            broken["apps"]["convertair"]["clips"][0][field] = value
            with tempfile.TemporaryDirectory() as folder:
                manifest = Path(folder) / "manifest.json"
                manifest.write_text(json.dumps(broken), encoding="utf-8")
                with patch.object(media, "MANIFEST_PATH", manifest):
                    with self.subTest(field=field), self.assertRaisesRegex(
                            ValueError, "APP_RUNTIME_PATH_OR_SOURCE_INVALID"):
                        media.load("convertair")

    def test_player_contract_rejects_autoplay_and_missing_proof_figure(self):
        valid = media.render("convertair", "Fusion", "Capture réelle de ConvertAir", base="/")
        with self.assertRaisesRegex(ValueError, "APP_RUNTIME_PLAYER_INVALID"):
            media.validate(nodes(valid.replace(" controls", " autoplay controls")), "convertair", "/")
        with self.assertRaisesRegex(ValueError, "APP_RUNTIME_FIGURE_COUNT"):
            media.validate(nodes(valid.replace(' data-media-kind="RUNTIME_CAPTURE"', "")), "convertair", "/")

    def test_unrelated_runtime_figure_does_not_collide(self):
        valid = media.render("convertair", "Fusion", "Capture réelle de ConvertAir", base="/")
        other = '<figure data-media-kind="RUNTIME_CAPTURE"><video></video></figure>'
        media.validate(nodes(valid + other), "convertair", "/")

    def test_standard_pages_show_only_runtime_video_or_fixed_screens(self):
        config = json.loads((media.ROOT / "site.config.json").read_text(encoding="utf-8"))
        convertair = product_pages.product_body("convertair", config)
        doccipher = product_pages.product_body("doccipher", config)
        self.assertEqual(convertair.count("<video"), 1)
        self.assertEqual(convertair.count('data-app-runtime="convertair-runtime-merge"'), 1)
        self.assertNotIn("data-src=", convertair)
        self.assertNotIn("data-hover-video", convertair)
        self.assertNotIn("aperçu animé", convertair)
        self.assertNotIn("<video", doccipher)
        self.assertNotIn("data-src=", doccipher)
        self.assertNotIn("data-hover-video", doccipher)


if __name__ == "__main__":
    unittest.main()
