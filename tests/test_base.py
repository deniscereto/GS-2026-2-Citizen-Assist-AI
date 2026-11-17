"""Testes da leitura e validação da base de conhecimento."""

import json

import pytest

from base_conhecimento import ErroBase, carregar_base

TEMAS = {"documentos": {"nome": "Documentos", "subtemas": {"identificacao": "Identificação"}}}


def registro(rid="T01", **mudancas):
    base = {
        "id": rid, "tema": "documentos", "subtema": "identificacao",
        "titulo": "Teste", "perguntas": ["pergunta"], "palavras_chave": ["teste"],
        "resumo": "Resumo.", "orientacao": ["Item."],
        "referencia": {"titulo": "Fonte", "orgao": "Órgão", "url": "https://exemplo.gov.br"},
        "data_verificacao": "2026-11-17",
    }
    base.update(mudancas)
    return base


def salvar(tmp_path, conteudo):
    arquivo = tmp_path / "base.json"
    arquivo.write_text(conteudo if isinstance(conteudo, str) else json.dumps(conteudo),
                       encoding="utf-8")
    return arquivo


def test_base_real_carrega_sem_avisos(assistente):
    assert len(assistente.base.registros) >= 15
    assert len(assistente.base.temas_disponiveis()) >= 3
    assert assistente.base.avisos == []


def test_arquivo_ausente(tmp_path):
    with pytest.raises(ErroBase, match="não encontrado"):
        carregar_base(tmp_path / "nao_existe.json")


def test_arquivo_vazio(tmp_path):
    with pytest.raises(ErroBase, match="vazio"):
        carregar_base(salvar(tmp_path, ""))


def test_json_invalido(tmp_path):
    with pytest.raises(ErroBase, match="JSON válido"):
        carregar_base(salvar(tmp_path, "{ isso não é json"))


def test_registro_sem_campo_e_ignorado(tmp_path):
    sem_fonte = registro("T02")
    del sem_fonte["referencia"]
    base = carregar_base(salvar(tmp_path, {"temas": TEMAS, "registros": [registro(), sem_fonte]}))
    assert list(base.por_id) == ["T01"]
    assert "T02" in base.avisos[0] and "referencia" in base.avisos[0]


def test_url_e_data_invalidas_sao_rejeitadas(tmp_path):
    ruim = registro("T02", data_verificacao="17/11/2026",
                    referencia={"titulo": "x", "orgao": "y", "url": "site sem link"})
    base = carregar_base(salvar(tmp_path, {"temas": TEMAS, "registros": [registro(), ruim]}))
    assert "T02" not in base.por_id
    assert "URL" in base.avisos[0] and "data_verificacao" in base.avisos[0]


def test_id_repetido_e_relacionado_inexistente(tmp_path):
    dados = {"temas": TEMAS, "registros": [registro(relacionados=["X99"]), registro()]}
    base = carregar_base(salvar(tmp_path, dados))
    assert len(base.registros) == 1
    assert base.por_id["T01"]["relacionados"] == []
    assert any("repetido" in a for a in base.avisos)


def test_sem_registros_validos(tmp_path):
    with pytest.raises(ErroBase, match="Nenhum registro"):
        carregar_base(salvar(tmp_path, {"temas": TEMAS, "registros": [{"id": "x"}]}))
