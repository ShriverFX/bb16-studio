#!/usr/bin/env python3
"""Negative mutation tests for the publication and security claim gates."""

from __future__ import annotations

import contextlib
import copy
import io
import html
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import export_site
import validate_site
import build_site
import app_runtime_media


class SiteGateMutationTests(unittest.TestCase):
    def test_retired_media_cannot_return_to_export(self) -> None:
        self.assertTrue({"assets/screens/convertair/paywall.webp", "assets/video/convertair/premium.mp4"} <= export_site.RETIRED_MEDIA)
        for entry in export_site.RETIRED_MEDIA:
            with self.subTest(entry=entry), patch.object(export_site, "ASSET_FILES", export_site.ASSET_FILES + (entry,)):
                with self.assertRaisesRegex(SystemExit, "RETIRED_MEDIA_EXPORT"):
                    export_site.publication_files()

    def test_retired_media_and_unattested_video_are_rejected_in_pages(self) -> None:
        texts = {name: (validate_site.SITE / name).read_text(encoding="utf-8") for name in validate_site.PAGES}
        validate_site.validate_current_media_and_hgq_legal(texts)
        for entry in export_site.RETIRED_MEDIA:
            edited = {**texts, "hgq.html": texts["hgq.html"] + f'<img src="/{entry}">'}
            with self.subTest(entry=entry), self.assertRaisesRegex(SystemExit, "RETIRED_MEDIA_REFERENCE"):
                validate_site.validate_current_media_and_hgq_legal(edited)
        with self.assertRaisesRegex(SystemExit, "HGQ_UNATTESTED_VIDEO"):
            validate_site.validate_current_media_and_hgq_legal({**texts, "hgq.html": texts["hgq.html"] + '<video></video>'})

    def test_hgq_canonical_bodies_and_links_are_pinned(self) -> None:
        texts = {name: (validate_site.SITE / name).read_text(encoding="utf-8") for name in validate_site.PAGES}
        privacy = texts["hgq-privacy.html"]
        self.assertNotIn("indépendant et non commercial", privacy)
        reverted = privacy.replace("indépendant sur la culture", "indépendant et non commercial sur la culture")
        self.assertNotEqual(reverted, privacy)
        with self.assertRaisesRegex(SystemExit, "HGQ_CANONICAL_BODY_CHANGED=hgq-privacy.html"):
            validate_site.validate_current_media_and_hgq_legal({**texts, "hgq-privacy.html": reverted})
        for page in validate_site.HGQ_CANONICAL_BODY_SHA256:
            changed = texts[page].replace("<!-- HGQ_CANONICAL_BEGIN -->", "<!-- HGQ_CANONICAL_BEGIN -->Changed")
            with self.subTest(page=page), self.assertRaisesRegex(SystemExit, "HGQ_CANONICAL_BODY_CHANGED"):
                validate_site.validate_current_media_and_hgq_legal({**texts, page: changed})
        for link in ("hgq-privacy.html", "hgq-account-deletion.html"):
            changed = texts["hgq.html"].replace('href="/' + link + '"', 'href="/other.html"').replace('href="' + link + '"', 'href="other.html"')
            with self.subTest(link=link), self.assertRaisesRegex(SystemExit, "HGQ_DEDICATED_LEGAL_LINK_MISSING"):
                validate_site.validate_current_media_and_hgq_legal({**texts, "hgq.html": changed})

    def test_hgq_unverified_player_or_link_is_rejected(self) -> None:
        text = (validate_site.SITE / 'hgq.html').read_text(encoding='utf-8')
        validate_site.validate_brand_teaser(text, 'hgq')
        for injected in ('<video src="/unverified-gameplay.mp4"></video>',
                         '<a href="/assets/video/brand/hgq-presentation-fr.mp4">Voir</a>'):
            with self.subTest(injected=injected), self.assertRaisesRegex(SystemExit, 'HGQ_UNATTESTED_VIDEO'):
                validate_site.validate_brand_teaser(text + injected, 'hgq')

    def test_hgq_admob_disclosure_cannot_lose_sdk_data_or_purposes(self) -> None:
        texts = {name: (validate_site.SITE / name).read_text(encoding="utf-8") for name in validate_site.PAGES}
        privacy = texts["hgq-privacy.html"]
        for fact in (
            "L'adresse IP, qui peut servir à estimer une localisation approximative.",
            "Les interactions avec l'application et les publicités",
            "Des diagnostics de performance de l'application et du SDK publicitaire",
            "Des identifiants de l'appareil ou de l'application",
            "Google utilise ces données pour la publicité, l'analyse et la prévention de la fraude.",
            "Ces diagnostics publicitaires sont distincts des rapports Firebase Crashlytics",
            "Les formulaires Google UMP permettent d'exprimer tes choix lorsqu'un consentement est requis",
            "Gérer mon consentement lorsque ces options sont disponibles.",
        ):
            with self.subTest(fact=fact):
                self.assertIn(fact, privacy)
                with self.assertRaisesRegex(SystemExit, "HGQ_CANONICAL_BODY_CHANGED=hgq-privacy.html"):
                    validate_site.validate_current_media_and_hgq_legal({**texts, "hgq-privacy.html": privacy.replace(fact, "")})

    def test_legacy_contacts_remain_forbidden_even_in_legal_wrappers(self) -> None:
        original_read_text = Path.read_text
        for page in ("hgq.html", "hgq-privacy.html", "hgq-account-deletion.html"):
            for contact in ("shriverfx" + "@gmail.com", "support" + "@hgq.app", "legal" + "@hgq.app"):
                def edited_read_text(path: Path, *args, **kwargs) -> str:
                    text = original_read_text(path, *args, **kwargs)
                    return text + "<p>" + contact + "</p>" if path == validate_site.SITE / page else text
                with self.subTest(page=page, contact=contact), patch.object(Path, "read_text", new=edited_read_text):
                    with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(SystemExit, "FORBIDDEN_PUBLIC_TEXT"):
                        validate_site.main()

    def test_custom_domain_contract_rejects_inconsistent_config_and_cname(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            cname = folder / "CNAME"
            config = {"custom_domain": "bb16studio.com", "site_url": "https://bb16studio.com", "base_path": "/"}
            cname.write_text("bb16studio.com\n", encoding="utf-8")
            with patch.object(validate_site, "SITE", folder):
                validate_site.validate_custom_domain(config)
                for key, value, error in (
                    ("custom_domain", "https://bb16studio.com", "BAD_CUSTOM_DOMAIN"),
                    ("custom_domain", "bb16studio.com\nother.invalid", "BAD_CUSTOM_DOMAIN"),
                    ("site_url", "https://shriverfx.github.io", "CUSTOM_DOMAIN_ORIGIN_OR_BASE_MISMATCH"),
                    ("base_path", "/bb16-studio/", "CUSTOM_DOMAIN_ORIGIN_OR_BASE_MISMATCH"),
                ):
                    with self.subTest(key=key, value=value), self.assertRaisesRegex(SystemExit, error):
                        validate_site.validate_custom_domain({**config, key: value})
                for value in ("other.invalid\n", "bb16studio.com\nother.invalid\n"):
                    cname.write_text(value, encoding="utf-8")
                    with self.subTest(cname=value), self.assertRaisesRegex(SystemExit, "CUSTOM_DOMAIN_CNAME_MISMATCH"):
                        validate_site.validate_custom_domain(config)
                cname.unlink()
                with self.assertRaisesRegex(SystemExit, "CUSTOM_DOMAIN_CNAME_MISSING"):
                    validate_site.validate_custom_domain(config)

    def test_j0_technical_privacy_disclosures_are_mandatory(self) -> None:
        for page, phrases in validate_site.PRIVACY_J0_TECHNICAL_REQUIRED.items():
            for phrase in phrases:
                with self.subTest(page=page, phrase=phrase):
                    self.assert_removal_is_rejected(page, phrase, "MISSING_PRIVACY_TEXT=" + page)

    def test_convertair_privacy_rejects_stale_mlkit_and_erasure_overclaims(self) -> None:
        target = (validate_site.SITE / "convertair-privacy.html").resolve()
        original_read_text = Path.read_text
        for phrase in validate_site.CONVERTAIR_PRIVACY_FORBIDDEN:
            def edited_read_text(path: Path, *args, **kwargs) -> str:
                text = original_read_text(path, *args, **kwargs)
                return text + "<p>" + phrase + "</p>" if path.resolve() == target else text

            with self.subTest(phrase=phrase), patch.object(Path, "read_text", new=edited_read_text):
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(
                    SystemExit, "FORBIDDEN_PRIVACY_TEXT=convertair-privacy.html"
                ):
                    validate_site.main()

    def test_social_links_reject_untrusted_destinations(self) -> None:
        for url in (
            "javascript:alert(1)",
            "http://www.instagram.com/bb16studio/",
            "https://www.instagram.com.evil.invalid/bb16studio/",
            "https://www.instagram.com@evil.invalid/bb16studio/",
            "https://user:password@www.instagram.com/bb16studio/",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                build_site.footer({"social_profiles": {"instagram": url}})

    def test_feedback_pages_reject_automatic_collection(self) -> None:
        for page in validate_site.FEEDBACK_PAGES:
            text = (validate_site.SITE / page).read_text(encoding="utf-8")
            validate_site.validate_feedback_markup(text, page)
            for insertion in (
                '<form action="https://example.invalid/collect">',
                '<iframe src="https://example.invalid/collect"></iframe>',
                '<script>fetch("https://example.invalid/collect")</script>',
                '<script src="https://example.invalid/code.js"></script>',
                '<input type="password">',
                '<input type="file">',
            ):
                with self.subTest(page=page, insertion=insertion):
                    with self.assertRaises(SystemExit):
                        validate_site.validate_feedback_markup(text + insertion, page)

    def test_feedback_pages_reject_missing_noindex_and_duplicate_ids(self) -> None:
        for page in validate_site.FEEDBACK_PAGES:
            text = (validate_site.SITE / page).read_text(encoding="utf-8")
            with self.subTest(page=page):
                with self.assertRaisesRegex(SystemExit, "FEEDBACK_INDEXING_NOT_DISABLED"):
                    validate_site.validate_feedback_markup(
                        text.replace('content="noindex,nofollow"', 'content="index,follow"'), page
                    )
                with self.assertRaisesRegex(SystemExit, "FEEDBACK_DUPLICATE_IDS"):
                    validate_site.validate_feedback_markup(text + '<div id="test-form"></div>', page)

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

    def test_security_reservations_do_not_allow_positive_promises(self) -> None:
        texts = {page: html.unescape((validate_site.SITE / page).read_text(encoding="utf-8"))
                 for page in validate_site.PAGES}
        validate_site.validate_security_claims(texts)
        for reservation in validate_site.OVERCLAIM_NEGATIVE_RESERVATIONS:
            positive = reservation.replace("ne garantit pas que", "garantit que").replace(
                "does not guarantee", "guarantees"
            )
            mutated = dict(texts)
            mutated["doccipher.html"] += "<p>" + positive + "</p>"
            with self.subTest(reservation=reservation), self.assertRaisesRegex(SystemExit, "OVERCLAIM="):
                validate_site.validate_security_claims(mutated)
        mutated = dict(texts)
        mutated["index.html"] += "<p>" + validate_site.OVERCLAIM_NEGATIVE_RESERVATIONS[0] + "</p>"
        with self.assertRaisesRegex(SystemExit, "OVERCLAIM="):
            validate_site.validate_security_claims(mutated)

    def test_panic_claims_require_attribution_in_the_same_text_unit(self) -> None:
        texts = {page: html.unescape((validate_site.SITE / page).read_text(encoding="utf-8"))
                 for page in validate_site.PAGES}
        for phrase in (
            "<p>Google Play</p><p>Le coffre leurre est en validation.</p>",
            "<details><summary>Le PIN de panique est prévu.</summary><p>Google Play</p></details>",
        ):
            mutated = dict(texts)
            mutated["doccipher.html"] += phrase
            with self.subTest(phrase=phrase), self.assertRaisesRegex(
                SystemExit, "PANIC_WITHOUT_STORE_ATTRIBUTION="
            ):
                validate_site.validate_security_claims(mutated)

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

    def test_convertair_online_review_access_notice_is_mandatory(self) -> None:
        for phrase in validate_site.CONVERTAIR_REVIEW_ACCESS_REQUIRED:
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

    def test_publication_flags_match_the_dated_reference(self) -> None:
        config = json.loads(
            (validate_site.SITE / "site.config.json").read_text(encoding="utf-8")
        )
        reference = json.loads(validate_site.PUBLICATION_REFERENCE.read_text(encoding="utf-8"))
        validate_site.validate_publication_reference(config, reference)
        for key in ("convertair", "doccipher"):
            with self.subTest(key=key):
                mutated = copy.deepcopy(config)
                mutated["store_listings"][key]["published"] = False
                with self.assertRaisesRegex(
                    SystemExit, f"PUBLICATION_STATE_MISMATCH={key}"
                ):
                    validate_site.validate_publication_reference(mutated, reference)
        for key in ("hgq", "peaksolo"):
            with self.subTest(key=key):
                mutated = copy.deepcopy(config)
                mutated["store_listings"][key] = {"package": "com.example." + key, "published": True}
                with self.assertRaisesRegex(SystemExit, f"COMING_SOON_MARKED_PUBLISHED={key}"):
                    validate_site.validate_publication_reference(mutated, reference)

    def test_publication_reference_cannot_promote_another_package_or_device_proof(self) -> None:
        config = json.loads((validate_site.SITE / "site.config.json").read_text(encoding="utf-8"))
        reference = json.loads(validate_site.PUBLICATION_REFERENCE.read_text(encoding="utf-8"))
        for key in ("convertair", "doccipher"):
            with self.subTest(key=key, mutation="missing"):
                mutated = copy.deepcopy(reference)
                del mutated["applications"][key]
                with self.assertRaisesRegex(SystemExit, "PUBLICATION_REFERENCE_MISSING=" + key):
                    validate_site.validate_publication_reference(config, mutated)
            with self.subTest(key=key, mutation="package"):
                mutated = copy.deepcopy(reference)
                mutated["applications"][key]["package"] = "com.example.other"
                with self.assertRaisesRegex(SystemExit, "PUBLICATION_REFERENCE_MISMATCH=" + key):
                    validate_site.validate_publication_reference(config, mutated)
            with self.subTest(key=key, mutation="runtime"):
                mutated = copy.deepcopy(reference)
                mutated["applications"][key]["runtime_qualification"] = "ALL_DEVICE_TESTS_PASSED"
                with self.assertRaisesRegex(SystemExit, "BAD_PUBLICATION_REFERENCE_SCOPE=" + key):
                    validate_site.validate_publication_reference(config, mutated)

    def test_available_status_belongs_to_each_card_and_hero(self) -> None:
        config = json.loads((validate_site.SITE / "site.config.json").read_text(encoding="utf-8"))
        texts = {page: (validate_site.SITE / page).read_text(encoding="utf-8")
                 for page in ("index.html", "apps.html", "convertair.html", "doccipher.html")}
        validate_site.validate_availability_markup(texts, config["store_listings"])
        needle = '<p class="meta">Disponible sur Google Play</p>'
        for page in ("index.html", "apps.html"):
            text = texts[page]
            self.assertEqual(text.count(needle), 2)
            last = text.rfind(needle)
            edited = text[:last] + '<p class="meta">Bientôt sur Android</p>' + text[last + len(needle):]
            with self.subTest(page=page), self.assertRaisesRegex(SystemExit, f"MISSING_PRODUCT_AVAILABILITY={page}:doccipher"):
                validate_site.validate_availability_markup({**texts, page: edited}, config["store_listings"])
        for key in ("convertair", "doccipher"):
            page = key + ".html"
            edited = texts[page].replace('<span class="status">Disponible sur Google Play</span>',
                                         '<span class="status pending">Disponible sur Google Play</span>')
            self.assertNotEqual(edited, texts[page])
            with self.subTest(key=key), self.assertRaisesRegex(SystemExit, "MISSING_PRODUCT_AVAILABILITY=" + page):
                validate_site.validate_availability_markup({**texts, page: edited}, config["store_listings"])

    def test_prelaunch_pages_reject_offers_store_links_and_missing_peak_privacy_boundaries(self) -> None:
        texts = {
            page: (validate_site.SITE / page).read_text(encoding="utf-8")
            for page in ("peaksolo.html", "peaksolo-privacy.html", "hgq.html")
        }
        for page, text in texts.items():
            with self.subTest(page=page, mutation="price"):
                with self.assertRaisesRegex(SystemExit, "UNVERIFIED_PRELAUNCH_OFFER=" + page):
                    validate_site.validate_prelaunch_pages({**texts, page: text + "<p>9,99 €</p>"})
            with self.subTest(page=page, mutation="play_link"):
                with self.assertRaisesRegex(SystemExit, "UNVERIFIED_PRELAUNCH_OFFER=" + page):
                    validate_site.validate_prelaunch_pages(
                        {**texts, page: text + "https://play.google.com/store/apps/details?id=com.example"}
                    )

        for phrase in (
            'BB16 Studio',
            'bb16studio@gmail.com',
            'SQLCipher',
            'ML Kit',
            'sur votre appareil',
            'sauvegarde portable',
            'pas de connexion Google Drive intégrée ni de synchronisation automatique',
            'Lorsque les achats sont activés dans la version distribuée',
            'RevenueCat',
            "historique d'achat",
            'États-Unis',
            'ne résilie pas un abonnement',
            'Conservation et suppression',
            'Vos droits',
            'CNIL',
        ):
            with self.subTest(page="peaksolo-privacy.html", phrase=phrase):
                edited = texts["peaksolo-privacy.html"].replace(phrase, "")
                with self.assertRaisesRegex(SystemExit, "PEAKSOLO_MISSING_BOUNDARY=" + phrase):
                    validate_site.validate_prelaunch_pages(
                        {**texts, "peaksolo-privacy.html": edited}
                    )

    def test_export_target_is_exactly_site_directory(self) -> None:
        self.assertEqual(export_site.resolve_output("_site"), export_site.SITE / "_site")
        for unsafe in (".git", ".", "..", "assets", "_site/../.git", "_SITE"):
            with self.subTest(unsafe=unsafe):
                with self.assertRaisesRegex(SystemExit, "UNSAFE_EXPORT_OUTPUT"):
                    export_site.resolve_output(unsafe)

    def test_export_manifest_contains_only_attested_app_runtime_media(self) -> None:
        names = {
            path.relative_to(export_site.SITE).as_posix()
            for path in export_site.publication_files()
        }
        runtime = set(export_site.peaksolo_runtime_media.files())
        self.assertEqual({name for name in names if name.startswith((
            "assets/video/peaksolo/runtime-", "assets/screens/peaksolo/runtime-",
        ))}, runtime)
        app_runtime=set(app_runtime_media.files())
        self.assertEqual({name for name in names if name.startswith((
            "assets/video/convertair/runtime-", "assets/screens/convertair/runtime-",
            "assets/video/doccipher/runtime-", "assets/screens/doccipher/runtime-",
        ))},app_runtime)
        self.assertEqual(export_site.presentation_media(),[])
        self.assertFalse(any('doccipher/presentation-v2' in name for name in names))
        self.assertTrue({"presse.html", "presse.json"} <= names)
        self.assertTrue({"assets/branding/convertair-share.jpg", "assets/branding/press-share.jpg"} <= names)
        self.assertTrue({"assets/video/convertair/pt-BR/teaser.mp4", "assets/downloads/kit-brasil.zip"} <= names)
        self.assertNotIn('assets/video/brand/peaksolo-presentation-fr.mp4',names)
        self.assertNotIn('assets/branding/peaksolo-presentation-fr.webp',names)
        self.assertNotIn('assets/video/brand/hgq-presentation-fr.mp4', names)
        self.assertNotIn('assets/branding/hgq-presentation-fr.webp', names)
        self.assertNotIn('assets/branding/hgq-presentation-fr.png', names)
        self.assertNotIn('assets/branding/peaksolo-presentation-fr.png', names)
        self.assertTrue({'i18n.css', 'locale.js', 'ar/convertair.html',
                         'zh-Hant/doccipher-privacy.html',
                         'assets/screens/doccipher/ja/coffre.webp'} <= names)
        self.assertIn("app-ads.txt", names)
        self.assertEqual((export_site.SITE / "app-ads.txt").read_text(encoding="utf-8").strip(),
                         "google.com, pub-7532135517195314, DIRECT, f08c47fec0942fa0")
        self.assertTrue({"hgq-privacy.html", "hgq-account-deletion.html"} <= names)
        self.assertFalse(names & export_site.RETIRED_MEDIA)
        self.assertFalse(names & {"assets/screens/hgq/connexion.webp", "assets/screens/hgq/inscription.webp"})
        self.assertIn("CNAME", names)
        self.assertIn("convertair-test.html", names)
        self.assertIn("doccipher-test.html", names)
        self.assertIn("assets/branding/bb16-studio-logo-light-256.webp", names)
        self.assertIn("assets/branding/bb16-studio-logo-dark-256.webp", names)
        for forbidden in (
            "build_site.py",
            "export_site.py",
            "product_pages.py",
            "site.config.json",
            "test_site_gates.py",
            "validate_site.py",
            "content/hgq-privacy.html",
            "content/hgq-account-deletion.html",
            "content/brand-teaser-provenance-20261102.json",
            "content/peaksolo-runtime-media.json",
            "locales/source.json",
            "locales/en.json",
            "I18N.md",
            "site_i18n.py",
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
