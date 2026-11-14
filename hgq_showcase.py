"""Localized web quiz and presentation copy for Hard Gamer Quiz."""
from html import escape
import hgq_runtime_media

PAD_COLORS = ("blue", "green", "yellow", "red")
PAD_MEDIA = tuple(f"assets/apps/hgq-pad-{color}.webp" for color in PAD_COLORS)
ANSWERS = ("Shigeru Miyamoto", "Markus Persson", "Hideo Kojima", "Gabe Newell")


COPY = {
    "fr": (
        "Tes souvenirs de jeu", "à l’épreuve.",
        "Reconnais les jeux, les créateurs et les univers qui ont marqué l’histoire du jeu vidéo. Joue en solo ou défie tes amis.",
        "Bientôt sur Android", "Question d’échauffement",
        "Qui est crédité comme le créateur original de Minecraft ?", "Bonne réponse", "Réessaie",
        "Les crédits officiels attribuent la création originale à Markus Persson.", "Crédits officiels",
        "À chacun son défi", "Solo", "Affûte tes connaissances à ton rythme.",
        "Multijoueur", "Joue à 2, 3 ou 4, en salon privé ou en matchmaking.",
        "Jokers", "Choisis quand utiliser un joker pour faire basculer la partie.",
    ),
    "en": (
        "Put your gaming memories", "to the test.",
        "Recognize the games, creators and worlds that shaped gaming history. Play solo or challenge your friends.",
        "Coming to Android", "Warm-up question",
        "Who is credited as the original creator of Minecraft?", "Correct", "Try again",
        "The official credits name Markus Persson as the original creator.", "Official credits",
        "Pick your challenge", "Solo", "Sharpen your knowledge at your own pace.",
        "Multiplayer", "Play with 2, 3 or 4 players in private rooms or matchmaking.",
        "Jokers", "Choose when to use a joker to turn the round around.",
    ),
    "es": (
        "Pon a prueba", "tu memoria gamer.",
        "Reconoce los juegos, creadores y mundos que marcaron la historia del videojuego. Juega en solitario o reta a tus amigos.",
        "Próximamente en Android", "Pregunta de calentamiento",
        "¿Quién figura en los créditos como creador original de Minecraft?", "Respuesta correcta", "Inténtalo de nuevo",
        "Los créditos oficiales atribuyen la creación original a Markus Persson.", "Créditos oficiales",
        "Elige tu reto", "Solitario", "Pon a punto tus conocimientos a tu ritmo.",
        "Multijugador", "Juega con 2, 3 o 4 personas en salas privadas o mediante emparejamiento.",
        "Comodines", "Elige cuándo usar un comodín para dar la vuelta a la partida.",
    ),
    "pt": (
        "Põe à prova", "a tua memória gamer.",
        "Reconhece os jogos, os criadores e os mundos que marcaram a história dos videojogos. Joga a solo ou desafia os teus amigos.",
        "Em breve no Android", "Pergunta de aquecimento",
        "Quem aparece nos créditos como criador original de Minecraft?", "Resposta certa", "Tenta de novo",
        "Os créditos oficiais atribuem a criação original a Markus Persson.", "Créditos oficiais",
        "Escolhe o teu desafio", "Solo", "Treina os teus conhecimentos ao teu ritmo.",
        "Multijogador", "Joga com 2, 3 ou 4 pessoas em salas privadas ou por emparelhamento.",
        "Jokers", "Escolhe quando usar um joker para mudar o rumo da partida.",
    ),
    "ja": (
        "ゲームの記憶を", "クイズで試そう。",
        "ゲームの歴史を彩った作品、クリエイター、世界を思い出そう。ひとりで遊ぶのも、友達と競うのも自由。",
        "Android版 近日登場", "ウォーミングアップ問題",
        "Minecraftのオリジナル制作者としてクレジットされているのは誰？", "正解", "もう一度",
        "公式クレジットではMarkus Perssonがオリジナル制作者です。", "公式クレジット",
        "遊び方を選ぼう", "ソロ", "自分のペースで知識を磨こう。",
        "マルチプレイ", "プライベートルームやマッチメイクで2〜4人対戦。",
        "ジョーカー", "ここぞという場面でジョーカーを使い、流れを変えよう。",
    ),
    "ko": (
        "게임의 추억을", "퀴즈로 겨뤄 보세요.",
        "게임 역사에 한 획을 그은 작품, 개발자, 세계를 떠올려 보세요. 혼자 풀거나 친구와 대결할 수 있어요.",
        "Android 출시 예정", "몸풀기 문제",
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
    options = []
    for index, name in enumerate(ANSWERS):
        answer = f"<strong>{correct}</strong> {explanation} <a href='https://www.minecraft.net/fr-fr/credits'>{credits}</a>" if index == 1 else retry
        options.append(f'<details name="hgq-warmup" class="hgq-answer{" is-correct" if index == 1 else ""}"><summary data-pad="{PAD_COLORS[index]}"><img src="{PAD_MEDIA[index]}" width="160" height="145" alt=""><span>{name}</span></summary><p>{answer}</p></details>')
    cards = ''.join(
        f'<article class="card hgq-mode"><span aria-hidden="true">{index:02}</span><h3>{title}</h3><p>{description}</p></article>'
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
      <div class="actions"><a class="button" href="#apercus">{warmup}</a></div>
    </div>
    <aside class="hgq-quiz" id="apercus" aria-labelledby="hgq-question">
      <p class="hgq-quiz-kicker">{warmup} <span aria-hidden="true">01 / 01</span></p>
      <h2 id="hgq-question">{question}</h2>
      <div class="hgq-answers">{''.join(options)}</div>
    </aside>
  </div>
</section>
{hgq_runtime_media.render(locale)}
<section class="section" id="univers"><div class="container">
  <h2>{modes}</h2><div class="grid">{cards}</div>
</div></section>
'''
