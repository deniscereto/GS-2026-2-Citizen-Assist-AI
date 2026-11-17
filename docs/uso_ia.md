# Uso de inteligência artificial no desenvolvimento

O enunciado permite usar ferramentas de IA para apoiar o desenvolvimento, desde que a
solução seja compreendida, testada e justificada por quem a entrega. Este projeto é
individual, e o autor é responsável por todo o conteúdo. Este arquivo registra como a IA foi
usada e como as saídas dela foram validadas.

## 1. A IA não responde ao cidadão

O protótipo **não chama nenhum modelo de linguagem** durante o uso. Toda resposta
mostrada ao usuário vem da base `data/base_conhecimento.json`, com fonte e data de
verificação. Os "prompts" do projeto (`docs/prompts.md`) são instruções de resposta
aplicadas por código. Por isso o assistente não tem como inventar uma orientação.

## 2. Onde a IA generativa foi usada como apoio

Ferramenta: assistente de IA generativa (Claude, da Anthropic), usado durante o
desenvolvimento.

| Etapa | Como a IA ajudou | Como foi validado |
|---|---|---|
| Pesquisa das orientações | Localizar páginas oficiais e resumir o conteúdo de cada uma | Cada orientação foi conferida na página oficial citada, e o link e a data de verificação foram registrados no próprio registro |
| Estrutura do código | Sugerir a divisão em módulos e revisar trechos | Código executado, lido módulo a módulo e coberto por 22 testes automatizados (`python -m pytest`) |
| Estratégia de busca | Discutir alternativas (palavras-chave, pesos, limiar) | Avaliação com 24 perguntas de teste e 12 de validação; os erros foram mantidos no relatório |
| Casos-limite | Sugerir situações difíceis (entrada vazia, ambígua, dados pessoais, emergência) | Viraram perguntas de teste e testes unitários |
| Textos | Revisar clareza e linguagem simples da documentação e do roteiro do vídeo | Revisão final pelo autor |

## 3. Validação crítica: o que foi conferido e corrigido

- **Fontes:** nenhuma orientação entrou na base sem uma página oficial (gov.br, TSE,
  INSS, Procon, Defensoria Pública, Consumidor.gov.br, portal oficial do Registro
  Civil). Quando a página não confirmava um detalhe, ele ficou de fora. Exemplo: a
  página de emergências do Ministério das Comunicações não diz se as ligações são
  gratuitas, então essa afirmação não aparece na base.
- **Informação que muda:** orientações com valores ou regras que variam por estado
  ou mudam com o tempo têm `requer_confirmacao: true` e um aviso explícito.
- **Avaliação sem autoengano:** os parâmetros da busca foram ajustados com as
  perguntas de teste. Para medir o desempenho real, um segundo conjunto de perguntas
  (validação) foi escrito **depois** do ajuste e não foi usado para calibrar nada.
  Nele o acerto foi de 75%, contra 100% no teste. Os dois números estão no README.
- **Limitações registradas:** casos em que o assistente erra (ex.: "receita de bolo"
  confundida com "Receita Federal") estão documentados no README em vez de escondidos.

## 4. Responsabilidade

Todo o código entregue foi executado e testado antes de cada commit, e o autor é
capaz de explicar cada módulo, a estratégia de busca e as métricas de avaliação.
