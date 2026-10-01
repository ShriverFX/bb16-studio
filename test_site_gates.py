#!/usr/bin/env python3
"""Negative mutation tests for the publication and security claim gates."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import export_site
import validate_site


class SiteGateMutationTests(unittest.TestCase):
    def assert_removal_is_rejected(
        self, page: str, phrase: str, expected_error: str
    ) -> None:
        target = (validate_site.SITE / page).resolve()
        original_read_text = Path.read_text

        def mutated_read_text(path: Path, *args, **kwargs) -> str:
            text = original_read_text(path, *args, **kwargs)
            if path.resolve() == target:
                self.assertIn(phrase, text)
                return text.replace(phrase, "")
            return text

        with patch.object(Path, "read_text", new=mutated_read_text):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(SystemExit, expected_error):
                    validate_site.main()

    def test_doccipher_privacy_security_boundaries_are_mandatory(self) -> None:
        phrases = (
            "confirmation de l'action irréversible",
            "Seule la saisie exacte du PIN de panique armé déclenche ensuite",
            "ne garantit pas l'écrasement physique du stockage",
            "documentée publiquement",
            "après la protection réussie d'un document ou la réussite d'une sauvegarde",
            "Aucun document, coffre, PIN ou texte saisi ne passe par ce canal",
            "confirmation of the irreversible action",
            "Only entering the exact armed panic PIN then triggers",
            "does not guarantee physical overwriting of storage",
            "publicly documented",
            "after a document has been protected successfully or a backup has completed successfully",
            "No document, vault, PIN or user-entered text passes through this channel",
        )
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assert_removal_is_rejected(
                    "doccipher-privacy.html",
                    phrase,
                    "MISSING_PRIVACY_TEXT=doccipher-privacy.html",
                )

    def test_doccipher_product_safety_disclosure_is_mandatory(self) -> None:
        for phrase in (
            "confirmation de l'action irréversible",
            "La fonction est documentée publiquement",
            "Seule la saisie exacte du PIN de panique armé déclenche cette action",
        ):
            with self.subTest(phrase=phrase):
                self.assert_removal_is_rejected(
                    "doccipher.html", phrase, "MISSING_PANIC_SOON_BLOCK"
                )

    def test_convertair_review_privacy_boundaries_are_mandatory(self) -> None:
        phrases = (
            "troisième résultat réussi réellement affiché",
            "jamais faite au démarrage, pendant un traitement, après une erreur ou après un lot partiellement réussi",
            "séparées d'au moins 60 jours",
            "si le service est indisponible ou échoue, l'application reste silencieuse",
            "ConvertAir ne reçoit ni note ni commentaire",
            "Aucun document, image, texte reconnu ou contenu saisi n'est transmis par cet appel",
            "geste manuel séparé",
            "il n'utilise ni le compteur de succès ni le délai de 60 jours",
            "third successful result actually shown",
            "never makes this request at startup, during processing, after an error or after a partially successful batch",
            "at least 60 days apart",
            "if the service is unavailable or fails, the app stays silent",
            "ConvertAir receives neither a rating nor a comment",
            "No document, image, recognised text or user-entered content is sent by this call",
            "separate manual gesture",
            "it uses neither the success counter nor the 60-day delay",
        )
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assert_removal_is_rejected(
                    "convertair-privacy.html",
                    phrase,
                    "MISSING_PRIVACY_TEXT=convertair-privacy.html",
                )

    def test_convertair_product_review_claim_is_mandatory(self) -> None:
        self.assert_removal_is_rejected(
            "convertair.html",
            "Après un résultat réussi affiché",
            "MISSING_CONVERTAIR_REVIEW_CLAIM",
        )

    def test_every_store_listing_stays_unpublished_for_coming_soon(self) -> None:
        config = json.loads(
            (validate_site.SITE / "site.config.json").read_text(encoding="utf-8")
        )
        for key in ("convertair", "doccipher", "hgq"):
            with self.subTest(key=key):
                mutated = copy.deepcopy(config)
                mutated["store_listings"][key]["published"] = True
                with self.assertRaisesRegex(
                    SystemExit, f"COMING_SOON_MARKED_PUBLISHED={key}"
                ):
                    validate_site.validate_products(mutated, mutated["base_path"])

    def test_export_target_is_exactly_site_directory(self) -> None:
        self.assertEqual(export_site.resolve_output("_site"), export_site.SITE / "_site")
        for unsafe in (".git", ".", "..", "assets", "_site/../.git", "_SITE"):
            with self.subTest(unsafe=unsafe):
                with self.assertRaisesRegex(SystemExit, "UNSAFE_EXPORT_OUTPUT"):
                    export_site.resolve_output(unsafe)

    def test_export_manifest_is_exact_and_contains_branding_webp(self) -> None:
        names = {
            path.relative_to(export_site.SITE).as_posix()
            for path in export_site.publication_files()
        }
        self.assertEqual(len(names), 73)
        self.assertIn("assets/branding/bb16-studio-logo-light-256.webp", names)
        self.assertIn("assets/branding/bb16-studio-logo-dark-256.webp", names)
        for forbidden in (
            "build_site.py",
            "export_site.py",
            "product_pages.py",
            "site.config.json",
            "test_site_gates.py",
            "validate_site.py",
        ):
            self.assertNotIn(forbidden, names)

    def test_external_css_resources_are_rejected(self) -> None:
        samples = (
            'body { background: url("https://example.invalid/pixel"); }',
            'body { background: URL("https://example.invalid/pixel"); }',
            '@import "https://example.invalid/font.css";',
            '@import url("//example.invalid/theme.css");',
        )
        source = export_site.SITE / "_site" / "styles.css"
        for css in samples:
            with self.subTest(css=css):
                with self.assertRaisesRegex(SystemExit, "EXTERNAL_CSS_RESOURCE"):
                    validate_site.validate_css_resources(css)
                links = export_site.css_resource_links(css)
                self.assertTrue(links)
                for link in links:
                    with self.assertRaisesRegex(
                        SystemExit, "EXPORT_EXTERNAL_CSS_RESOURCE"
                    ):
                        export_site.css_local_target(
                            link, "/bb16-studio/", source, source.parent
                        )

    def test_windows_backslash_traversal_is_rejected(self) -> None:
        source = export_site.SITE / "_site" / "styles.css"
        with self.assertRaisesRegex(SystemExit, "EXPORT_LINK_BACKSLASH"):
            export_site.local_target(
                r"..\site.config.json",
                "/bb16-studio/",
                source,
                source.parent,
            )
        with self.assertRaisesRegex(SystemExit, "BAD_CSS_RESOURCE_PATH"):
            validate_site.validate_css_resources(
                r'body { background: url("..\site.config.json"); }'
            )

    def test_existing_export_with_unexpected_content_is_not_removed(self) -> None:
        expected = export_site.publication_files()
        export_site.validate_disposable_output(export_site.SITE / "_site", expected)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            unexpected = output / "owner-proof.txt"
            unexpected.write_text("preserve", encoding="utf-8")
            with self.assertRaisesRegex(
                SystemExit, "EXPORT_OUTPUT_NOT_DISPOSABLE=owner-proof.txt"
            ):
                export_site.validate_disposable_output(output, expected)
            self.assertEqual(unexpected.read_text(encoding="utf-8"), "preserve")


if __name__ == "__main__":
    unittest.main()
