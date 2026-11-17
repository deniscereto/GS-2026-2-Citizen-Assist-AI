"""Leitura e validação da base de conhecimento (arquivo JSON).

As regras do programa não dependem do conteúdo: para acrescentar ou corrigir
uma orientação, basta editar data/base_conhecimento.json. Ao carregar, cada
registro é validado; registros inconsistentes são ignorados com um aviso, em
vez de derrubar o programa.
"""

import json
from datetime import date
from pathlib import Path

CAMPOS_OBRIGATORIOS = {
    "id": str,
    "tema": str,
    "subtema": str,
    "titulo": str,
    "perguntas": list,
    "palavras_chave": list,
    "resumo": str,
    "orientacao": list,
    "referencia": dict,
    "data_verificacao": str,
}
CAMPOS_REFERENCIA = ("titulo", "orgao", "url")


class ErroBase(Exception):
    """Erro que impede o uso da base (arquivo ausente, vazio ou ilegível)."""


class BaseConhecimento:
    """Guarda os registros válidos e índices para acesso rápido."""

    def __init__(self, temas: dict, registros: list, avisos: list):
        self.temas = temas
        self.registros = registros
        self.avisos = avisos
        # Dicionário id -> registro: busca por identificador em O(1).
        self.por_id = {r["id"]: r for r in registros}
        # Dicionário tema -> lista de registros.
        self.por_tema = {}
        for r in registros:
            self.por_tema.setdefault(r["tema"], []).append(r)

    def nome_tema(self, tema: str) -> str:
        return self.temas.get(tema, {}).get("nome", tema)

    def nome_subtema(self, tema: str, subtema: str) -> str:
        return self.temas.get(tema, {}).get("subtemas", {}).get(subtema, subtema)

    def temas_disponiveis(self) -> list:
        """Temas que têm ao menos um registro válido, na ordem do arquivo."""
        return [t for t in self.temas if t in self.por_tema]

    def registros_do_subtema(self, tema: str, subtema: str) -> list:
        return [r for r in self.por_tema.get(tema, []) if r["subtema"] == subtema]


def validar_registro(registro: dict, temas: dict) -> list:
    """Retorna a lista de problemas do registro (vazia se estiver válido)."""
    problemas = []
    if not isinstance(registro, dict):
        return ["registro não é um objeto JSON"]

    for campo, tipo in CAMPOS_OBRIGATORIOS.items():
        valor = registro.get(campo)
        if valor is None:
            problemas.append(f"campo obrigatório ausente: {campo}")
        elif not isinstance(valor, tipo):
            problemas.append(f"campo {campo} deveria ser {tipo.__name__}")
        elif isinstance(valor, (str, list)) and len(valor) == 0:
            problemas.append(f"campo {campo} está vazio")
    if problemas:
        return problemas

    ref = registro["referencia"]
    for campo in CAMPOS_REFERENCIA:
        if not str(ref.get(campo, "")).strip():
            problemas.append(f"referência sem o campo {campo}")
    if not str(ref.get("url", "")).startswith(("http://", "https://")):
        problemas.append("referência sem URL verificável (http/https)")

    try:
        date.fromisoformat(registro["data_verificacao"])
    except ValueError:
        problemas.append("data_verificacao fora do formato AAAA-MM-DD")

    tema = registro["tema"]
    if tema not in temas:
        problemas.append(f"tema desconhecido: {tema}")
    elif registro["subtema"] not in temas[tema].get("subtemas", {}):
        problemas.append(f"subtema desconhecido: {registro['subtema']}")

    if registro.get("requer_confirmacao") and not str(registro.get("aviso", "")).strip():
        problemas.append("requer_confirmacao=true, mas o aviso está vazio")
    return problemas


def carregar_base(caminho) -> BaseConhecimento:
    """Lê o JSON, valida e devolve a base. Lança ErroBase se não der para usar."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroBase(f"Arquivo da base não encontrado: {caminho}")
    texto = caminho.read_text(encoding="utf-8").strip()
    if not texto:
        raise ErroBase(f"O arquivo da base está vazio: {caminho}")
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as erro:
        raise ErroBase(f"A base não é um JSON válido (linha {erro.lineno}): {erro.msg}")

    if not isinstance(dados, dict) or not isinstance(dados.get("registros"), list):
        raise ErroBase("A base precisa ter a lista 'registros'.")
    temas = dados.get("temas")
    if not isinstance(temas, dict) or not temas:
        raise ErroBase("A base precisa ter o dicionário 'temas'.")

    validos, avisos, ids_vistos = [], [], set()
    for posicao, registro in enumerate(dados["registros"], start=1):
        problemas = validar_registro(registro, temas)
        rid = registro.get("id", f"posição {posicao}") if isinstance(registro, dict) else f"posição {posicao}"
        if not problemas and rid in ids_vistos:
            problemas.append("id repetido")
        if problemas:
            avisos.append(f"Registro {rid} ignorado: " + "; ".join(problemas))
            continue
        ids_vistos.add(rid)
        registro.setdefault("relacionados", [])
        registro.setdefault("requer_confirmacao", False)
        registro.setdefault("aviso", "")
        validos.append(registro)

    if not validos:
        raise ErroBase("Nenhum registro válido na base.")

    # Ligações para ids inexistentes são removidas (não quebram a navegação).
    for registro in validos:
        faltando = [r for r in registro["relacionados"] if r not in ids_vistos]
        if faltando:
            avisos.append(f"Registro {registro['id']}: relacionados inexistentes removidos {faltando}")
            registro["relacionados"] = [r for r in registro["relacionados"] if r in ids_vistos]

    return BaseConhecimento(temas, validos, avisos)


def carregar_sinonimos(caminho) -> dict:
    """Sinônimos são opcionais: se o arquivo faltar ou estiver inválido, segue sem eles."""
    caminho = Path(caminho)
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        return dados.get("sinonimos", {})
    except (OSError, json.JSONDecodeError, AttributeError):
        return {}
