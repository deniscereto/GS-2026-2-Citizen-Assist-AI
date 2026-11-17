"""Regras de resposta do Citizen Assist AI.

Fluxo de uma consulta:
  validar a entrada -> mascarar dados pessoais -> buscar na base ->
  decidir (resposta / ambígua / sem resposta) -> montar o texto com o modelo
  de resposta escolhido -> sugerir assuntos relacionados (grafo).
"""

import time
from dataclasses import dataclass, field
from pathlib import Path

from base_conhecimento import carregar_base, carregar_sinonimos
from busca import FATOR_AMBIGUIDADE, LIMIAR_RESPOSTA, MotorBusca
from grafo import GrafoAssuntos, montar_hierarquia
from respostas import (AVISO_EMERGENCIA, AVISO_NAO_OFICIAL, AVISO_PRIVACIDADE,
                       MODELOS)
from texto import mascarar_dados_pessoais, normalizar

PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"
TAMANHO_MAXIMO = 300

# Situações possíveis de uma consulta
RESPONDIDA = "respondida"
AMBIGUA = "ambigua"
SEM_RESPOSTA = "sem_resposta"
INVALIDA = "invalida"


@dataclass
class Consulta:
    pergunta: str
    situacao: str
    texto: str
    ids: list = field(default_factory=list)      # orientação escolhida ou opções
    pontuacao: float = 0.0
    relacionados: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    tempo_ms: float = 0.0


class Assistente:
    def __init__(self, caminho_base=None, caminho_sinonimos=None, modelo: str = "B"):
        self.base = carregar_base(caminho_base or PASTA_DADOS / "base_conhecimento.json")
        sinonimos = carregar_sinonimos(caminho_sinonimos or PASTA_DADOS / "sinonimos.json")
        self.busca = MotorBusca(self.base, sinonimos)
        self.grafo = GrafoAssuntos(self.base)
        self.hierarquia = montar_hierarquia(self.base)
        self.modelo = modelo

    # ------------------------------------------------------------------
    @staticmethod
    def validar_entrada(pergunta) -> str | None:
        """Retorna a mensagem de erro, ou None se a pergunta puder ser buscada."""
        if pergunta is None or not str(pergunta).strip():
            return "A pergunta está vazia. Escreva sua dúvida, por exemplo: \"como tirar a carteira de trabalho\"."
        if len(pergunta) > TAMANHO_MAXIMO:
            return f"A pergunta é muito longa. Use até {TAMANHO_MAXIMO} caracteres e foque em uma dúvida por vez."
        letras = [c for c in normalizar(pergunta) if c.isalpha()]
        if len(letras) < 3:
            return "Não entendi a pergunta. Use palavras, por exemplo: \"telefone do INSS\"."
        return None

    def texto_orientacao(self, rid: str) -> str:
        registro = self.base.por_id[rid]
        formatador = MODELOS[self.modelo]["resposta"]
        return formatador(registro, self.base.nome_tema(registro["tema"]))

    def relacionados(self, rid: str) -> list:
        return [vizinho for vizinho, _ in self.grafo.relacionados_bfs(rid, limite=3)]

    # ------------------------------------------------------------------
    def consultar(self, pergunta: str) -> Consulta:
        inicio = time.perf_counter()
        consulta = self._consultar(pergunta)
        consulta.tempo_ms = round((time.perf_counter() - inicio) * 1000, 3)
        return consulta

    def _consultar(self, pergunta: str) -> Consulta:
        erro = self.validar_entrada(pergunta)
        if erro:
            return Consulta(pergunta, INVALIDA, erro)

        avisos = []
        limpa, tipos = mascarar_dados_pessoais(pergunta)
        if tipos:
            avisos.append(AVISO_PRIVACIDADE.format(tipos=", ".join(tipos)))
            if self.validar_entrada(limpa):
                return Consulta(pergunta, INVALIDA, avisos[0], avisos=avisos)

        resultado = self.busca.buscar(limpa)
        if resultado.emergencia:
            avisos.insert(0, AVISO_EMERGENCIA)
        if resultado.correcoes:
            trocas = ", ".join(f"\"{a}\" -> \"{b}\"" for a, b in resultado.correcoes.items())
            avisos.append(f"Considerei: {trocas}.")

        candidatos = resultado.candidatos
        if not candidatos or candidatos[0].pontuacao < LIMIAR_RESPOSTA:
            sugestoes = self.busca.sugerir_palavras(limpa)
            texto = MODELOS[self.modelo]["sem_resposta"](sugestoes)
            return Consulta(pergunta, SEM_RESPOSTA, texto,
                            pontuacao=candidatos[0].pontuacao if candidatos else 0.0,
                            avisos=avisos)

        primeiro = candidatos[0]
        empatados = [c for c in candidatos[1:]
                     if c.pontuacao >= LIMIAR_RESPOSTA
                     and c.pontuacao >= FATOR_AMBIGUIDADE * primeiro.pontuacao]
        if empatados:
            opcoes = [primeiro.id] + [c.id for c in empatados]
            linhas = ["Sua pergunta pode ser sobre mais de um assunto. Qual deles?"]
            for n, rid in enumerate(opcoes, start=1):
                linhas.append(f"  {n}. {self.base.por_id[rid]['titulo']}")
            return Consulta(pergunta, AMBIGUA, "\n".join(linhas), ids=opcoes,
                            pontuacao=primeiro.pontuacao, avisos=avisos)

        return Consulta(pergunta, RESPONDIDA, self.texto_orientacao(primeiro.id),
                        ids=[primeiro.id], pontuacao=primeiro.pontuacao,
                        relacionados=self.relacionados(primeiro.id), avisos=avisos)


AVISO_GERAL = AVISO_NAO_OFICIAL
