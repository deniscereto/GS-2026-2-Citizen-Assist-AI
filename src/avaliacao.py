"""Avaliação do Citizen Assist AI.

Executa:
  1. As perguntas de teste (data/perguntas_teste.json) e as de validação
     (data/perguntas_validacao.json), registrando resposta esperada, obtida,
     acerto e tempo de consulta.
  2. A comparação entre os dois modelos de resposta (A e B).
  3. O roteiro de tarefas de usabilidade, simulando um usuário no menu.

Uso:  python src/avaliacao.py
Saída: docs/resultados/*.csv, docs/resultados/grafico_acertos.png e
       docs/resultados_avaliacao.md
"""

import csv
import json
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

from assistente import RESPONDIDA, SEM_RESPOSTA, Assistente
from respostas import MODELOS
from texto import remover_acentos

RAIZ = Path(__file__).resolve().parent.parent
PASTA_SAIDA = RAIZ / "docs" / "resultados"
REPETICOES = 30  # cada pergunta é repetida para medir um tempo mais estável


# ======================================================================
# 1. Perguntas de teste
# ======================================================================
def avaliar_conjunto(assistente, arquivo: str, nome_conjunto: str) -> list:
    perguntas = json.loads((RAIZ / "data" / arquivo).read_text(encoding="utf-8"))["perguntas"]
    linhas = []
    for item in perguntas:
        tempos = []
        for _ in range(REPETICOES):
            consulta = assistente.consultar(item["pergunta"])
            tempos.append(consulta.tempo_ms)
        id_obtido = consulta.ids[0] if consulta.situacao == RESPONDIDA else ""
        acerto = consulta.situacao == item["esperado"] and (
            item["id_esperado"] is None or id_obtido == item["id_esperado"])
        linhas.append({
            "conjunto": nome_conjunto,
            "n": item["n"],
            "tipo": item["tipo"],
            "pergunta": item["pergunta"],
            "esperado": item["esperado"],
            "id_esperado": item["id_esperado"] or "",
            "obtido": consulta.situacao,
            "id_obtido": id_obtido if id_obtido else "/".join(consulta.ids),
            "pontuacao": consulta.pontuacao,
            "acerto": "acerto" if acerto else "erro",
            "tempo_ms": round(statistics.mean(tempos), 4),
        })
    return linhas


def resumo_conjunto(linhas: list) -> dict:
    acertos = sum(1 for l in linhas if l["acerto"] == "acerto")
    tempos = [l["tempo_ms"] for l in linhas]
    por_tipo = {}
    for l in linhas:
        total, ok = por_tipo.get(l["tipo"], (0, 0))
        por_tipo[l["tipo"]] = (total + 1, ok + (l["acerto"] == "acerto"))
    return {
        "perguntas": len(linhas),
        "acertos": acertos,
        "taxa_acerto": round(100 * acertos / len(linhas), 1),
        "tempo_medio_ms": round(statistics.mean(tempos), 4),
        "tempo_mediano_ms": round(statistics.median(tempos), 4),
        "tempo_maximo_ms": round(max(tempos), 4),
        "por_tipo": {t: {"perguntas": a, "acertos": b} for t, (a, b) in por_tipo.items()},
    }


# ======================================================================
# 2. Comparação dos modelos de resposta
# ======================================================================
def contar_silabas(palavra: str) -> int:
    """Aproximação: cada grupo de vogais conta como uma sílaba."""
    return max(1, len(re.findall(r"[aeiouy]+", remover_acentos(palavra.lower()))))


def legibilidade(texto: str) -> dict:
    """Índice Flesch adaptado ao português (Martins et al., 1996).

    Quanto maior, mais fácil: 75-100 muito fácil; 50-75 fácil;
    25-50 difícil; 0-25 muito difícil. Linhas de fonte/link são ignoradas.
    """
    corpo = "\n".join(l for l in texto.splitlines()
                      if not l.startswith(("Fonte:", "Link:", "Tema:")) and "http" not in l)
    frases = [f for f in re.split(r"[.!?:]\s|\n\s*-\s|\n\n", corpo) if f.strip()]
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", corpo)
    if not palavras or not frases:
        return {"palavras_por_frase": 0, "indice_flesch": 0}
    ppf = len(palavras) / len(frases)
    spp = sum(contar_silabas(p) for p in palavras) / len(palavras)
    return {"palavras_por_frase": round(ppf, 1),
            "indice_flesch": round(248.835 - 1.015 * ppf - 84.6 * spp, 1)}


def avaliar_resposta(texto: str, registro: dict) -> dict:
    criterios = {
        "cita_link_da_fonte": "http" in texto,
        "cita_orgao_da_fonte": registro["referencia"]["orgao"] in texto,
        "mostra_data_de_verificacao": "conferida em" in texto,
        "aviso_quando_necessario": (not registro.get("requer_confirmacao"))
                                   or ("Confirme" in texto),
        "organizado_em_topicos": "\n  - " in texto,
    }
    criterios.update(legibilidade(texto))
    return criterios


def comparar_modelos(assistente, linhas_teste: list) -> list:
    resultado = []
    for linha in linhas_teste:
        if linha["obtido"] == RESPONDIDA:
            registro = assistente.base.por_id[linha["id_obtido"]]
            for chave in ("A", "B"):
                texto = MODELOS[chave]["resposta"](registro, assistente.base.nome_tema(registro["tema"]))
                resultado.append({"n": linha["n"], "situacao": RESPONDIDA, "modelo": chave,
                                  **avaliar_resposta(texto, registro)})
        elif linha["obtido"] == SEM_RESPOSTA:
            sugestoes = assistente.busca.sugerir_palavras(linha["pergunta"])
            for chave in ("A", "B"):
                texto = MODELOS[chave]["sem_resposta"](sugestoes)
                resultado.append({
                    "n": linha["n"], "situacao": SEM_RESPOSTA, "modelo": chave,
                    "explica_o_limite": "não responder" in texto or "confiável" in texto,
                    "indica_caminho_alternativo": "tema" in texto or "site oficial" in texto,
                })
    return resultado


def resumo_modelos(comparacao: list) -> dict:
    resumo = {}
    for chave in ("A", "B"):
        respondidas = [c for c in comparacao if c["modelo"] == chave and c["situacao"] == RESPONDIDA]
        sem = [c for c in comparacao if c["modelo"] == chave and c["situacao"] == SEM_RESPOSTA]
        criterios = ["cita_link_da_fonte", "cita_orgao_da_fonte", "mostra_data_de_verificacao",
                     "aviso_quando_necessario", "organizado_em_topicos"]
        item = {c: round(100 * sum(r[c] for r in respondidas) / len(respondidas), 1)
                for c in criterios}
        item["palavras_por_frase"] = round(statistics.mean(r["palavras_por_frase"] for r in respondidas), 1)
        item["indice_flesch"] = round(statistics.mean(r["indice_flesch"] for r in respondidas), 1)
        if sem:
            item["sem_resposta_explica_limite"] = round(100 * sum(r["explica_o_limite"] for r in sem) / len(sem), 1)
            item["sem_resposta_indica_caminho"] = round(100 * sum(r["indica_caminho_alternativo"] for r in sem) / len(sem), 1)
        item["checklist_medio"] = round(statistics.mean(item[c] for c in criterios), 1)
        resumo[chave] = item
    return resumo


# ======================================================================
# 3. Roteiro de tarefas (usabilidade)
# ======================================================================
TAREFAS = [
    {"id": "T1", "tarefa": "Descobrir o telefone do INSS fazendo uma pergunta",
     "entradas": ["1", "qual o telefone do INSS?"], "esperado": "135"},
    {"id": "T2", "tarefa": "Achar o direito de arrependimento navegando pelos temas",
     "entradas": ["2", "3", "1", "1"], "esperado": "7 dias"},
    {"id": "T3", "tarefa": "A partir de uma resposta, abrir um assunto relacionado",
     "entradas": ["1", "devolver compra feita pela internet", "1"], "esperado": "90 dias"},
    {"id": "T4", "tarefa": "Fazer uma pergunta fora do tema e entender o aviso",
     "entradas": ["1", "como renovar o passaporte", "n"], "esperado": "Não encontrei"},
    {"id": "T5", "tarefa": "Resolver uma pergunta ambígua escolhendo a opção certa",
     "entradas": ["1", "carteira", "2"], "esperado": "Carteira de Trabalho Digital"},
    {"id": "T6", "tarefa": "Trocar para o formato de resposta curto",
     "entradas": ["4"], "esperado": "Modelo A - Direto"},
]


def executar_roteiro() -> list:
    resultado = []
    for tarefa in TAREFAS:
        entrada = "\n".join(tarefa["entradas"] + ["0"] * 8) + "\n"
        inicio = time.perf_counter()
        processo = subprocess.run([sys.executable, str(RAIZ / "src" / "sistema.py")],
                                  input=entrada, capture_output=True, text=True,
                                  encoding="utf-8", timeout=30)
        duracao = (time.perf_counter() - inicio) * 1000
        concluida = tarefa["esperado"] in processo.stdout and processo.returncode == 0
        invalidas = processo.stdout.count("Opção inválida")
        resultado.append({"id": tarefa["id"], "tarefa": tarefa["tarefa"],
                          "passos": len(tarefa["entradas"]),
                          "concluida": "sim" if concluida else "não",
                          "mensagens_de_erro": invalidas,
                          "tempo_execucao_ms": round(duracao, 1)})
    return resultado


# ======================================================================
def salvar_csv(nome: str, linhas: list):
    with open(PASTA_SAIDA / nome, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]), delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)


def gerar_grafico(resumos: dict):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    tipos = ["direta", "reformulada", "erro_digitacao", "fora_do_tema", "limitacao", "privacidade"]
    fig, ax = plt.subplots(figsize=(8, 4))
    largura = 0.38
    rotulos_tipo = {"direta": "direta", "reformulada": "reformulada",
                    "erro_digitacao": "erro de\ndigitação", "fora_do_tema": "fora do tema",
                    "limitacao": "limitação", "privacidade": "privacidade"}
    nomes = {"teste": "Teste", "validacao": "Validação"}
    for i, (nome, cor) in enumerate([("teste", "#2E6F95"), ("validacao", "#E08A2E")]):
        por_tipo = resumos[nome]["por_tipo"]
        taxas = [100 * por_tipo[t]["acertos"] / por_tipo[t]["perguntas"] if t in por_tipo else 0
                 for t in tipos]
        posicoes = [x + (i - 0.5) * largura for x in range(len(tipos))]
        barras = ax.bar(posicoes, taxas, largura, label=f"{nomes[nome]} ({resumos[nome]['taxa_acerto']}%)",
                        color=cor)
        for barra, t in zip(barras, tipos):
            if t in por_tipo:
                ax.annotate(f"{por_tipo[t]['acertos']}/{por_tipo[t]['perguntas']}",
                            (barra.get_x() + barra.get_width() / 2, barra.get_height()),
                            ha="center", va="bottom", fontsize=8)
    ax.set_xticks(range(len(tipos)))
    ax.set_xticklabels([rotulos_tipo[t] for t in tipos], fontsize=9)
    ax.set_ylabel("Taxa de acerto (%)")
    ax.set_ylim(0, 115)
    ax.set_title("Acertos por tipo de pergunta")
    ax.legend(frameon=False)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    fig.savefig(PASTA_SAIDA / "grafico_acertos.png", dpi=150)
    plt.close(fig)
    return True


def tabela_md(linhas: list, colunas: list) -> str:
    cab = "| " + " | ".join(colunas) + " |\n|" + "---|" * len(colunas) + "\n"
    return cab + "".join("| " + " | ".join(str(l[c]) for c in colunas) + " |\n" for l in linhas)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    inicio = time.perf_counter()
    assistente = Assistente(modelo="B")
    carga_ms = round((time.perf_counter() - inicio) * 1000, 2)

    teste = avaliar_conjunto(assistente, "perguntas_teste.json", "teste")
    validacao = avaliar_conjunto(assistente, "perguntas_validacao.json", "validacao")
    resumos = {"teste": resumo_conjunto(teste), "validacao": resumo_conjunto(validacao)}
    comparacao = comparar_modelos(assistente, teste)
    modelos = resumo_modelos(comparacao)
    roteiro = executar_roteiro()

    salvar_csv("resultados_testes.csv", teste + validacao)
    salvar_csv("comparacao_modelos.csv", [c for c in comparacao if c["situacao"] == RESPONDIDA])
    salvar_csv("roteiro_usabilidade.csv", roteiro)
    grafico = gerar_grafico(resumos)
    indicadores = {"carga_da_base_ms": carga_ms, "conjuntos": resumos, "modelos": modelos,
                   "roteiro": {"tarefas": len(roteiro),
                               "concluidas": sum(r["concluida"] == "sim" for r in roteiro),
                               "passos_medios": round(statistics.mean(r["passos"] for r in roteiro), 1)}}
    (PASTA_SAIDA / "indicadores.json").write_text(
        json.dumps(indicadores, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------------- relatório em Markdown ----------------
    t, v = resumos["teste"], resumos["validacao"]
    md = ["# Resultados da avaliação", "",
          "Gerado automaticamente por `python src/avaliacao.py`. Os números abaixo "
          "são da última execução.", "",
          "## Indicadores gerais", "",
          "| Indicador | Teste | Validação |", "|---|---|---|",
          f"| Perguntas | {t['perguntas']} | {v['perguntas']} |",
          f"| Acertos | {t['acertos']} | {v['acertos']} |",
          f"| **Taxa de acerto** | **{t['taxa_acerto']}%** | **{v['taxa_acerto']}%** |",
          f"| Tempo médio de consulta | {t['tempo_medio_ms']} ms | {v['tempo_medio_ms']} ms |",
          f"| Tempo mediano | {t['tempo_mediano_ms']} ms | {v['tempo_mediano_ms']} ms |",
          f"| Tempo máximo | {t['tempo_maximo_ms']} ms | {v['tempo_maximo_ms']} ms |",
          "", f"Carregamento e indexação da base: {carga_ms} ms. Cada pergunta foi "
          f"executada {REPETICOES} vezes e o tempo registrado é a média.", ""]
    if grafico:
        md += ["![Acertos por tipo](resultados/grafico_acertos.png)", ""]
    colunas = ["n", "tipo", "pergunta", "esperado", "id_esperado", "obtido", "id_obtido",
               "pontuacao", "acerto", "tempo_ms"]
    md += ["## Perguntas de teste", "", tabela_md(teste, colunas),
           "## Perguntas de validação (não usadas no ajuste)", "", tabela_md(validacao, colunas),
           "## Comparação dos modelos de resposta", "",
           "Percentual das respostas que cumprem cada critério "
           f"({sum(1 for c in comparacao if c['modelo'] == 'A' and c['situacao'] == RESPONDIDA)} "
           "respostas do conjunto de teste).", "",
           "| Critério | Modelo A (direto) | Modelo B (estruturado) |", "|---|---|---|"]
    rotulos = {
        "cita_link_da_fonte": "Cita o link da fonte (%)",
        "cita_orgao_da_fonte": "Cita o órgão da fonte (%)",
        "mostra_data_de_verificacao": "Mostra a data de verificação (%)",
        "aviso_quando_necessario": "Mostra o aviso quando a orientação exige confirmação (%)",
        "organizado_em_topicos": "Organizado em tópicos (%)",
        "checklist_medio": "**Média do checklist (%)**",
        "palavras_por_frase": "Palavras por frase (menor = mais simples)",
        "indice_flesch": "Índice de legibilidade Flesch-PT (maior = mais fácil)",
        "sem_resposta_explica_limite": "Sem resposta: explica o limite (%)",
        "sem_resposta_indica_caminho": "Sem resposta: indica outro caminho (%)",
    }
    for chave, rotulo in rotulos.items():
        md.append(f"| {rotulo} | {modelos['A'].get(chave, '-')} | {modelos['B'].get(chave, '-')} |")
    md += ["", "## Roteiro de tarefas de usabilidade (execução automatizada)", "",
           tabela_md(roteiro, ["id", "tarefa", "passos", "concluida", "mensagens_de_erro"]),
           "A avaliação por percurso cognitivo está em `docs/teste_usabilidade.md`.", ""]
    (RAIZ / "docs" / "resultados_avaliacao.md").write_text("\n".join(md), encoding="utf-8")

    print(f"Teste:     {t['acertos']}/{t['perguntas']} = {t['taxa_acerto']}%  "
          f"| tempo médio {t['tempo_medio_ms']} ms")
    print(f"Validação: {v['acertos']}/{v['perguntas']} = {v['taxa_acerto']}%  "
          f"| tempo médio {v['tempo_medio_ms']} ms")
    print(f"Modelo A checklist {modelos['A']['checklist_medio']}%  |  "
          f"Modelo B checklist {modelos['B']['checklist_medio']}%")
    print(f"Roteiro: {indicadores['roteiro']['concluidas']}/{len(roteiro)} tarefas concluídas")
    print("Relatório: docs/resultados_avaliacao.md")


if __name__ == "__main__":
    main()
