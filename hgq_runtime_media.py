"""Curated Android gameplay clips and localized HGQ video presentation."""

import json
from hashlib import sha256
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "content/hgq-runtime-media.json").read_text(encoding="utf-8"))
CLIPS = MANIFEST["clips"]
FILES = {clip[kind]: clip[kind + "_sha256"] for clip in CLIPS for kind in ("video", "poster")}
ARTWORK = MANIFEST.get("joker_artwork", {})
FILES.update({item["image"]: item["sha256"] for item in ARTWORK.values()})
VIDEO_MAX = 2_500_000
PAGE_VIDEOS_MAX = 6_000_000

COPY = {
    "fr": {
        "watch": "Voir l’extrait Fortnite", "try": "Tester une question",
        "heading": "Un autre univers. Le même défi.",
        "note": "Parties capturées sur Android, en français · version de test.",
        "trailer": ("Entre dans la partie.", "FIGHT, la dernière question, GAME OVER. Et ton score."),
        "answer": ("La bonne réponse.", "Le bon souvenir, les points qui tombent."),
        "fortnite": ("Fortnite, à toi de jouer.", "Une vraie question, une réponse et les points. Musique du jeu incluse."),
        "joker": ("Tous tes jokers, en un coup d’œil.", "Leurs effets et leur coût en Hegos, la monnaie du jeu."),
        "miss": ("Le chrono a le dernier mot.", "Une question, une hésitation, puis le verdict."),
    },
    "en": {
        "watch": "Watch the Fortnite clip", "try": "Try a question",
        "heading": "Another universe. The same challenge.",
        "note": "Android gameplay captured in French · test version.",
        "trailer": ("Step into the game.", "FIGHT, the last question, GAME OVER. Then your score."),
        "answer": ("The right answer.", "Recall the detail. Watch the points land."),
        "fortnite": ("Fortnite. Your turn.", "A real question, an answer and points, with music from the game."),
        "joker": ("Every joker at a glance.", "Their effects and prices in Hegos, the in-game currency."),
        "miss": ("The clock has the last word.", "One question, a moment of hesitation, then the verdict."),
    },
    "es": {
        "watch": "Ver el vídeo de Fortnite", "try": "Probar una pregunta",
        "heading": "Otro universo. El mismo desafío.",
        "note": "Partidas grabadas en Android, en francés · versión de prueba.",
        "trailer": ("Entra en la partida.", "FIGHT, la última pregunta, GAME OVER. Y tu puntuación."),
        "answer": ("La respuesta correcta.", "Recuerda el detalle y suma puntos."),
        "fortnite": ("Fortnite. Te toca jugar.", "Una pregunta real, una respuesta y puntos, con música del juego."),
        "joker": ("Todos tus comodines de un vistazo.", "Sus efectos y precios en Hegos, la moneda del juego."),
        "miss": ("El reloj tiene la última palabra.", "Una pregunta, una duda y el veredicto."),
    },
    "pt": {
        "watch": "Ver o vídeo de Fortnite", "try": "Experimentar uma pergunta",
        "heading": "Outro universo. O mesmo desafio.",
        "note": "Partidas captadas no Android, em francês · versão de teste.",
        "trailer": ("Entra na partida.", "FIGHT, a última pergunta, GAME OVER. E a tua pontuação."),
        "answer": ("A resposta certa.", "Lembra-te do detalhe e soma pontos."),
        "fortnite": ("Fortnite. É a tua vez.", "Uma pergunta real, uma resposta e pontos, com música do jogo."),
        "joker": ("Todos os teus jokers num relance.", "Os seus efeitos e preços em Hegos, a moeda do jogo."),
        "miss": ("O relógio tem a última palavra.", "Uma pergunta, uma hesitação e o veredito."),
    },
    "ja": {
        "watch": "Fortniteのプレイ動画を見る", "try": "クイズに挑戦",
        "heading": "別の世界でも、知識で勝負。",
        "note": "Androidテスト版の実際のプレイ映像です。表示言語はフランス語です。",
        "trailer": ("さあ、勝負の時間。", "FIGHTから最後の問題、GAME OVER、そしてスコアへ。"),
        "answer": ("正解の瞬間。", "ゲームの記憶を呼び起こしてポイント獲得。"),
        "fortnite": ("Fortniteで、いざ勝負。", "実際の問題、解答、ポイント獲得。ゲーム内の音楽とともに。"),
        "joker": ("すべてのジョーカーを一覧で。", "効果とゲーム内通貨Hegosでの価格を確認しよう。"),
        "miss": ("制限時間との勝負。", "ひとつの問題、ためらう一瞬、そして結果。"),
    },
    "ko": {
        "watch": "Fortnite 플레이 영상 보기", "try": "퀴즈에 도전",
        "heading": "다른 세계에서도 지식으로 승부하세요.",
        "note": "Android 테스트 버전의 실제 플레이 영상입니다. 프랑스어로 진행됩니다.",
        "trailer": ("대결을 시작하세요.", "FIGHT부터 마지막 문제, GAME OVER, 그리고 점수까지."),
        "answer": ("정답의 순간.", "게임 속 기억을 떠올리고 점수를 얻으세요."),
        "fortnite": ("Fortnite. 이제 내 차례.", "실제 문제와 답변, 점수 획득까지. 게임 음악과 함께 확인하세요."),
        "joker": ("모든 조커를 한눈에.", "효과와 게임 내 화폐 Hegos 가격을 확인하세요."),
        "miss": ("시간과의 승부.", "문제 하나, 망설이는 순간, 그리고 결과."),
    },
}

# The catalogue keeps its existing 22-language coverage. Product pages use six languages.
CATALOGUE = {
    "fr": ("Le quiz de ta culture jeu vidéo.", "FIGHT. Une question. GAME OVER. Jusqu’où iras-tu ?", "Découvrir HGQ", "Gameplay Android en français · version de test"),
    "en": ("Put your gaming knowledge to the test.", "FIGHT. One question. GAME OVER. How far will you go?", "Discover HGQ", "Android gameplay in French · test version"),
    "de": ("Teste dein Videospielwissen.", "FIGHT. Eine Frage. GAME OVER. Wie weit kommst du?", "HGQ entdecken", "Android-Gameplay auf Französisch · Testversion"),
    "es": ("Pon a prueba tu cultura de videojuegos.", "FIGHT. Una pregunta. GAME OVER. ¿Hasta dónde llegarás?", "Descubrir HGQ", "Partida en Android en francés · versión de prueba"),
    "it": ("Metti alla prova la tua cultura videoludica.", "FIGHT. Una domanda. GAME OVER. Fin dove arriverai?", "Scopri HGQ", "Gameplay Android in francese · versione di test"),
    "pt": ("Põe à prova a tua cultura de videojogos.", "FIGHT. Uma pergunta. GAME OVER. Até onde vais chegar?", "Descobrir HGQ", "Partida no Android em francês · versão de teste"),
    "pt-BR": ("Teste seus conhecimentos sobre videogames.", "FIGHT. Uma pergunta. GAME OVER. Até onde você vai?", "Conheça HGQ", "Partida no Android em francês · versão de teste"),
    "nl": ("Test je kennis van videogames.", "FIGHT. Eén vraag. GAME OVER. Hoe ver kom jij?", "Ontdek HGQ", "Android-gameplay in het Frans · testversie"),
    "pl": ("Sprawdź swoją wiedzę o grach.", "FIGHT. Jedno pytanie. GAME OVER. Jak daleko zajdziesz?", "Odkryj HGQ", "Rozgrywka na Androidzie po francusku · wersja testowa"),
    "ru": ("Проверь свои знания о видеоиграх.", "FIGHT. Один вопрос. GAME OVER. Как далеко ты зайдёшь?", "Открой HGQ", "Игра на Android на французском · тестовая версия"),
    "uk": ("Перевір свої знання про відеоігри.", "FIGHT. Одне запитання. GAME OVER. Як далеко ти зайдеш?", "Відкрий HGQ", "Гра на Android французькою · тестова версія"),
    "tr": ("Video oyunu bilgini sına.", "FIGHT. Bir soru. GAME OVER. Ne kadar ileri gideceksin?", "HGQ’yu keşfet", "Android oynanışı Fransızca · test sürümü"),
    "ar": ("اختبر معرفتك بألعاب الفيديو.", "FIGHT. سؤال واحد. GAME OVER. إلى أين ستصل؟", "اكتشف HGQ", "لعب على Android بالفرنسية · نسخة تجريبية"),
    "hi": ("वीडियो गेम की अपनी जानकारी परखें।", "FIGHT. एक सवाल। GAME OVER. आप कितनी दूर पहुँचेंगे?", "HGQ देखें", "Android पर फ़्रेंच में गेमप्ले · परीक्षण संस्करण"),
    "id": ("Uji pengetahuan video game kamu.", "FIGHT. Satu pertanyaan. GAME OVER. Sejauh mana kamu bisa?", "Kenali HGQ", "Gameplay Android dalam bahasa Prancis · versi uji coba"),
    "ja": ("ゲームの知識で勝負しよう。", "FIGHT、ひとつの問題、GAME OVER。どこまでいける？", "HGQを見る", "Android版のプレイ映像・フランス語・テスト版"),
    "ko": ("게임 지식으로 승부하세요.", "FIGHT. 문제 하나. GAME OVER. 어디까지 갈 수 있나요?", "HGQ 알아보기", "Android 플레이 영상 · 프랑스어 · 테스트 버전"),
    "th": ("ทดสอบความรู้เรื่องวิดีโอเกมของคุณ", "FIGHT. หนึ่งคำถาม GAME OVER. คุณจะไปได้ไกลแค่ไหน?", "รู้จัก HGQ", "เกมเพลย์ Android ภาษาฝรั่งเศส · เวอร์ชันทดสอบ"),
    "vi": ("Thử tài kiến thức trò chơi điện tử.", "FIGHT. Một câu hỏi. GAME OVER. Bạn sẽ tiến xa đến đâu?", "Khám phá HGQ", "Gameplay Android bằng tiếng Pháp · bản thử nghiệm"),
    "zh": ("用你的游戏知识来挑战。", "FIGHT。一道问题。GAME OVER。你能走多远？", "了解 HGQ", "Android 实机游戏画面 · 法语 · 测试版"),
    "zh-Hans": ("用你的游戏知识来挑战。", "FIGHT。一道问题。GAME OVER。你能走多远？", "了解 HGQ", "Android 实机游戏画面 · 法语 · 测试版"),
    "zh-Hant": ("用你的遊戲知識來挑戰。", "FIGHT。一道問題。GAME OVER。你能走多遠？", "認識 HGQ", "Android 實際遊戲畫面 · 法語 · 測試版"),
}


def player(clip_id, locale, *, base="", caption=True):
    clip = next(clip for clip in CLIPS if clip["id"] == clip_id)
    title, description = map(escape, COPY[locale][clip_id])
    content = (
        f'<video class="hgq-video" src="{base}{clip["video"]}" poster="{base}{clip["poster"]}" '
        f'controls playsinline preload="none" width="540" height="960" lang="fr" '
        f'data-hgq-runtime="{clip_id}" aria-label="{title}"></video>'
    )
    text = f'<figcaption><h3>{title}</h3><p>{description}</p></figcaption>' if caption else ""
    return f'<figure class="hgq-film" data-media-kind="RUNTIME_CAPTURE">{content}{text}</figure>'


def render(locale):
    copy = COPY[locale]
    clips = "".join(player(clip["id"], locale) for clip in CLIPS if clip["id"] != "trailer")
    return (
        '<section class="section hgq-moments" id="gameplay" aria-labelledby="hgq-moments-title">'
        '<div class="container"><div class="section-head">'
        f'<div><h2 id="hgq-moments-title">{escape(copy["heading"])}</h2>'
        f'<p class="section-note">{escape(copy["note"])}</p></div></div>'
        f'<div class="hgq-film-grid">{clips}{joker_image(locale)}</div></div></section>'
    )


def joker_image(locale):
    artwork = ARTWORK[locale]
    title, description = map(escape, COPY[locale]["joker"])
    return (
        '<figure class="hgq-joker-guide" data-media-kind="JOKER_GUIDE">'
        f'<a href="{artwork["image"]}" aria-label="{title}">'
        f'<img src="{artwork["image"]}" width="720" height="1470" '
        f'loading="lazy" decoding="async" alt="{escape(artwork["alt"], quote=True)}"></a>'
        f'<figcaption><h3>{title}</h3><p>{description}</p></figcaption></figure>'
    )


def render_catalogue(locale, base):
    heading, description, cta, note = map(escape, CATALOGUE[locale])
    target = (locale + "/" if locale in COPY and locale != "fr" else "") + "hgq.html"
    language = ' hreflang="fr"' if locale not in COPY else ""
    suffix = '<span lang="fr"> · Français</span>' if locale not in COPY else ""
    clip = next(clip for clip in CLIPS if clip["id"] == "trailer")
    return (
        '<section class="section hgq-catalogue-feature"><div class="container hgq-catalogue-panel">'
        '<div class="hgq-catalogue-copy"><div class="hgq-identity">'
        f'<img src="{base}assets/apps/hgq-logo-192.webp" width="192" height="212" alt="" loading="lazy">'
        '<p class="eyebrow">Hard Gamer Quiz</p></div>'
        f'<h2>{heading}</h2><p class="lede">{description}</p><div class="actions">'
        f'<a class="button" href="{base}{target}"{language}>{cta}{suffix}</a></div></div>'
        '<figure class="hgq-film"><video class="hgq-video" '
        f'src="{base}{clip["video"]}" poster="{base}{clip["poster"]}" controls playsinline preload="none" '
        f'width="540" height="960" lang="fr" aria-label="Hard Gamer Quiz · FIGHT · GAME OVER"></video>'
        f'<figcaption class="section-note">{note}</figcaption></figure></div></section>'
    )


def validate(nodes, locale, base):
    videos = [node for node in nodes if node.tag == "video"]
    figures = [node for node in nodes if node.get("data-media-kind") == "RUNTIME_CAPTURE"]
    if len(videos) != len(CLIPS) or len(figures) != len(CLIPS):
        raise ValueError("HGQ_RUNTIME_CAPTURE_REQUIRED")
    for clip in CLIPS:
        found = [video for video in videos if video.get("data-hgq-runtime") == clip["id"]]
        if len(found) != 1:
            raise ValueError("HGQ_RUNTIME_CAPTURE_REQUIRED")
        video = found[0]
        attrs = dict(video.attrs)
        if (video.get("src") != base + clip["video"] or video.get("poster") != base + clip["poster"]
                or video.get("lang") != "fr" or video.get("preload") != "none"
                or not {"controls", "playsinline"} <= attrs.keys()
                or {"autoplay", "loop"} & attrs.keys()):
            raise ValueError("HGQ_RUNTIME_CAPTURE_REQUIRED")
    guides = [node for node in nodes if node.get("data-media-kind") == "JOKER_GUIDE"]
    artwork = ARTWORK[locale]
    images = [node for node in nodes if node.tag == "img" and node.get("src") == base + artwork["image"]]
    if len(guides) != 1 or len(images) != 1 or images[0].get("alt") != artwork["alt"]:
        raise ValueError("HGQ_JOKER_GUIDE_REQUIRED")
    for path, expected in FILES.items():
        asset = ROOT / path
        if not asset.is_file() or sha256(asset.read_bytes()).hexdigest() != expected:
            raise ValueError("HGQ_RUNTIME_CAPTURE_HASH_CHANGED=" + path)
