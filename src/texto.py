"""Tratamento de texto: normalização, tokenização e detecção de dados pessoais.

A busca compara palavras. Para que "Certidões" e "certidao" sejam a mesma
palavra, todo texto (da base e da pergunta) passa pelas mesmas etapas:
minúsculas -> remoção de acentos -> remoção de pontuação -> tokens ->
remoção de palavras vazias (stopwords) -> redução simples de plural.
"""

import re
import unicodedata

# Palavras muito comuns que não ajudam a identificar o assunto da pergunta.
STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "da", "do", "das",
    "dos", "em", "na", "no", "nas", "nos", "por", "para", "pra", "pro", "com",
    "sem", "e", "ou", "que", "se", "me", "meu", "minha", "meus", "minhas", "eu",
    "voce", "ele", "ela", "isso", "esse", "essa", "este", "esta", "ao", "aos",
    "como", "onde", "qual", "quais", "quando", "quanto", "quem", "porque",
    "faco", "fazer", "faz", "tirar", "tiro", "quero", "queria", "preciso",
    "precisa", "posso", "pode", "consigo", "saber", "sobre", "ter", "tem",
    "tenho", "e", "ja", "agora", "algum", "alguma", "ser", "sou", "foi", "esta",
    "estou", "la", "aqui", "ai", "muito", "mais", "menos", "favor", "ola",
    "oi", "bom", "boa", "dia", "tarde", "noite", "obrigado", "obrigada", "ajuda",
    "duvida", "pelo", "pela", "pelos", "pelas", "num", "numa", "seu", "sua",
    "lhe", "nao", "sim", "depois", "antes", "entao", "ainda", "so", "deu",
    "outro", "outra", "hoje", "amanha", "ontem", "coisa", "algo", "gente",
}


def remover_acentos(texto: str) -> str:
    """Troca letras acentuadas pelas equivalentes sem acento (ç -> c, ã -> a)."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    """Deixa o texto em minúsculas, sem acentos e sem pontuação."""
    texto = remover_acentos(texto.lower())
    # Mantém letras, números e espaços; o resto vira espaço.
    texto = re.sub(r"[^a-z0-9 ]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def reduzir_plural(palavra: str) -> str:
    """Redução simples de plural para português (certidoes -> certidao)."""
    if len(palavra) <= 3 or palavra.isdigit():
        return palavra
    if palavra.endswith("oes") or palavra.endswith("aes"):
        return palavra[:-3] + "ao"
    if palavra.endswith("ais"):
        return palavra[:-2] + "l"
    if palavra.endswith("s"):
        return palavra[:-1]
    return palavra


def tokenizar(texto: str, remover_stopwords: bool = True) -> list:
    """Transforma um texto em lista de palavras normalizadas."""
    palavras = normalizar(texto).split()
    if remover_stopwords:
        palavras = [p for p in palavras if p not in STOPWORDS]
    return [reduzir_plural(p) for p in palavras]


# --- Privacidade -----------------------------------------------------------
# O assistente não precisa de dados pessoais. Se a pessoa digitar algum,
# ele é mascarado antes da busca e nunca é gravado.
PADROES_DADOS_PESSOAIS = {
    "CPF": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    "e-mail": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
    "telefone": re.compile(r"(?:\(?\b\d{2}\)?\s?)?\b9?\d{4}-?\d{4}\b"),
}


def mascarar_dados_pessoais(texto: str):
    """Retorna (texto_mascarado, lista_de_tipos_encontrados)."""
    encontrados = []
    for tipo, padrao in PADROES_DADOS_PESSOAIS.items():
        if padrao.search(texto):
            encontrados.append(tipo)
            texto = padrao.sub(" ", texto)
    return texto, encontrados
