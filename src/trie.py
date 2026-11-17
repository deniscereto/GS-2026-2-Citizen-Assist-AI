"""Trie (árvore de prefixos) com as palavras-chave da base.

Usada quando a pergunta não encontra resposta: a partir do início de cada
palavra digitada, o assistente sugere palavras-chave que existem na base
(ex.: "segu" -> "seguro desemprego"). A busca por prefixo custa O(m), em que
m é o tamanho do prefixo, independentemente de quantas palavras existem.
"""


class NoTrie:
    __slots__ = ("filhos", "termos")

    def __init__(self):
        self.filhos = {}
        self.termos = set()  # termos completos que passam por este nó


class Trie:
    def __init__(self):
        self.raiz = NoTrie()

    def inserir(self, palavra: str, termo: str) -> None:
        """Guarda 'termo' no caminho de 'palavra' (cada letra é um nó)."""
        no = self.raiz
        for letra in palavra:
            no = no.filhos.setdefault(letra, NoTrie())
            no.termos.add(termo)

    def com_prefixo(self, prefixo: str, limite: int = 5) -> list:
        no = self.raiz
        for letra in prefixo:
            if letra not in no.filhos:
                return []
            no = no.filhos[letra]
        return sorted(no.termos)[:limite]
