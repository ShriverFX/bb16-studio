"""Localized web quiz and presentation copy for Hard Gamer Quiz."""
from html import escape
import hgq_runtime_media
import hgq_warmup_media

PAD_COLORS = ("blue", "green", "yellow", "red")
PAD_MEDIA = tuple(f"assets/apps/hgq-pad-{color}.webp" for color in PAD_COLORS)
ANSWERS = ("Shigeru Miyamoto", "Markus Persson", "Hideo Kojima", "Gabe Newell")

WARMUP_COPY = {
    "fr": ("Lancer l’échauffement", "Rejouer", "Couper le son", "Activer le son", "1 / 1 · Bonne réponse", "0 / 1 · Réessaie", "Musique principale : Quartier Arcade"),
    "en": ("Start the warm-up", "Play again", "Mute sound", "Turn sound on", "1 / 1 · Correct", "0 / 1 · Try again", "Main theme: Quartier Arcade"),
    "es": ("Empezar el calentamiento", "Volver a jugar", "Silenciar", "Activar el sonido", "1 / 1 · Respuesta correcta", "0 / 1 · Inténtalo de nuevo", "Tema principal: Quartier Arcade"),
    "pt": ("Começar o aquecimento", "Jogar de novo", "Desligar o som", "Ativar o som", "1 / 1 · Resposta certa", "0 / 1 · Tenta de novo", "Tema principal: Quartier Arcade"),
    "ja": ("ウォームアップ開始", "もう一度プレイ", "音を消す", "音を出す", "1 / 1 · 正解", "0 / 1 · もう一度", "メインテーマ：Quartier Arcade"),
    "ko": ("몸풀기 시작", "다시 플레이", "소리 끄기", "소리 켜기", "1 / 1 · 정답", "0 / 1 · 다시 도전", "메인 테마: Quartier Arcade"),
}


COPY = {
    "fr": (
        "Tu connais les jeux.", "Prouve-le.",
        "Reconnais les jeux, les créateurs et les univers qui ont marqué l’histoire du jeu vidéo. Joue en solo ou défie tes amis.",
        "En test sur Android", "Question d’échauffement",
        "Qui est crédité comme le créateur original de Minecraft ?", "Bonne réponse", "Réessaie",
        "Les crédits officiels attribuent la création originale à Markus Persson.", "Crédits officiels",
        "À chacun son défi", "Solo", "Affûte tes connaissances à ton rythme.",
        "Multijoueur", "Joue à 2, 3 ou 4, en salon privé ou en matchmaking.",
        "Jokers", "Choisis quand utiliser un joker pour faire basculer la partie.",
    ),
    "en": (
        "You know the games.", "Prove it.",
        "Recognize the games, creators and worlds that shaped gaming history. Play solo or challenge your friends.",
        "In testing on Android", "Warm-up question",
        "Who is credited as the original creator of Minecraft?", "Correct", "Try again",
        "The official credits name Markus Persson as the original creator.", "Official credits",
        "Pick your challenge", "Solo", "Sharpen your knowledge at your own pace.",
        "Multiplayer", "Play with 2, 3 or 4 players in private rooms or matchmaking.",
        "Jokers", "Choose when to use a joker to turn the round around.",
    ),
    "es": (
        "Conoces los juegos.", "Demuéstralo.",
        "Reconoce los juegos, creadores y mundos que marcaron la historia del videojuego. Juega en solitario o reta a tus amigos.",
        "En pruebas para Android", "Pregunta de calentamiento",
        "¿Quién figura en los créditos como creador original de Minecraft?", "Respuesta correcta", "Inténtalo de nuevo",
        "Los créditos oficiales atribuyen la creación original a Markus Persson.", "Créditos oficiales",
        "Elige tu reto", "Solitario", "Pon a punto tus conocimientos a tu ritmo.",
        "Multijugador", "Juega con 2, 3 o 4 personas en salas privadas o mediante emparejamiento.",
        "Comodines", "Elige cuándo usar un comodín para dar la vuelta a la partida.",
    ),
    "pt": (
        "Conheces os jogos.", "Prova-o.",
        "Reconhece os jogos, os criadores e os mundos que marcaram a história dos videojogos. Joga a solo ou desafia os teus amigos.",
        "Em testes no Android", "Pergunta de aquecimento",
        "Quem aparece nos créditos como criador original de Minecraft?", "Resposta certa", "Tenta de novo",
        "Os créditos oficiais atribuem a criação original a Markus Persson.", "Créditos oficiais",
        "Escolhe o teu desafio", "Solo", "Treina os teus conhecimentos ao teu ritmo.",
        "Multijogador", "Joga com 2, 3 ou 4 pessoas em salas privadas ou por emparelhamento.",
        "Jokers", "Escolhe quando usar um joker para mudar o rumo da partida.",
    ),
    "ja": (
        "そのゲームの知識を、", "いざ勝負。",
        "ゲームの歴史を彩った作品、クリエイター、世界を思い出そう。ひとりで遊ぶのも、友達と競うのも自由。",
        "Android版 テスト中", "ウォーミングアップ問題",
        "Minecraftのオリジナル制作者としてクレジットされているのは誰？", "正解", "もう一度",
        "公式クレジットではMarkus Perssonがオリジナル制作者です。", "公式クレジット",
        "遊び方を選ぼう", "ソロ", "自分のペースで知識を磨こう。",
        "マルチプレイ", "プライベートルームやマッチメイクで2〜4人対戦。",
        "ジョーカー", "ここぞという場面でジョーカーを使い、流れを変えよう。",
    ),
    "ko": (
        "게임 지식으로", "승부하세요.",
        "게임 역사에 한 획을 그은 작품, 개발자, 세계를 떠올려 보세요. 혼자 풀거나 친구와 대결할 수 있어요.",
        "Android 버전 테스트 중", "몸풀기 문제",
        "Minecraft의 최초 제작자로 크레딧에 이름을 올린 사람은 누구일까요?", "정답", "다시 도전",
        "공식 크레딧은 Markus Persson을 최초 제작자로 명시합니다.", "공식 크레딧",
        "도전 방식 고르기", "솔로", "내 속도에 맞춰 게임 지식을 쌓아 보세요.",
        "멀티플레이", "비공개 방이나 매치메이킹에서 2~4명이 함께 플레이하세요.",
        "조커", "결정적인 순간에 조커를 사용해 경기의 흐름을 바꿔 보세요.",
    ),
}


def render(locale):
    (first, second, lead, status, warmup, question, correct, retry, explanation, credits,
     modes, solo, solo_copy, multi, multi_copy, jokers, joker_copy) = map(escape, COPY[locale])
    play, replay, mute, unmute, won, lost, music = map(escape, WARMUP_COPY[locale])
    options = []
    for index, name in enumerate(ANSWERS):
        answer = f"<strong>{correct}</strong> {explanation} <a href='https://www.minecraft.net/fr-fr/credits'>{credits}</a>" if index == 1 else retry
        options.append(f'<details name="hgq-warmup" class="hgq-answer{" is-correct" if index == 1 else ""}" data-warmup-answer data-correct="{str(index == 1).lower()}"><summary data-pad="{PAD_COLORS[index]}" data-warmup-option><img src="{PAD_MEDIA[index]}" width="160" height="145" alt="" loading="lazy" decoding="async"><span>{name}</span></summary><p>{answer}</p></details>')
    cards = ''.join(
        f'<article class="card hgq-mode"><h3>{title}</h3><p>{description}</p></article>'
        for index, (title, description) in enumerate(((solo, solo_copy), (multi, multi_copy), (jokers, joker_copy)), 1)
    )
    return f'''
<section class="product-hero hgq-hero" id="presentation">
  <div class="container product-hero-grid">
    <div class="product-hero-copy">
      <div class="hgq-identity"><img src="assets/apps/hgq-logo-192.webp" width="192" height="212" alt=""><p class="eyebrow">BB16 Studio · Hard Gamer Quiz</p></div>
      <h1><span>{first}</span><span>{second}</span></h1>
      <p class="lede">{lead}</p>
      <p class="hero-status"><span class="status pending">{status}</span></p>
      <div class="actions"><a class="button" href="#gameplay">{escape(hgq_runtime_media.COPY[locale]["watch"])}</a><a class="button secondary" href="#apercus">{escape(hgq_runtime_media.COPY[locale]["try"])}</a></div>
    </div>
    <div class="hgq-hero-film">{hgq_runtime_media.player("trailer", locale)}<p class="section-note">{escape(hgq_runtime_media.COPY[locale]["note"])}</p></div>
  </div>
</section>
{hgq_runtime_media.render(locale)}
<section class="section hgq-try"><div class="container">
    <aside class="hgq-quiz" id="apercus" aria-labelledby="hgq-question" data-hgq-warmup data-state="idle"
      data-label-mute="{mute}" data-label-unmute="{unmute}" data-score-won="{won}" data-score-lost="{lost}">
      <div class="hgq-warmup-head">
        <p class="hgq-quiz-kicker">{warmup} <span aria-hidden="true">01 / 01</span></p>
        <p class="hgq-warmup-music">{music}</p>
        <div class="actions hgq-warmup-actions">
          <button class="button" type="button" data-warmup-start hidden>{play}</button>
          <button class="button secondary" type="button" data-warmup-sound aria-pressed="false" hidden>{mute}</button>
        </div>
      </div>
      <div class="hgq-warmup-callout" data-warmup-callout hidden aria-hidden="true" role="status" aria-live="assertive">FIGHT</div>
      <div data-warmup-question>
        <h2 id="hgq-question" tabindex="-1">{question}</h2>
        <div class="hgq-answers">{''.join(options)}</div>
      </div>
      <div class="hgq-warmup-result" data-warmup-result hidden role="status" aria-live="polite">
        <strong>GAME OVER</strong><p data-warmup-score></p>
        <button class="button" type="button" data-warmup-restart>{replay}</button>
      </div>
      {hgq_warmup_media.render()}
    </aside>
  </div></section>
<section class="section" id="univers"><div class="container">
  <h2>{modes}</h2><div class="grid">{cards}</div>
</div></section>
'''
