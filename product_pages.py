"""Pages produit premium de ConvertAir, DocCipher et HGQ.

Ce module ne dépend que de la bibliothèque standard : il décrit les pages
(textes, captures, vidéos, prix, FAQ) et produit leur HTML. `build_site.py`
l'enveloppe dans le gabarit commun.

Les médias viennent de VRAIES captures des applications, lues dans leurs
dépôts (voir SCREENS). `make_media.py` (Pillow + ffmpeg, machine source
seulement) les réduit en WebP et en fabrique de courtes vidéos MP4 ; la
génération normale du site n'en a pas besoin et vérifie seulement leur
présence.

HONNÊTETÉ — aucune fonction non publiée n'est présentée comme disponible.
Le code de panique et le coffre leurre de DocCipher (décision D-0051,
IMPLEMENTED_LOCAL_UNVALIDATED) sont annoncés pour le lancement, sous réserve
des revues de sécurité et essais sur appareil encore requis. Leur formulation
publique reste bornée par la décision.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

SITE = Path(__file__).resolve().parent
STUDIO = SITE.parent  # C:\BB16\10_STUDIO

CA_FR = STUDIO / "ConvertAir" / "docs" / "poc" / "screenshots-gate6" / "fr"
DC_FR = STUDIO / "DocCipher" / "docs" / "store" / "screenshots" / "fr"
HGQ_DEV = STUDIO / "HGQ" / "hgq" / "app_preview"
HGQ_STORE = STUDIO / "HGQ" / "hgq" / "docs" / "store" / "screenshots" / "2026-09-19-android-preview"

# Largeur des captures WebP publiées et des vidéos (pixels).
SCREEN_WIDTH = 540
VIDEO_WIDTH = 432

# Chaque app a un rapport d'écran unique (après recadrage des barres système).
APP_SCREEN = {
    "convertair": {"crop": (0, 0), "source_size": (786, 1606)},
    "doccipher": {"crop": (0, 0), "source_size": (1080, 1920)},
    # Barre d'état (heure, notifications) et barre de gestes retirées.
    "hgq": {"crop": (84, 60), "source_size": (1080, 2400)},
}


def _hgq(name: str) -> Path:
    return HGQ_DEV / f"Screenshot_2025-11-22-{name}_com.example.realtime_quizzes.jpg"


# Clé publiée -> (application, fichier source dans le dépôt de l'app).
SCREENS: dict[str, tuple[str, Path]] = {
    "assets/screens/convertair/accueil.webp": ("convertair", CA_FR / "accueil.png"),
    "assets/screens/convertair/catalogue.webp": ("convertair", CA_FR / "catalogue.png"),
    "assets/screens/convertair/catalogue-ocr.webp": ("convertair", CA_FR / "catalogue-ocr.png"),
    "assets/screens/convertair/fusion.webp": ("convertair", CA_FR / "fusion.png"),
    "assets/screens/convertair/fichiers.webp": ("convertair", CA_FR / "fichiers.png"),
    "assets/screens/convertair/reglages.webp": ("convertair", CA_FR / "reglages.png"),
    "assets/screens/convertair/paywall.webp": ("convertair", CA_FR / "paywall.png"),
    "assets/screens/doccipher/coffre.webp": ("doccipher", DC_FR / "01-journeys-home.png"),
    "assets/screens/doccipher/parcours.webp": ("doccipher", DC_FR / "02-journeys.png"),
    "assets/screens/doccipher/recherche.webp": ("doccipher", DC_FR / "03-search.png"),
    "assets/screens/doccipher/premium.webp": ("doccipher", DC_FR / "04-paywall.png"),
    "assets/screens/doccipher/echeances.webp": ("doccipher", DC_FR / "05-expiry-radar.png"),
    "assets/screens/doccipher/import.webp": ("doccipher", DC_FR / "06-import-summary.png"),
    "assets/screens/doccipher/confiance.webp": ("doccipher", DC_FR / "07-trust.png"),
    "assets/screens/doccipher/ajout.webp": ("doccipher", DC_FR / "08-photo.png"),
    # Captures sans adresse email ni donnée de compte visible.
    "assets/screens/hgq/creer.webp": ("hgq", _hgq("21-28-33-109")),
    "assets/screens/hgq/salon.webp": ("hgq", _hgq("21-45-38-403")),
    "assets/screens/hgq/resultat.webp": ("hgq", _hgq("22-06-05-486")),
    "assets/screens/hgq/duel.webp": ("hgq", _hgq("22-08-11-253")),
    "assets/screens/hgq/connexion.webp": ("hgq", HGQ_STORE / "hgq_01_login.png"),
    "assets/screens/hgq/inscription.webp": ("hgq", HGQ_STORE / "hgq_02_signup.png"),
}

# Vidéo publiée -> segments (capture, mouvement). « scroll » : zoom marqué et
# défilement vertical, comme un pouce qui parcourt l'écran ; « drift » : zoom
# léger et glissement lent. Les segments s'enchaînent en fondu.
VIDEOS: dict[str, list[tuple[str, str]]] = {
    "assets/video/convertair/scan.mp4": [("assets/screens/convertair/accueil.webp", "scroll")],
    "assets/video/convertair/outils.mp4": [("assets/screens/convertair/catalogue.webp", "scroll"), ("assets/screens/convertair/catalogue-ocr.webp", "drift")],
    "assets/video/convertair/fusion.mp4": [("assets/screens/convertair/fusion.webp", "drift")],
    "assets/video/convertair/fichiers.mp4": [("assets/screens/convertair/fichiers.webp", "drift")],
    "assets/video/convertair/ocr.mp4": [("assets/screens/convertair/catalogue-ocr.webp", "scroll")],
    "assets/video/convertair/reglages.mp4": [("assets/screens/convertair/reglages.webp", "scroll")],
    "assets/video/convertair/premium.mp4": [("assets/screens/convertair/paywall.webp", "scroll")],
    "assets/video/doccipher/coffre.mp4": [("assets/screens/doccipher/coffre.webp", "scroll")],
    "assets/video/doccipher/parcours.mp4": [("assets/screens/doccipher/parcours.webp", "scroll")],
    "assets/video/doccipher/echeances.mp4": [("assets/screens/doccipher/coffre.webp", "drift"), ("assets/screens/doccipher/echeances.webp", "scroll")],
    "assets/video/doccipher/ajout.mp4": [("assets/screens/doccipher/ajout.webp", "scroll")],
    "assets/video/doccipher/recherche.mp4": [("assets/screens/doccipher/recherche.webp", "drift")],
    "assets/video/doccipher/import.mp4": [("assets/screens/doccipher/import.webp", "scroll")],
    "assets/video/doccipher/confiance.mp4": [("assets/screens/doccipher/confiance.webp", "scroll")],
    "assets/video/doccipher/premium.mp4": [("assets/screens/doccipher/premium.webp", "scroll")],
    "assets/video/hgq/creer.mp4": [("assets/screens/hgq/creer.webp", "scroll")],
    "assets/video/hgq/duel.mp4": [("assets/screens/hgq/duel.webp", "drift")],
    "assets/video/hgq/resultat.mp4": [("assets/screens/hgq/resultat.webp", "drift")],
    "assets/video/hgq/salon.mp4": [("assets/screens/hgq/salon.webp", "drift")],
    "assets/video/hgq/compte.mp4": [("assets/screens/hgq/connexion.webp", "drift"), ("assets/screens/hgq/inscription.webp", "drift")],
}

# Icônes légères dérivées des icônes déjà publiées (assets/apps/*.png).
ICONS: dict[str, tuple[str, tuple[int, int]]] = {
    "assets/branding/bb16-studio-logo-light-256.webp": ("assets/branding/bb16-studio-logo.jpg", (256, 256)),
    "assets/branding/bb16-studio-logo-dark-256.webp": ("assets/branding/bb16-studio-logo-dark.png", (256, 256)),
    "assets/apps/convertair-icon-192.webp": ("assets/apps/convertair-icon-512.png", (192, 192)),
    "assets/apps/doccipher-icon-192.webp": ("assets/apps/doccipher-icon-512.png", (192, 192)),
    "assets/apps/hgq-logo-192.webp": ("assets/apps/hgq-logo.png", (192, 212)),
}

MEDIA_FILES = sorted(SCREENS) + sorted(VIDEOS) + sorted(ICONS)


def screen_size(app: str, width: int) -> tuple[int, int]:
    """Taille publiée (paire) d'une capture recadrée de l'app, à une largeur donnée."""
    spec = APP_SCREEN[app]
    source_w, source_h = spec["source_size"]
    top, bottom = spec["crop"]
    height = (source_h - top - bottom) * width / source_w
    return width, int(round(height / 2) * 2)


# ---------------------------------------------------------------------------
# Contenu. Chaque phrase décrit une capture réelle ou une page de
# confidentialité déjà publiée ; les prix sont ceux décidés par le propriétaire.
# ---------------------------------------------------------------------------

PRODUCTS: dict[str, dict] = {
    "convertair": {
        "name": "ConvertAir",
        "headline": ("Tous vos documents.", "Un seul outil."),
        "icon": "assets/apps/convertair-icon-192.webp",
        "icon_size": (192, 192),
        "eyebrow": "Documents · Android",
        "lede": "Scanner, convertir, assembler, signer et reconnaître le texte de vos documents, directement sur votre téléphone.",
        "status": "Bientôt sur Android",
        "points": ["Traitement sur l'appareil", "Aucun compte à créer", "3 opérations gratuites par jour"],
        "hero": ("assets/screens/convertair/accueil.webp", "Écran d'accueil de ConvertAir : scanner un document, recettes de workflow et conversions"),
        "tour_title": "Tout le document, dans la main.",
        "tour": [
            ("scan", "Scanner un document", "Cadrez : les bords sont détectés en temps réel. Depuis l'accueil, les conversions courantes sont à un geste — images vers PDF, PDF vers images, texte vers PDF — et les recettes de workflow enchaînent plusieurs étapes sur l'appareil.", "assets/screens/convertair/accueil.webp", "assets/video/convertair/scan.mp4", "Accueil de ConvertAir avec le scanner et les conversions"),
            ("outils", "Tous les outils PDF, au même endroit", "Fusionner, diviser, compresser, pivoter, recadrer, numéroter, filigraner, protéger, déverrouiller, réparer. Pour remplir un formulaire : signature, zone de texte, date rapide et coches. Le catalogue se parcourt ou se recherche.", "assets/screens/convertair/catalogue.webp", "assets/video/convertair/outils.mp4", "Catalogue des outils PDF de ConvertAir"),
            ("fusion", "Fusionner dans le bon ordre", "Glissez pour réordonner : l'ordre de la liste est l'ordre de fusion. Chaque fichier est vérifié avant l'assemblage.", "assets/screens/convertair/fusion.webp", "assets/video/convertair/fusion.mp4", "Écran Fusionner avec deux PDF vérifiés"),
            ("fichiers", "Retrouver chaque fichier", "L'historique local garde vos derniers documents, avec recherche et favoris. Il peut se purger seul après 30 ou 90 jours, selon votre réglage.", "assets/screens/convertair/fichiers.webp", "assets/video/convertair/fichiers.mp4", "Écran Fichiers avec l'historique local"),
        ],
        "grid_title": "Et dans le détail.",
        "grid": [
            ("Le texte, reconnu sur place", "PDF cherchable et extraction du texte, avec des modèles embarqués : aucune image n'est envoyée à un serveur pour la reconnaissance.", "assets/screens/convertair/catalogue-ocr.webp", "assets/video/convertair/ocr.mp4", "Outils de reconnaissance de texte de ConvertAir"),
            ("Des réglages qui disent tout", "Thème, langue, nettoyage de l'historique, et une explication claire : vos documents sont traités sur l'appareil, le réseau ne sert qu'aux achats.", "assets/screens/convertair/reglages.webp", "assets/video/convertair/reglages.mp4", "Réglages de ConvertAir : apparence, langue, confidentialité"),
            ("Premium, quand il le faut", "Opérations illimitées, export sans filigrane, traitement par lot. Mensuel, annuel ou à vie.", "assets/screens/convertair/paywall.webp", "assets/video/convertair/premium.mp4", "Offre Premium de ConvertAir"),
        ],
        "also": None,
        "soon": None,
        "pricing_intro": "Premium débloque les opérations illimitées, l'export sans filigrane et le traitement par lot.",
        "plans": [
            ("Gratuit", "0 €", "", ["3 opérations par jour", "Traitement sur l'appareil", "Sans compte"], False),
            ("Mensuel", "9,99 €", "par mois", ["Premium complet", "Résiliable à tout moment dans Google Play"], False),
            ("Annuel", "49,99 €", "par an", ["Premium complet", "Soit environ 4,17 € par mois"], True),
            ("À vie", "119,99 €", "au lancement, puis 159,99 €", ["Premium complet", "Paiement unique"], False),
        ],
        "privacy": [
            ("Vos documents restent sur le téléphone", "Numérisation, conversions, signature et reconnaissance de texte s'exécutent sur l'appareil. BB16 Studio ne reçoit aucune copie."),
            ("Des services Store bornés", "Google Play encaisse le paiement, RevenueCat vérifie l'accès Premium. Après un résultat réussi affiché, l'API officielle Google Play peut proposer un avis. Aucun contenu de document ne passe par ces chemins."),
            ("Ni publicité, ni mesure d'audience", "Aucun compte, aucun identifiant publicitaire, aucun SDK d'analytics intégré à l'application."),
        ],
        "privacy_link": ("convertair-privacy.html", "Lire la politique de confidentialité de ConvertAir"),
        "faq": [
            ("Mes documents sont-ils envoyés sur un serveur ?", "Non. Les traitements s'exécutent sur votre téléphone. Un fichier ne quitte ConvertAir que si vous le partagez, l'enregistrez ailleurs ou l'imprimez."),
            ("Que permet la version gratuite ?", "Trois opérations par jour, traitées sur l'appareil et sans compte. Premium lève la limite, retire le filigrane des exports et ajoute le traitement par lot."),
            ("Comment résilier un abonnement ?", "Dans Google Play, à tout moment. L'accès Premium reste actif jusqu'à la fin de la période payée. L'offre à vie est un paiement unique, sans renouvellement."),
            ("Faut-il une connexion Internet ?", "Pas pour traiter vos documents. La connexion sert aux achats et à la vérification de l'accès Premium."),
            ("Quand ConvertAir sera-t-il disponible ?", "La V1 Android est en préparation. Le lien Google Play apparaîtra sur cette page dès la publication. Une version iOS est à l'étude."),
        ],
        "captures_note": "Captures de l'application en français, prises sur une version de préparation.",
    },
    "doccipher": {
        "name": "DocCipher",
        "headline": ("Vos papiers.", "Votre tranquillité."),
        "icon": "assets/apps/doccipher-icon-192.webp",
        "icon_size": (192, 192),
        "eyebrow": "Coffre documentaire · Android",
        "lede": "Vos papiers importants, chiffrés sur votre téléphone. Sans compte, sans serveur documentaire, avec une sauvegarde que vous choisissez.",
        "status": "Bientôt sur Android",
        "points": ["Coffre chiffré sur l'appareil", "Gratuit jusqu'à 15 documents", "Premium : 19,99 € une seule fois"],
        "hero": ("assets/screens/doccipher/coffre.webp", "Coffre DocCipher « Papiers de famille » : dix documents, parcours et échéances"),
        "tour_title": "Vos papiers, rangés et protégés.",
        "tour": [
            ("coffre", "Votre coffre, d'un coup d'œil", "Nombre de documents, taille, santé du coffre et prochaine étape conseillée. Affichage en grille, en liste, par catégorie ou par échéance.", "assets/screens/doccipher/coffre.webp", "assets/video/doccipher/coffre.mp4", "Accueil du coffre DocCipher"),
            ("parcours", "Des parcours pour ne rien oublier", "Garanties et achats, papiers essentiels, voyage : des suggestions selon votre situation pour rassembler vos papiers. Un compteur, pas une vérification : DocCipher ne juge pas ce que vous ajoutez.", "assets/screens/doccipher/parcours.webp", "assets/video/doccipher/parcours.mp4", "Parcours DocCipher : garanties et papiers essentiels"),
            ("echeances", "Les échéances avant qu'elles tombent", "Les documents qui expirent sous 30 jours remontent en tête ; les suivants sont rangés par date.", "assets/screens/doccipher/echeances.webp", "assets/video/doccipher/echeances.mp4", "Vue Échéances de DocCipher"),
            ("ajout", "Photographier, vérifier, chiffrer", "Titre, catégorie, date d'achat et durée de garantie : DocCipher propose la fin de garantie, chiffre la photo dans votre coffre et efface sa copie temporaire.", "assets/screens/doccipher/ajout.webp", "assets/video/doccipher/ajout.mp4", "Ajout d'un document photographié dans DocCipher"),
        ],
        "grid_title": "Et dans le détail.",
        "grid": [
            ("Chercher et filtrer", "Par mot, par catégorie, par émetteur : le bon papier en quelques lettres.", "assets/screens/doccipher/recherche.webp", "assets/video/doccipher/recherche.mp4", "Recherche filtrée dans DocCipher"),
            ("Importer par lots", "Un bilan clair après l'import : ce qui est ajouté, ce qui se trouvait déjà dans le coffre.", "assets/screens/doccipher/import.webp", "assets/video/doccipher/import.mp4", "Bilan d'import de plusieurs fichiers"),
            ("Ce que DocCipher envoie", "Un écran dit exactement ce qui sort : aucun document, titre, catégorie ni nombre de documents n'accompagne un achat.", "assets/screens/doccipher/confiance.webp", "assets/video/doccipher/confiance.mp4", "Écran « Ce que DocCipher envoie »"),
            ("Premium en un seul paiement", "19,99 €, pas d'abonnement : la limite de 15 documents disparaît et vous pouvez ajouter des documents dans plusieurs coffres.", "assets/screens/doccipher/premium.webp", "assets/video/doccipher/premium.mp4", "Offre DocCipher Premium à 19,99 €"),
        ],
        "also": ["Déverrouillage biométrique par l'invite d'Android ; le code PIN reste nécessaire.", "Sauvegarde .dcvault chiffrée, exportée là où vous le décidez.", "Kit de récupération à imprimer ou enregistrer en PDF.", "Reconnaissance de texte sur l'appareil."],
        "soon": True,
        "pricing_intro": "Un seul achat, pour toujours. Pas d'abonnement.",
        "plans": [
            ("Gratuit", "0 €", "", ["Jusqu'à 15 documents", "Coffre chiffré sur l'appareil", "Sans compte"], False),
            ("Premium", "19,99 €", "paiement unique", ["Plus de limite de 15 documents", "Des documents dans plusieurs coffres", "Code de panique et coffre leurre prévus dès le lancement", "Droit Premium à vie, sans supplément pour ces protections"], True),
        ],
        "privacy": [
            ("Chiffré sur l'appareil", "Documents, aperçus, texte reconnu et données du coffre restent dans l'espace privé de l'application, chiffrés."),
            ("Ni compte, ni serveur documentaire", "BB16 Studio n'héberge, ne synchronise et ne sauvegarde aucun document. Vos documents ne sortent que par un export que vous déclenchez."),
            ("Aucun document dans les services tiers", "Google Play encaisse, RevenueCat vérifie l'accès Premium et l'API officielle Google Play peut proposer un avis après une réussite. Aucun document, coffre, mot de passe, PIN ni clé ne passe par ces chemins."),
        ],
        "privacy_link": ("doccipher-privacy.html", "Lire la politique de confidentialité de DocCipher"),
        "faq": [
            ("Et si j'oublie mon mot de passe ?", "Votre mot de passe maître n'est ni enregistré ni envoyé : personne, pas même BB16 Studio, ne peut le réinitialiser. Le kit de récupération (phrase et code QR), à imprimer ou enregistrer, sert à cela."),
            ("Mes documents sont-ils sauvegardés en ligne ?", "Non. Vous exportez vous-même une sauvegarde .dcvault chiffrée vers l'emplacement de votre choix. La synchronisation WebDAV ou Nextcloud n'est pas disponible dans cette version."),
            ("Premium est-il un abonnement ?", "Non : 19,99 € une seule fois. Sans achat, DocCipher reste utilisable jusqu'à 15 documents."),
            ("Le code de panique et le coffre leurre seront-ils présents au lancement ?", "Ils sont prévus dès le lancement et inclus dans le droit Premium à vie, sans supplément. Leur implémentation locale reste en validation : ils ne seront rendus disponibles que si les revues de sécurité et les essais sur appareil requis sont concluants."),
            ("Quand DocCipher sera-t-il disponible ?", "DocCipher arrive bientôt sur Android. Il n'est pas encore disponible sur Google Play ; le lien apparaîtra sur cette page après sa publication."),
        ],
        "captures_note": "Captures de l'application en français, avec un coffre d'exemple.",
    },
    "hgq": {
        "name": "HGQ",
        "headline": ("La culture gaming.", "Le plaisir de jouer."),
        "icon": "assets/apps/hgq-logo-192.webp",
        "icon_size": (192, 212),
        "eyebrow": "Quiz multijoueur · Android",
        "lede": "Hard Gamer Quiz : des duels en temps réel sur la culture jeu vidéo. Créez une partie, affrontez un joueur, comparez vos scores.",
        "status": "Bientôt sur Android",
        "points": ["Duels en temps réel", "Mode solo", "Amis, profils et classements"],
        "hero": ("assets/screens/hgq/connexion.webp", "Écran d'accueil de Hard Gamer Quiz : se connecter ou s'inscrire"),
        "tour_title": "Une question. Deux joueurs. Un gagnant.",
        "tour": [
            ("creer", "Créer une partie à votre mesure", "Catégorie, nombre de questions, difficulté, mode multijoueur ou solo : la partie se règle en quelques touches.", "assets/screens/hgq/creer.webp", "assets/video/hgq/creer.mp4", "Création d'une partie HGQ : catégorie, questions, difficulté, mode"),
            ("duel", "Répondre plus vite que l'adversaire", "Les deux joueurs voient la même question au même moment. Le chrono tourne, les réponses s'affichent en direct.", "assets/screens/hgq/duel.webp", "assets/video/hgq/duel.mp4", "Question en duel dans HGQ"),
            ("resultat", "Le verdict", "Score final face à face. Les parties classées sont validées côté serveur.", "assets/screens/hgq/resultat.webp", "assets/video/hgq/resultat.mp4", "Résultat final d'un duel HGQ"),
        ],
        "grid_title": "Et autour de la partie.",
        "grid": [
            ("La salle d'attente", "Votre partie attend un adversaire et démarre dès qu'un joueur la rejoint.", "assets/screens/hgq/salon.webp", "assets/video/hgq/salon.mp4", "Salle d'attente d'une partie HGQ"),
            ("Un compte pour progresser", "Connexion par email ou avec Google, pseudo et avatar : vos statistiques et vos amis vous suivent.", "assets/screens/hgq/connexion.webp", "assets/video/hgq/compte.mp4", "Connexion et création de compte HGQ"),
        ],
        "also": ["Amis et recherche de joueurs.", "Profil, historique des parties et statistiques.", "Classements.", "Suppression du compte depuis les paramètres de l'application."],
        "soon": None,
        "pricing_intro": "Une formule Premium est prévue. Son contenu sera détaillé à la sortie.",
        "plans": [
            ("Premium mensuel", "3,99 €", "par mois", ["Résiliable à tout moment dans Google Play"], False),
            ("Premium annuel", "24,99 €", "par an", ["Soit environ 2,08 € par mois"], True),
        ],
        "privacy": [
            ("Un compte, et c'est tout", "HGQ utilise un compte (email ou Google), vos statistiques de jeu et vos amis pour faire fonctionner les parties en ligne."),
            ("Suppression dans l'application", "Paramètres, puis Mon compte, puis Supprimer mon compte. Sans accès, écrivez au support."),
            ("Une politique dédiée", "La politique de confidentialité de l'application détaille ses données et ses services tiers."),
        ],
        "privacy_link": ("data-deletion.html", "Supprimer un compte HGQ"),
        "faq": [
            ("Quand HGQ sera-t-il disponible ?", "Bientôt sur Android. Le lien Google Play apparaîtra sur cette page dès la publication."),
            ("Faut-il un compte ?", "Oui : il porte vos statistiques, vos amis et vos classements. La connexion se fait par email ou avec Google."),
            ("Que contiendra Premium ?", "Les prix sont fixés — 3,99 € par mois ou 24,99 € par an — mais le contenu de Premium sera annoncé avec la sortie. Rien n'est promis avant."),
            ("Comment supprimer mon compte ?", "Depuis l'application : Paramètres, Mon compte, Supprimer mon compte. La page Suppression de compte explique la marche à suivre si vous n'avez plus accès."),
        ],
        "captures_note": "Captures de versions de développement : l'interface, encore partiellement en anglais, évolue d'ici la sortie.",
    },
}

HGQ_PRIVACY_URL = "https://hgq-prod.web.app/privacy"


def play_url(package: str) -> str:
    return f"https://play.google.com/store/apps/details?id={package}"


def store_listing(config: dict, key: str) -> dict:
    listing = (config.get("store_listings") or {}).get(key) or {}
    if not listing.get("package"):
        raise ValueError(f"store_listings.{key}.package manquant dans site.config.json")
    return {"package": listing["package"], "published": listing.get("published") is True}


def screen_img(app: str, src: str, alt: str, eager: bool = False) -> str:
    w, h = screen_size(app, SCREEN_WIDTH)
    loading = 'fetchpriority="high"' if eager else 'loading="lazy"'
    alt_attr = escape(alt, quote=True)
    return f'<img src="{src}" alt="{alt_attr}" width="{w}" height="{h}" {loading} decoding="async">'


def video_tag(video: str) -> str:
    # Pas de src : product.js la pose au besoin (chargement différé), jamais
    # quand l'utilisateur demande moins d'animations.
    return f'<video data-src="{video}" muted loop playsinline preload="none" aria-hidden="true" tabindex="-1"></video>'


def phone_frame(inner: str, extra_class: str = "") -> str:
    """Unique coque générique ; sa géométrie appartient uniquement au CSS partagé.

    Les dimensions intrinsèques des médias restent celles des captures réelles.
    Elles ne déterminent jamais la taille ni la forme du téléphone.
    """
    cls = f"phone {extra_class}".strip()
    return f'<div class="{cls}" data-phone><div class="screen">{inner}</div></div>'


def phone(app: str, src: str, alt: str, video: str | None = None, eager: bool = False, extra_class: str = "") -> str:
    inner = screen_img(app, src, alt, eager) + (video_tag(video) if video else "")
    return phone_frame(inner, extra_class)


def store_button(key: str, config: dict, verb: str = "rate") -> str:
    product = PRODUCTS[key]
    listing = store_listing(config, key)
    if listing["published"]:
        label = f"Noter {product['name']} sur Google Play" if verb == "rate" else f"Télécharger {product['name']} sur Google Play"
        return f'<a class="button store-button" href="{play_url(listing["package"])}" rel="noopener">{label}</a>'
    return '<span class="store-pending">Bientôt sur Google Play</span>'


def icon_tag(key: str, extra: str = "", lazy: bool = True) -> str:
    product = PRODUCTS[key]
    cls = "app-icon hgq-icon" if key == "hgq" else "app-icon"
    if extra:
        cls += " " + extra
    w, h = product["icon_size"]
    loading = ' loading="lazy"' if lazy else ""
    return f'<img class="{cls}" src="{product["icon"]}" alt="" width="{w}" height="{h}"{loading}>'


def rating_section(key: str, config: dict) -> str:
    product = PRODUCTS[key]
    listing = store_listing(config, key)
    if listing["published"]:
        text = f"Vous utilisez {product['name']} ? Une note et quelques mots sur Google Play aident d'autres personnes à trouver l'application et nous disent quoi améliorer."
    else:
        text = f"{product['name']} n'est pas encore sur Google Play. Le lien pour noter l'application apparaîtra ici dès sa publication."
    icon = icon_tag(key)
    return f'''<section class="section alt" id="noter"><div class="container"><div class="rate-card">
  {icon}
  <div class="rate-copy"><p class="eyebrow">Notez-nous sur le Store</p><h2>Votre avis compte.</h2><p>{text}</p><p class="meta">Un avis honnête, rien en échange : pas de parrainage, pas de récompense.</p></div>
  <div class="rate-action">{store_button(key, config)}</div>
</div></div></section>'''


def home_rating_section(config: dict) -> str:
    rows = []
    for key, product in PRODUCTS.items():
        name = product["name"]
        rows.append(f'<li class="rate-row">{icon_tag(key)}<a class="rate-name" href="{key}.html">{name}</a>{store_button(key, config)}</li>')
    return f'''<section class="section" id="noter"><div class="container"><div class="section-head"><div><p class="eyebrow">Notez-nous sur le Store</p><h2>Votre avis nous fait avancer.</h2></div><p>Une note sur Google Play aide d'autres personnes à trouver nos applications. Un avis honnête, rien en échange : pas de parrainage, pas de récompense. Chaque lien apparaît dès que l'application est publiée.</p></div><ul class="rate-list">{"".join(rows)}</ul></div></section>'''


def soon_block() -> str:
    return '''<section class="section" id="bientot"><div class="container"><div class="soon">
  <p class="soon-badge">Prévu dès le lancement · inclus dans Premium</p>
  <h2>Deux protections prévues dès le lancement.</h2>
  <p class="soon-intro">Leur implémentation locale est en validation. Elles seront proposées au lancement seulement si les revues de sécurité et les essais sur appareil requis sont concluants. DocCipher n'est pas encore disponible sur Google Play.</p>
  <div class="soon-grid">
    <article class="soon-item"><h3>Code de panique</h3><p>Une option Premium que vous activez volontairement avec votre mot de passe maître, un code PIN distinct saisi deux fois, deux consentements et une confirmation de l'action irréversible. Vous choisissez certains coffres ou tous les coffres.</p><p>Le PIN armé déclenche un effacement logique des fichiers, clés locales, caches et miniatures des coffres choisis : « Effacer les coffres présents sur cet appareil. Vos sauvegardes externes ne sont pas supprimées. » Seule la saisie exacte du PIN de panique armé déclenche cette action. L'opération ne promet pas un effacement physique du stockage du téléphone.</p></article>
    <article class="soon-item"><h3>Coffre leurre</h3><p>Un coffre local séparé, avec son propre PIN, ses propres clés et son propre contenu, à ouvrir si quelqu'un regarde par-dessus votre épaule ou vous demande d'ouvrir l'application.</p><p>La fonction est documentée publiquement : elle protège d'un regard occasionnel, elle ne garantit pas qu'un observateur ignore son existence ni qu'une analyse de l'appareil ne la distingue.</p></article>
  </div>
  <p class="meta">Le droit Premium à vie inclut ces deux fonctions sans supplément.</p>
</div></div></section>'''


def product_body(key: str, config: dict) -> str:
    p = PRODUCTS[key]
    listing = store_listing(config, key)
    hero_cta = store_button(key, config, verb="get") if listing["published"] else ""
    points = "".join(f"<li>{escape(x)}</li>" for x in p["points"])
    hero_src, hero_alt = p["hero"]
    hero_icon = icon_tag(key, "hero-icon", lazy=False)
    eyebrow, name, lede = escape(p["eyebrow"]), escape(p["name"]), escape(p["lede"])
    headline = "".join(f"<span>{escape(line)}</span>" for line in p["headline"])
    status, tour_title, grid_title = escape(p["status"]), escape(p["tour_title"]), escape(p["grid_title"])
    captures_note, pricing_intro = escape(p["captures_note"]), escape(p["pricing_intro"])
    soon = soon_block() if p["soon"] else ""
    secondary = " secondary" if hero_cta else ""

    steps = []
    layers = []
    total = len(p["tour"])
    for i, (sid, title, text, src, video, alt) in enumerate(p["tour"], start=1):
        steps.append(f'''<li class="tour-step" data-step id="etape-{sid}"><div class="step-copy"><p class="step-index">{i:02d} <span>/ {total:02d}</span></p><h3>{escape(title)}</h3><p>{escape(text)}</p></div><div class="step-device">{phone(key, src, alt, video, extra_class="step-phone")}</div></li>''')
        active = " is-active" if i == 1 else ""
        layers.append(f'<div class="layer{active}" data-layer>{screen_img(key, src, "")}{video_tag(video)}</div>')

    cards = []
    for title, text, src, video, alt in p["grid"]:
        cards.append(f'''<article class="feature-card" data-hover-video><div class="feature-copy"><h3>{escape(title)}</h3><p>{escape(text)}</p></div><div class="feature-device">{phone(key, src, alt, video)}</div><button class="preview-toggle" type="button" data-preview-toggle aria-pressed="false" hidden><span data-preview-label>Voir l'aperçu animé</span><span class="sr-only"> : {escape(title)}</span></button></article>''')
    also = ""
    if p["also"]:
        also = '<ul class="also-list">' + "".join(f"<li>{escape(x)}</li>" for x in p["also"]) + "</ul>"

    plans = []
    for plan_name, price, unit, features, featured in p["plans"]:
        feats = "".join(f"<li>{escape(f)}</li>" for f in features)
        unit_html = f'<span class="plan-unit">{escape(unit)}</span>' if unit else ""
        featured_cls = " featured" if featured else ""
        plans.append(f'<article class="plan{featured_cls}"><h3>{escape(plan_name)}</h3><p class="plan-price">{escape(price)}{unit_html}</p><ul>{feats}</ul></article>')

    privacy = "".join(f'<article class="card"><h3>{escape(t)}</h3><p>{escape(d)}</p></article>' for t, d in p["privacy"])
    link_href, link_label = p["privacy_link"]
    privacy_actions = f'<a class="button secondary" href="{link_href}">{escape(link_label)}</a>'
    if key == "hgq":
        privacy_actions = f'<a class="button secondary" href="{HGQ_PRIVACY_URL}" rel="noopener">Politique de confidentialité HGQ</a>' + privacy_actions

    faq = "".join(f'<details class="faq-item"><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q, a in p["faq"])

    return f'''<nav class="product-nav" aria-label="Dans cette page"><div class="container product-nav-inner"><a class="product-nav-name" href="#presentation">{name}</a><div class="product-nav-links"><a href="#fonctions">Fonctions</a><a href="#apercus">Aperçus</a><a href="#prix">Prix</a><a href="#confidentialite">Confidentialité</a><a href="#faq">FAQ</a></div></div></nav>
<section class="product-hero" id="presentation"><div class="container product-hero-grid">
  <div class="product-hero-copy">
    <div class="product-identity">{hero_icon}<div><p class="product-name">{name}</p><p class="eyebrow">{eyebrow}</p></div></div>
    <h1>{headline}</h1>
    <p class="lede">{lede}</p>
    <ul class="hero-points">{points}</ul>
    <div class="actions">{hero_cta}<a class="button{secondary}" href="#fonctions">Voir les fonctions</a><a class="button secondary" href="#prix">Prix</a></div>
    <p class="hero-status"><span class="status pending">{status}</span></p>
  </div>
  <figure class="hero-device">{phone(key, hero_src, hero_alt, eager=True)}<figcaption>Capture réelle de {name}</figcaption></figure>
</div></section>
<section class="section tour-section" id="fonctions"><div class="container">
  <div class="section-head"><div><p class="eyebrow">01 · Visite guidée</p><h2>{tour_title}</h2></div><div class="section-intro"><p>Découvrez chaque fonction au fil de la page. {captures_note}</p><button class="motion-toggle" type="button" data-motion-toggle aria-pressed="false" hidden>Mettre les aperçus en pause</button></div></div>
  <div class="tour" data-tour>
    <ol class="tour-steps">{"".join(steps)}</ol>
    <div class="tour-stage" aria-hidden="true"><div class="tour-sticky">{phone_frame("".join(layers))}<p class="tour-counter"><span data-counter>01</span> <span>/ {total:02d}</span></p></div></div>
  </div>
</div></section>
<section class="section alt" id="apercus"><div class="container">
  <div class="section-head"><div><p class="eyebrow">02 · En mouvement</p><h2>{grid_title}</h2></div><div class="section-intro"><p class="hover-hint">Survolez une carte ou lancez son aperçu animé.</p><p class="touch-hint">Les aperçus s'animent lorsqu'ils apparaissent à l'écran. Vous pouvez les mettre en pause.</p><p class="motion-hint">Animations désactivées : explorez les captures à votre rythme.</p></div></div>
  <div class="feature-grid">{"".join(cards)}</div>{also}
</div></section>
{soon}
<section class="section" id="prix"><div class="container">
  <div class="section-head"><div><p class="eyebrow">03 · Prix</p><h2>Simple et affiché.</h2></div><p>{pricing_intro}</p></div>
  <div class="plan-grid">{"".join(plans)}</div>
  <p class="meta plan-note">Prix de référence en France. Le prix affiché par Google Play au moment de l'achat fait foi.</p>
</div></section>
<section class="section alt" id="confidentialite"><div class="container">
  <div class="section-head"><div><p class="eyebrow">04 · Confidentialité</p><h2>Ce qui reste chez vous.</h2></div></div>
  <div class="grid">{privacy}</div>
  <div class="actions">{privacy_actions}</div>
</div></section>
<section class="section" id="faq"><div class="container faq">
  <p class="eyebrow">05 · Questions fréquentes</p><h2>Tout ce qu'il faut savoir.</h2>
  {faq}
  <p class="meta">Une autre question ? <a href="contact.html">Écrivez-nous</a>.</p>
</div></section>
{rating_section(key, config)}'''
