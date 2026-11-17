"""Testes da busca, das regras de resposta e das estruturas de dados."""

from assistente import AMBIGUA, INVALIDA, RESPONDIDA, SEM_RESPOSTA
from texto import mascarar_dados_pessoais, normalizar, tokenizar
from trie import Trie


def test_normalizacao_e_plural():
    assert normalizar("Certidões, AÇÃO!") == "certidoes acao"
    assert tokenizar("As certidões de nascimento") == ["certidao", "nascimento"]


def test_pergunta_direta(assistente):
    consulta = assistente.consultar("Como pedir seguro-desemprego?")
    assert consulta.situacao == RESPONDIDA and consulta.ids == ["SER02"]


def test_sinonimo_do_dia_a_dia(assistente):
    consulta = assistente.consultar("me mandaram embora, tenho direito a algo?")
    assert consulta.ids == ["SER02"]


def test_erro_de_digitacao(assistente):
    consulta = assistente.consultar("seguro desenprego")
    assert consulta.ids == ["SER02"]
    assert any("desemprego" in a for a in consulta.avisos)


def test_entrada_vazia_e_simbolos(assistente):
    assert assistente.consultar("").situacao == INVALIDA
    assert assistente.consultar("   ").situacao == INVALIDA
    assert assistente.consultar("?!?!").situacao == INVALIDA
    assert assistente.consultar("x" * 400).situacao == INVALIDA


def test_fora_do_tema_nao_inventa(assistente):
    consulta = assistente.consultar("Como renovar o passaporte?")
    assert consulta.situacao == SEM_RESPOSTA
    assert "Não encontrei" in consulta.texto


def test_pergunta_ambigua_oferece_opcoes(assistente):
    consulta = assistente.consultar("carteira")
    assert consulta.situacao == AMBIGUA
    assert set(consulta.ids) == {"DOC01", "DOC04"}


def test_dados_pessoais_sao_mascarados(assistente):
    texto, tipos = mascarar_dados_pessoais("meu cpf é 123.456.789-09 e email a@b.com")
    assert "123" not in texto and "@" not in texto
    assert tipos == ["CPF", "e-mail"]
    consulta = assistente.consultar("Meu CPF é 123.456.789-09, ele está regular?")
    assert consulta.ids == ["DOC02"]
    assert any("dados pessoais" in a for a in consulta.avisos)


def test_aviso_de_emergencia(assistente):
    consulta = assistente.consultar("socorro, incêndio na cozinha")
    assert consulta.avisos and "190" in consulta.avisos[0]


def test_resposta_estruturada_tem_fonte_data_e_aviso(assistente):
    assistente.modelo = "B"
    texto = assistente.texto_orientacao("DOC01")
    assert "Link: https://" in texto
    assert "conferida em 17/11/2026" in texto
    assert "Confirme antes de agir" in texto


def test_grafo_e_simetrico_e_bfs_por_distancia(assistente):
    grafo = assistente.grafo
    for origem, vizinhos in grafo.adjacencia.items():
        for v in vizinhos:
            assert origem in grafo.adjacencia[v]
    resultado = grafo.relacionados_bfs("DIR01", limite=5)
    distancias = [d for _, d in resultado]
    assert distancias == sorted(distancias)          # mais próximos primeiro
    assert ("DIR02", 1) in resultado


def test_hierarquia_tem_todos_os_registros(assistente):
    ids = [rid for subtemas in assistente.hierarquia.values()
           for lista in subtemas.values() for rid in lista]
    assert sorted(ids) == sorted(assistente.base.por_id)


def test_trie_por_prefixo():
    trie = Trie()
    trie.inserir("seguro", "seguro desemprego")
    trie.inserir("segunda", "segunda via")
    assert trie.com_prefixo("segu") == ["segunda via", "seguro desemprego"]
    assert trie.com_prefixo("xyz") == []


def test_ranking_em_ordem_decrescente(assistente):
    candidatos = assistente.busca.buscar("certidão de nascimento segunda via").candidatos
    notas = [c.pontuacao for c in candidatos]
    assert notas == sorted(notas, reverse=True)
    assert candidatos[0].id == "DOC05"
