"""Citizen Assist AI - assistente de orientação cidadã (interface de texto).

Como executar (na pasta do projeto):
    python src/sistema.py                      # menu interativo
    python src/sistema.py --pergunta "telefone do INSS"
    python src/sistema.py --modelo A           # respostas no formato curto
"""

import argparse
import sys

from assistente import (AMBIGUA, AVISO_GERAL, RESPONDIDA, SEM_RESPOSTA,
                        Assistente)
from base_conhecimento import ErroBase
from respostas import MODELOS

LINHA = "-" * 78

MENU_PRINCIPAL = """
O que você quer fazer?
  1. Fazer uma pergunta
  2. Escolher um tema
  3. Ver o mapa dos assuntos
  4. Mudar o formato da resposta (atual: {formato})
  5. Sobre o assistente e seus limites
  0. Sair"""

SOBRE = """SOBRE O CITIZEN ASSIST AI
- Responde dúvidas simples sobre documentos, serviços públicos, direitos do
  consumidor e canais de emergência e denúncia.
- As respostas vêm de uma base de {total} orientações conferidas em sites
  oficiais. Cada resposta mostra a fonte e a data em que foi conferida.
- Quando não há informação suficiente, o assistente avisa e não inventa.
- Não é um canal oficial do governo e não faz pedidos em seu nome.
- Não pede e não guarda dados pessoais. Não digite CPF, telefone ou e-mail.
- Regras e valores podem mudar: confirme sempre no site do órgão."""


def configurar_saida():
    """Garante acentos corretos no terminal do Windows."""
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def ler(mensagem: str) -> str:
    """input() que trata Ctrl+C e fim de arquivo como pedido de saída."""
    try:
        return input(mensagem).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(0)


def escolher(opcoes: list, titulo: str, permitir_voltar: bool = True):
    """Mostra opções numeradas e devolve o índice escolhido (ou None = voltar)."""
    while True:
        print(f"\n{titulo}")
        for n, texto in enumerate(opcoes, start=1):
            print(f"  {n}. {texto}")
        if permitir_voltar:
            print("  0. Voltar")
        resposta = ler("Digite o número: ")
        if permitir_voltar and resposta in ("0", ""):
            return None
        if resposta.isdigit() and 1 <= int(resposta) <= len(opcoes):
            return int(resposta) - 1
        print(f"Opção inválida. Digite um número de 1 a {len(opcoes)}"
              + (" ou 0 para voltar." if permitir_voltar else "."))


# ----------------------------------------------------------------------
def mostrar_orientacao(assistente: Assistente, rid: str):
    """Mostra uma orientação e oferece assuntos relacionados (navegação)."""
    while rid:
        print(LINHA)
        print(assistente.texto_orientacao(rid))
        print(LINHA)
        relacionados = assistente.relacionados(rid)
        if not relacionados:
            return
        titulos = [assistente.base.por_id[r]["titulo"] for r in relacionados]
        escolha = escolher(titulos, "Assuntos relacionados para continuar a consulta:")
        rid = relacionados[escolha] if escolha is not None else None


def mostrar_consulta(assistente: Assistente, consulta):
    print()
    for aviso in consulta.avisos:
        print(f"* {aviso}")
    if consulta.situacao == RESPONDIDA:
        mostrar_orientacao(assistente, consulta.ids[0])
    elif consulta.situacao == AMBIGUA:
        titulos = [assistente.base.por_id[r]["titulo"] for r in consulta.ids]
        escolha = escolher(titulos, "Sua pergunta pode ser sobre mais de um assunto. Qual deles?")
        if escolha is not None:
            mostrar_orientacao(assistente, consulta.ids[escolha])
    else:
        print(consulta.texto)
        if consulta.situacao == SEM_RESPOSTA:
            if ler("\nQuer escolher um tema da lista? (s/n): ").lower().startswith("s"):
                navegar_temas(assistente)


def perguntar(assistente: Assistente):
    print("\nEscreva sua dúvida em poucas palavras (ou Enter para voltar).")
    print("Exemplo: \"como pedir o seguro-desemprego\"")
    pergunta = ler("Pergunta: ")
    if not pergunta:
        return
    mostrar_consulta(assistente, assistente.consultar(pergunta))


def navegar_temas(assistente: Assistente):
    base = assistente.base
    temas = list(assistente.hierarquia)
    while True:
        i = escolher([base.nome_tema(t) for t in temas], "Temas disponíveis:")
        if i is None:
            return
        tema = temas[i]
        subtemas = list(assistente.hierarquia[tema])
        while True:
            j = escolher([base.nome_subtema(tema, s) for s in subtemas],
                         f"{base.nome_tema(tema)} - escolha um assunto:")
            if j is None:
                break
            ids = assistente.hierarquia[tema][subtemas[j]]
            k = escolher([base.por_id[r]["titulo"] for r in ids], "Orientações:")
            if k is not None:
                mostrar_orientacao(assistente, ids[k])


def mapa_assuntos(assistente: Assistente):
    base = assistente.base
    print("\nMAPA DOS ASSUNTOS (tema > assunto > orientação [ligações])")
    for tema, subtemas in assistente.hierarquia.items():
        print(f"\n{base.nome_tema(tema)}")
        for subtema, ids in subtemas.items():
            print(f"  {base.nome_subtema(tema, subtema)}")
            for rid in ids:
                ligacoes = ", ".join(assistente.grafo.vizinhos(rid))
                print(f"    {rid} {base.por_id[rid]['titulo']}  [{ligacoes}]")
    print(f"\n{len(base.registros)} orientações e {assistente.grafo.numero_arestas()} ligações.")
    ler("\nEnter para voltar ao menu.")


def trocar_formato(assistente: Assistente):
    assistente.modelo = "A" if assistente.modelo == "B" else "B"
    print(f"\nFormato alterado para: {MODELOS[assistente.modelo]['nome']}.")


# ----------------------------------------------------------------------
def iniciar(caminho_base=None, modelo="B") -> Assistente:
    try:
        assistente = Assistente(caminho_base=caminho_base, modelo=modelo)
    except ErroBase as erro:
        print(f"Não foi possível iniciar o assistente: {erro}")
        print("Verifique o arquivo data/base_conhecimento.json e tente de novo.")
        raise SystemExit(1)
    for aviso in assistente.base.avisos:
        print(f"[aviso da base] {aviso}")
    return assistente


def menu(assistente: Assistente):
    print(LINHA)
    print("CITIZEN ASSIST AI - orientação cidadã")
    print(AVISO_GERAL)
    print("Não digite dados pessoais (CPF, telefone, e-mail).")
    print(LINHA)
    acoes = {"1": perguntar, "2": navegar_temas, "3": mapa_assuntos,
             "4": trocar_formato,
             "5": lambda a: print("\n" + SOBRE.format(total=len(a.base.registros)))}
    while True:
        print(MENU_PRINCIPAL.format(formato=MODELOS[assistente.modelo]["nome"]))
        opcao = ler("Digite o número: ")
        if opcao == "0":
            print("Até logo! Lembre-se de confirmar as informações nos sites oficiais.")
            return
        acao = acoes.get(opcao)
        if acao is None:
            print("Opção inválida. Digite um número de 0 a 5.")
            continue
        acao(assistente)


def main(argv=None):
    configurar_saida()
    parser = argparse.ArgumentParser(description="Citizen Assist AI")
    parser.add_argument("--pergunta", help="faz uma única pergunta e encerra")
    parser.add_argument("--modelo", choices=["A", "B"], default="B",
                        help="A = resposta curta; B = resposta estruturada (padrão)")
    parser.add_argument("--base", help="caminho de outra base JSON (opcional)")
    args = parser.parse_args(argv)

    assistente = iniciar(args.base, args.modelo)
    if args.pergunta is not None:
        consulta = assistente.consultar(args.pergunta)
        for aviso in consulta.avisos:
            print(f"* {aviso}")
        if consulta.situacao == RESPONDIDA:
            print(assistente.texto_orientacao(consulta.ids[0]))
            titulos = [assistente.base.por_id[r]["titulo"] for r in consulta.relacionados]
            if titulos:
                print("\nAssuntos relacionados: " + "; ".join(titulos))
        else:
            print(consulta.texto)
        print(f"\n({AVISO_GERAL})")
        return
    menu(assistente)


if __name__ == "__main__":
    main()
