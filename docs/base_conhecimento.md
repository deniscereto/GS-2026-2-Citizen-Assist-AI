# Base de conhecimento: organização e fontes

Arquivo: `data/base_conhecimento.json` (JSON, UTF-8). Sinônimos: `data/sinonimos.json`.

## Campos de cada orientação

| Campo | Obrigatório | Para que serve |
|---|---|---|
| `id` | sim | Identificador único (DOC01, SER02...). Usado no dicionário de acesso rápido |
| `tema` / `subtema` | sim | Posição na hierarquia de assuntos |
| `titulo` | sim | Nome mostrado nos menus e no topo da resposta |
| `perguntas` | sim | Exemplos de como as pessoas perguntam (ajudam a busca) |
| `palavras_chave` | sim | Termos principais do assunto (maior peso na busca) |
| `resumo` | sim | Orientação em uma frase |
| `orientacao` | sim | Lista de tópicos curtos com a orientação resumida |
| `referencia` | sim | `titulo`, `orgao` e `url` da fonte consultada |
| `data_verificacao` | sim | Data em que a fonte foi conferida (AAAA-MM-DD) |
| `requer_confirmacao` | não | `true` quando valores ou regras variam por estado ou mudam com o tempo |
| `aviso` | se `requer_confirmacao` | O que a pessoa deve confirmar antes de agir |
| `relacionados` | não | Ids de assuntos ligados (arestas do grafo de navegação) |

Ao iniciar, o programa valida todos os campos. Um registro com campo ausente, URL sem
`http`, data fora do formato, tema ou subtema desconhecido ou id repetido é **ignorado
com um aviso**, e os demais continuam funcionando. Arquivo ausente, vazio ou com JSON
inválido gera uma mensagem clara e o programa encerra sem travar.

**Para acrescentar uma orientação**, basta incluir um novo objeto em `registros`,
seguindo os campos acima. Nenhuma linha de código precisa mudar: o índice de busca, a
trie, a hierarquia e o grafo são montados a partir do arquivo a cada execução.

## Temas e orientações (18 registros, 4 temas, 11 subtemas)

| Id | Tema > subtema | Orientação | Fonte |
|---|---|---|---|
| DOC01 | Documentos > Identificação civil | Carteira de Identidade Nacional (CIN) | [Governo Digital](https://www.gov.br/governodigital/pt-br/identidade/cin) |
| DOC02 | Documentos > Identificação civil | Consulta da situação do CPF | [gov.br / Receita Federal](https://www.gov.br/pt-br/servicos/consultar-cadastro-de-pessoas-fisicas) |
| DOC03 | Documentos > Documento eleitoral | Título de eleitor digital (e-Título) | [TSE](https://www.tse.jus.br/eleitor/servicos/aplicativo-e-titulo-1) |
| DOC04 | Documentos > Documento de trabalho | Carteira de Trabalho Digital | [Ministério do Trabalho e Emprego](https://www.gov.br/trabalho-e-emprego/pt-br/servicos/trabalhador/carteira-de-trabalho/perguntas-frequentes-carteira-de-trabalho-digital) |
| DOC05 | Documentos > Identificação civil | Segunda via de certidão | [Portal oficial do Registro Civil](https://blog.registrocivil.org.br/como-pedir-a-segunda-via-da-sua-certidao-online/) |
| SER01 | Serviços > Acesso digital | Níveis da conta gov.br | [Governo Digital](https://www.gov.br/governodigital/pt-br/identidade/conta-gov-br/niveis-da-conta-govbr) |
| SER02 | Serviços > Trabalho e renda | Seguro-desemprego | [gov.br](https://www.gov.br/pt-br/servicos/solicitar-o-seguro-desemprego) |
| SER03 | Serviços > Trabalho e renda | Inscrição no Cadastro Único | [gov.br / MDS](https://www.gov.br/pt-br/servicos/inscrever-se-no-cadastro-unico-para-programas-sociais-do-governo-federal) |
| SER04 | Serviços > Previdência | Atendimento do INSS (Meu INSS e 135) | [INSS](https://www.gov.br/inss/pt-br/canais_atendimento/central-135) |
| SER05 | Serviços > Saúde | Cartão do SUS com o CPF | [Agência Gov / Ministério da Saúde](https://agenciagov.ebc.com.br/noticias/202509/ministerio-da-saude-comeca-a-emitir-cartao-sus-com-base-no-cpf) |
| DIR01 | Direitos > Consumidor | Direito de arrependimento | [Ministério da Justiça](https://www.gov.br/mj/pt-br/assuntos/noticias/consumidor-tem-direito-ao-arrependimento-em-compras-on-line) |
| DIR02 | Direitos > Consumidor | Prazos para reclamar de defeito | [Procon-PR](https://www.procon.pr.gov.br/Pagina/Dicas-e-Direitos-Prazos-para-Reclamacao) |
| DIR03 | Direitos > Consumidor | Reclamação no Consumidor.gov.br | [Senacon](https://www.consumidor.gov.br/pages/conteudo/publico/1) |
| DIR04 | Direitos > Assistência jurídica | Defensoria Pública | [Defensoria Pública de SP](https://www.defensoria.sp.def.br/atendimento/duvidas-frequentes) |
| COM01 | Comunidade > Emergências | Telefones de emergência | [Ministério das Comunicações](https://www.gov.br/mcom/pt-br/noticias/2026/setembro/emergencia-voce-sabe-para-quem-ligar-quando-precisa-de-ajuda) |
| COM02 | Comunidade > Emergências | Defesa Civil (199) | [Ministério das Comunicações](https://www.gov.br/mcom/pt-br/noticias/2026/setembro/emergencia-voce-sabe-para-quem-ligar-quando-precisa-de-ajuda) |
| COM03 | Comunidade > Denúncia e proteção | Disque 100 | [Ministério dos Direitos Humanos](https://www.gov.br/mdh/pt-br/campanha/direitoshumanosparatodos/disque-100-e-ligue-180) |
| COM04 | Comunidade > Denúncia e proteção | Ligue 180 | [Ministério dos Direitos Humanos](https://www.gov.br/mdh/pt-br/campanha/direitoshumanosparatodos/disque-100-e-ligue-180) |

Todas as fontes foram conferidas em **17/11/2026**.

## Critérios de seleção

- Só entram orientações com página oficial identificável (órgão público, tribunal,
  Procon, Defensoria ou o portal oficial dos cartórios).
- O texto resume a página com palavras simples; detalhes que a página não confirma
  ficam de fora.
- Orientações que mudam por estado ou com o tempo (CIN, certidões, Defensoria,
  Cadastro Único, Cartão SUS, seguro-desemprego, prazos do consumidor) trazem aviso
  de confirmação.
