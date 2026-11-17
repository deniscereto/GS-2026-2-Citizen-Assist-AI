"""Motor de busca de orientações.

Estratégia (explicada no README):
1. A pergunta é normalizada e quebrada em palavras (texto.py).
2. Expressões do dia a dia são trocadas por termos da base (sinônimos).
3. Palavras que não existem na base são aproximadas por radical comum
   (ex.: "demitiram" -> "demitido") ou por semelhança de escrita (erros de
   digitação, ex.: "desenprego" -> "desemprego").
4. Um índice invertido (dicionário palavra -> {id: peso}) diz em quais
   orientações cada palavra aparece. O peso depende do campo:
   palavra-chave 3, título 2, pergunta exemplo 1,5, resumo 1, texto 0,5.
5. Palavras raras valem mais que palavras comuns (peso IDF).
6. A pontuação de cada orientação vai de 0 a 1. As melhores são escolhidas
   com um heap (heapq.nlargest), sem ordenar a base inteira.
7. Evidência mínima: só concorre a orientação em que ao menos uma palavra
   da pergunta casou com o título ou com uma palavra-chave (peso >= 2).
   Palavras que só aparecem no texto de exemplo (ex.: "tempo") não bastam.
8. Decisão: pontuação abaixo do limiar -> sem resposta; duas melhores muito
   próximas -> pergunta ambígua (o usuário escolhe); senão -> resposta.
"""

import heapq
import math
from dataclasses import dataclass, field
from difflib import get_close_matches

from texto import normalizar, tokenizar
from trie import Trie

PESOS = {
    "palavras_chave": 3.0,
    "titulo": 2.0,
    "perguntas": 1.5,
    "resumo": 1.0,
    "orientacao": 0.5,
}
PESO_PALAVRA_COMPOSTA = 2.0  # palavra solta de uma palavra-chave composta
PESO_MAXIMO = max(PESOS.values())
LIMIAR_RESPOSTA = 0.20     # abaixo disso: não há base suficiente para orientar
FATOR_AMBIGUIDADE = 0.75   # 2º colocado com >= 75% da nota do 1º: ambígua
EVIDENCIA_MINIMA = 2.0     # ao menos uma palavra precisa casar com título ou palavra-chave
BONUS_FRASE = 0.25         # palavra-chave composta encontrada inteira na pergunta
TAMANHO_RADICAL = 6

PALAVRAS_EMERGENCIA = {
    "socorro", "urgente", "emergencia", "infarto", "desmaio", "desmaiou",
    "incendio", "fogo", "assalto", "sangrando", "afogando",
}


@dataclass
class Candidato:
    id: str
    pontuacao: float


@dataclass
class ResultadoBusca:
    candidatos: list = field(default_factory=list)   # em ordem decrescente
    termos_usados: list = field(default_factory=list)
    correcoes: dict = field(default_factory=dict)    # palavra digitada -> termo da base
    emergencia: bool = False


class MotorBusca:
    def __init__(self, base, sinonimos: dict | None = None):
        self.base = base
        self.sinonimos = {normalizar(k): [normalizar(x) for x in v]
                          for k, v in (sinonimos or {}).items()}
        self.indice = {}          # palavra -> {id: peso}
        self.frases = {}          # id -> palavras-chave compostas normalizadas
        self.trie = Trie()
        self._indexar()
        total = len(base.registros)
        # IDF: palavras presentes em poucas orientações valem mais.
        self.idf = {p: math.log(1 + total / len(ids)) for p, ids in self.indice.items()}
        self.idf_medio = sum(self.idf.values()) / len(self.idf)
        self.vocabulario = sorted(self.indice)

    # ------------------------------------------------------------------
    def _indexar(self) -> None:
        for registro in self.base.registros:
            rid = registro["id"]
            campos = {
                "palavras_chave": registro["palavras_chave"],
                "titulo": [registro["titulo"]],
                "perguntas": registro["perguntas"],
                "resumo": [registro["resumo"]],
                "orientacao": registro["orientacao"],
            }
            for campo, textos in campos.items():
                for texto in textos:
                    palavras = tokenizar(texto)
                    peso = PESOS[campo]
                    # Em "receita federal", a palavra "receita" sozinha é
                    # menos específica que a expressão inteira.
                    if campo == "palavras_chave" and len(palavras) > 1:
                        peso = PESO_PALAVRA_COMPOSTA
                    for palavra in palavras:
                        pesos = self.indice.setdefault(palavra, {})
                        pesos[rid] = max(pesos.get(rid, 0.0), peso)
            self.frases[rid] = [normalizar(k) for k in registro["palavras_chave"]
                                if len(normalizar(k).split()) > 1]
            for chave in registro["palavras_chave"]:
                chave_normal = normalizar(chave)
                for palavra in chave_normal.split():
                    self.trie.inserir(palavra, chave_normal)

    # ------------------------------------------------------------------
    def _expandir(self, pergunta_normal: str):
        """Troca expressões do dia a dia pelos termos da base.

        Retorna (texto_sem_as_expressoes, termos_acrescentados)."""
        extras = []
        texto = f" {pergunta_normal} "
        for expressao, termos in self.sinonimos.items():
            if f" {expressao} " in texto:
                texto = texto.replace(f" {expressao} ", " ")
                for termo in termos:
                    extras.extend(tokenizar(termo))
        return texto.strip(), extras

    def _aproximar(self, palavra: str):
        """Para palavras fora do vocabulário: radical comum ou erro de digitação."""
        if len(palavra) >= TAMANHO_RADICAL:
            radical = palavra[:TAMANHO_RADICAL]
            mesmos = [v for v in self.vocabulario if v.startswith(radical)]
            if mesmos:
                return min(mesmos, key=len)
        if len(palavra) >= 6:
            parecidas = get_close_matches(palavra, self.vocabulario, n=1, cutoff=0.85)
            if parecidas:
                return parecidas[0]
        return None

    def preparar_termos(self, pergunta: str):
        normal = normalizar(pergunta)
        restante, extras = self._expandir(normal)
        termos, correcoes = [], {}
        for palavra in tokenizar(restante) + extras:
            if palavra in self.indice:
                termos.append(palavra)
            else:
                aproximada = self._aproximar(palavra)
                if aproximada:
                    correcoes[palavra] = aproximada
                    termos.append(aproximada)
                else:
                    termos.append(palavra)  # continua contando no denominador
        # Remove repetições mantendo a ordem.
        vistos, unicos = set(), []
        for t in termos:
            if t not in vistos:
                vistos.add(t)
                unicos.append(t)
        return unicos, correcoes, normal

    # ------------------------------------------------------------------
    def buscar(self, pergunta: str, k: int = 3) -> ResultadoBusca:
        termos, correcoes, normal = self.preparar_termos(pergunta)
        resultado = ResultadoBusca(termos_usados=termos, correcoes=correcoes)
        resultado.emergencia = bool(set(normal.split()) & PALAVRAS_EMERGENCIA)
        if not termos:
            return resultado

        # Denominador: a nota máxima possível se todas as palavras casassem
        # com palavras-chave. Palavras desconhecidas também contam, para que
        # uma pergunta fora do tema não pareça bem respondida.
        maximo = sum(self.idf.get(t, self.idf_medio) * PESO_MAXIMO for t in termos)
        acumulado, maior_peso = {}, {}
        for termo in termos:
            for rid, peso in self.indice.get(termo, {}).items():
                acumulado[rid] = acumulado.get(rid, 0.0) + self.idf[termo] * peso
                maior_peso[rid] = max(maior_peso.get(rid, 0.0), peso)

        texto = f" {normal} "
        notas = []
        for rid, soma in acumulado.items():
            if maior_peso[rid] < EVIDENCIA_MINIMA:
                continue
            nota = soma / maximo
            if any(f" {frase} " in texto for frase in self.frases[rid]):
                nota += BONUS_FRASE
            notas.append(Candidato(rid, round(min(nota, 1.0), 4)))

        # Heap: pega só as k melhores sem ordenar tudo (O(n log k)).
        melhores = heapq.nlargest(k, notas, key=lambda c: c.pontuacao)
        # Empate de nota: ordem do identificador, para o resultado ser estável.
        resultado.candidatos = sorted(melhores, key=lambda c: (-c.pontuacao, c.id))
        return resultado

    def sugerir_palavras(self, pergunta: str, limite: int = 4) -> list:
        """Sugestões pela trie a partir do início de cada palavra digitada."""
        sugestoes = []
        for palavra in tokenizar(pergunta):
            for termo in self.trie.com_prefixo(palavra[:4], limite):
                if termo not in sugestoes:
                    sugestoes.append(termo)
        return sugestoes[:limite]
