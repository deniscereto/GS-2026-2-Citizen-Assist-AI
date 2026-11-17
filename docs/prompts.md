# Modelos de prompt e de instrução de resposta

O Citizen Assist AI não usa um modelo de linguagem externo (o enunciado não exige e,
assim, a resposta nunca pode inventar conteúdo). Cada **modelo de prompt** é uma
instrução de resposta documentada que o programa aplica sobre a orientação
encontrada na base verificada. O código está em `src/respostas.py`.

Os dois textos abaixo também podem ser usados como *prompt de sistema* caso um
modelo de linguagem seja conectado no futuro. Nesse caso, a resposta do modelo
teria de ser conferida com a base verificada antes de ser exibida (ver
`docs/uso_ia.md`).

## Modelo A — Direto

```text
Responda à pergunta do cidadão usando a orientação encontrada na base e informe
o link da fonte.
```

**Exemplo** (pergunta: "fui demitido sem justa causa"):

```text
O seguro-desemprego é para quem foi dispensado sem justa causa e pode ser
pedido pelo aplicativo Carteira de Trabalho Digital. Tem direito quem foi
dispensado sem justa causa e cumpre o tempo mínimo de salários. Na primeira
solicitação, são 12 meses nos últimos 18. Canais: aplicativo Carteira de
Trabalho Digital, portal gov.br, telefone 158 ou atendimento presencial com
agendamento. (...)
Fonte: https://www.gov.br/pt-br/servicos/solicitar-o-seguro-desemprego
```

Sem resposta: `Não encontrei uma resposta para essa pergunta.`

## Modelo B — Estruturado

```text
Papel: você é um assistente de orientação cidadã NÃO OFICIAL.
Regras:
1. Use somente a orientação encontrada na base verificada; não invente passos.
2. Formato: título; resumo em uma frase; até 5 tópicos curtos; fonte com órgão,
   link e data de verificação.
3. Linguagem simples, frases curtas, sem termos técnicos sem explicação.
4. Se a orientação exigir confirmação, mostre o aviso.
5. Se não houver orientação suficiente, diga isso claramente e sugira temas próximos.
6. Nunca peça dados pessoais e não se apresente como canal de órgão público.
```

**Exemplo** (mesma pergunta):

```text
SEGURO-DESEMPREGO
Tema: Serviços públicos

O seguro-desemprego é para quem foi dispensado sem justa causa e pode ser
pedido pelo aplicativo Carteira de Trabalho Digital.

  - Tem direito quem foi dispensado sem justa causa e cumpre o tempo mínimo de
    salários. Na primeira solicitação, são 12 meses nos últimos 18.
  - Canais: aplicativo Carteira de Trabalho Digital, portal gov.br, telefone
    158 ou atendimento presencial com agendamento.
  - (...)

Fonte: Solicitar o Seguro-Desemprego (Governo Federal / gov.br)
Link: https://www.gov.br/pt-br/servicos/solicitar-o-seguro-desemprego
Informação conferida em 17/11/2026.
Confirme antes de agir: Regras de prazo e número de parcelas dependem do seu
caso. Confirme no serviço oficial.
```

Sem resposta:

```text
Não encontrei uma orientação confiável para essa pergunta na base. Para não
passar uma informação errada, prefiro não responder.
Você também pode escolher um tema no menu principal ou procurar o site oficial
do órgão responsável.
```

## Comparação nas perguntas de teste

O script `src/avaliacao.py` aplica os dois modelos a todas as perguntas de teste
respondidas (17) e às perguntas sem resposta (3), e verifica critérios objetivos.
Os números abaixo são da última execução (`docs/resultados_avaliacao.md`).

| Critério | Modelo A | Modelo B |
|---|---|---|
| Cita o link da fonte | 100% | 100% |
| Cita o órgão da fonte | 0% | 100% |
| Mostra a data de verificação | 0% | 100% |
| Mostra o aviso quando a orientação exige confirmação | 47,1% | 100% |
| Organizado em tópicos | 0% | 100% |
| **Média do checklist** | **29,4%** | **100%** |
| Palavras por frase | 12,4 | 10,1 |
| Índice de legibilidade Flesch-PT | 60,3 | 59,4 |
| Sem resposta: explica o limite | 0% | 100% |
| Sem resposta: indica outro caminho | 0% | 100% |

## Conclusão: o Modelo B é o padrão

- **Mais consistente:** todas as respostas do Modelo B seguem o mesmo formato e
  trazem órgão, link e data. No Modelo A, a pessoa não sabe quando a informação
  foi conferida nem de qual órgão ela vem.
- **Mais seguro:** o Modelo B mostra o aviso de confirmação em 100% das orientações
  que exigem confirmação. O Modelo A omite o aviso (os 47,1% correspondem só às
  orientações que não precisam dele).
- **Mais fácil de ler na tela:** com tópicos, a frase média cai de 12,4 para 10,1
  palavras.
- **Limite honesto:** o índice Flesch ficou praticamente igual (60,3 e 59,4, faixa
  "fácil"), porque o vocabulário vem da mesma base. A vantagem do Modelo B está na
  organização e na transparência, não em palavras mais simples.

O Modelo A continua disponível no menu (opção 4) para quem prefere uma resposta
corrida, mais curta.
