"""Modelos de instrução de resposta (estratégias de prompt).

O protótipo não depende de um modelo de linguagem externo: cada "prompt" é
uma instrução de resposta documentada que o programa aplica como modelo
(template) sobre a orientação encontrada na base. Assim a resposta nunca
inventa conteúdo: ela só reorganiza o que está na base verificada.

Modelo A - Direto: instrução mínima ("responda com a orientação e a fonte").
Modelo B - Estruturado: papel definido, formato fixo, fonte e data
obrigatórias, aviso de limitação e próximos passos.

A comparação entre os dois está em src/avaliacao.py e docs/prompts.md.
"""

import textwrap

LARGURA = 78

PROMPT_A = (
    "Responda à pergunta do cidadão usando a orientação encontrada na base "
    "e informe o link da fonte."
)

PROMPT_B = (
    "Papel: você é um assistente de orientação cidadã NÃO OFICIAL.\n"
    "Regras:\n"
    "1. Use somente a orientação encontrada na base verificada; não invente passos.\n"
    "2. Formato: título; resumo em uma frase; até 5 tópicos curtos; fonte com "
    "órgão, link e data de verificação.\n"
    "3. Linguagem simples, frases curtas, sem termos técnicos sem explicação.\n"
    "4. Se a orientação exigir confirmação, mostre o aviso.\n"
    "5. Se não houver orientação suficiente, diga isso claramente e sugira "
    "temas próximos.\n"
    "6. Nunca peça dados pessoais e não se apresente como canal de órgão público."
)

AVISO_NAO_OFICIAL = ("Este assistente não é um canal oficial. Confirme sempre "
                     "no site do órgão responsável.")
AVISO_EMERGENCIA = ("ATENÇÃO: se for uma emergência agora, ligue 190 (Polícia), "
                    "192 (SAMU) ou 193 (Bombeiros).")
AVISO_PRIVACIDADE = ("Você digitou o que parece ser {tipos}. Não é preciso "
                     "informar dados pessoais: eles foram ignorados e não foram salvos.")


def _quebrar(texto: str, recuo: str = "") -> str:
    return textwrap.fill(texto, width=LARGURA, initial_indent=recuo,
                         subsequent_indent=" " * len(recuo))


def formatar_data(iso: str) -> str:
    ano, mes, dia = iso.split("-")
    return f"{dia}/{mes}/{ano}"


# ---------------------------------------------------------------- Modelo A
def modelo_a(registro: dict) -> str:
    texto = registro["resumo"] + " " + " ".join(registro["orientacao"])
    return "\n".join([
        _quebrar(texto),
        f"Fonte: {registro['referencia']['url']}",
    ])


def modelo_a_sem_resposta(_sugestoes) -> str:
    return "Não encontrei uma resposta para essa pergunta."


# ---------------------------------------------------------------- Modelo B
def modelo_b(registro: dict, nome_tema: str = "") -> str:
    linhas = [registro["titulo"].upper()]
    if nome_tema:
        linhas.append(f"Tema: {nome_tema}")
    linhas.append("")
    linhas.append(_quebrar(registro["resumo"]))
    linhas.append("")
    for item in registro["orientacao"][:5]:
        linhas.append(_quebrar(item, recuo="  - "))
    ref = registro["referencia"]
    linhas.append("")
    linhas.append(f"Fonte: {ref['titulo']} ({ref['orgao']})")
    linhas.append(f"Link: {ref['url']}")
    linhas.append(f"Informação conferida em {formatar_data(registro['data_verificacao'])}.")
    if registro.get("requer_confirmacao"):
        linhas.append(_quebrar("Confirme antes de agir: " + registro["aviso"]))
    return "\n".join(linhas)


def modelo_b_sem_resposta(sugestoes: list) -> str:
    linhas = [_quebrar(
        "Não encontrei uma orientação confiável para essa pergunta na base. "
        "Para não passar uma informação errada, prefiro não responder."
    )]
    if sugestoes:
        linhas.append("Talvez você esteja procurando: " + "; ".join(sugestoes) + ".")
    linhas.append(_quebrar(
        "Você também pode escolher um tema no menu principal ou procurar o "
        "site oficial do órgão responsável."
    ))
    return "\n".join(linhas)


MODELOS = {
    "A": {"nome": "Modelo A - Direto", "prompt": PROMPT_A,
          "resposta": lambda r, tema="": modelo_a(r), "sem_resposta": modelo_a_sem_resposta},
    "B": {"nome": "Modelo B - Estruturado", "prompt": PROMPT_B,
          "resposta": modelo_b, "sem_resposta": modelo_b_sem_resposta},
}
