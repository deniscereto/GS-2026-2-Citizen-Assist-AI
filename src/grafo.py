"""Organização dos assuntos: hierarquia de temas e grafo de assuntos relacionados.

1) Hierarquia (árvore): tema -> subtema -> orientação. É usada no menu.
2) Grafo não direcionado: cada orientação é um vértice, e o campo
   "relacionados" da base cria as arestas (ex.: CIN -- CPF). A navegação
   "continue a consulta" usa busca em largura (BFS) para sugerir primeiro os
   assuntos mais próximos (distância 1) e depois os de distância 2.
"""

from collections import deque


def montar_hierarquia(base) -> dict:
    """Retorna {tema: {subtema: [ids]}} respeitando a ordem da base."""
    arvore = {}
    for tema in base.temas_disponiveis():
        arvore[tema] = {}
        for subtema in base.temas[tema]["subtemas"]:
            ids = [r["id"] for r in base.registros_do_subtema(tema, subtema)]
            if ids:
                arvore[tema][subtema] = ids
    return arvore


class GrafoAssuntos:
    """Grafo representado por lista de adjacência (dicionário id -> conjunto)."""

    def __init__(self, base):
        self.adjacencia = {r["id"]: set() for r in base.registros}
        for registro in base.registros:
            for vizinho in registro["relacionados"]:
                # Aresta nos dois sentidos: se A lembra B, B lembra A.
                self.adjacencia[registro["id"]].add(vizinho)
                self.adjacencia[vizinho].add(registro["id"])

    def vizinhos(self, rid: str) -> list:
        return sorted(self.adjacencia.get(rid, ()))

    def relacionados_bfs(self, origem: str, limite: int = 3, profundidade_max: int = 2) -> list:
        """Lista de (id, distância) em ordem de proximidade, sem a origem."""
        if origem not in self.adjacencia:
            return []
        visitados = {origem}
        fila = deque([(origem, 0)])
        resultado = []
        while fila and len(resultado) < limite:
            atual, distancia = fila.popleft()
            if distancia == profundidade_max:
                continue
            for vizinho in sorted(self.adjacencia[atual]):
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    resultado.append((vizinho, distancia + 1))
                    fila.append((vizinho, distancia + 1))
                    if len(resultado) == limite:
                        break
        return resultado

    def numero_arestas(self) -> int:
        return sum(len(v) for v in self.adjacencia.values()) // 2
