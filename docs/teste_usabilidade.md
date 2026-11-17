# Teste de facilidade de uso

O teste de facilidade de uso tem três partes:

1. **Roteiro de tarefas automatizado**: o script `src/avaliacao.py` simula uma pessoa
   usando o menu e confere se cada tarefa termina com a informação certa. O resultado
   fica em `docs/resultados/roteiro_usabilidade.csv` e no relatório
   `docs/resultados_avaliacao.md`.
2. **Avaliação por percurso cognitivo**: o autor percorre as mesmas tarefas no lugar de
   um usuário típico e registra as dificuldades previstas (seção 3).
3. **Teste com usuário real**: as mesmas tarefas feitas por uma pessoa que não
   participou do desenvolvimento (seção 4).

## 1. Roteiro de tarefas

| Tarefa | O que a pessoa precisa fazer | Sucesso quando |
|---|---|---|
| T1 | Descobrir o telefone do INSS fazendo uma pergunta | A resposta mostra a Central 135 |
| T2 | Achar o direito de arrependimento navegando pelos temas (sem digitar pergunta) | Chega à orientação dos 7 dias |
| T3 | A partir de uma resposta, abrir um assunto relacionado | Abre outra orientação pela lista "Assuntos relacionados" |
| T4 | Fazer uma pergunta fora do tema (ex.: passaporte) e explicar o que o assistente disse | A pessoa entende que não há resposta na base |
| T5 | Perguntar só "carteira" e chegar à Carteira de Trabalho Digital | Escolhe a opção certa na lista |
| T6 | Trocar a resposta para o formato curto | O menu mostra "Modelo A - Direto" |

## 2. Resultado do roteiro automatizado

Na última execução, as 6 tarefas foram concluídas, sem nenhuma mensagem de "opção inválida".
O número de passos (entradas digitadas) foi de 1 a 4 por tarefa, com média de 2,7.
Esse teste mostra que o caminho de cada tarefa funciona. Ele **não** mede se uma
pessoa encontra esse caminho sozinha; por isso foi feita a avaliação da seção 3.

## 3. Avaliação por percurso cognitivo

Além do roteiro automatizado, as 6 tarefas foram percorridas pelo autor no papel de um
**usuário típico**. O percurso cognitivo (*cognitive walkthrough*) é um método de
avaliação de usabilidade em que, a cada passo, o avaliador se pergunta: a pessoa sabe
o que fazer? Ela encontra a opção certa? Ela entende a resposta?

> Esta seção **não** é um teste com usuário real. Ela registra a análise do autor e as
> dificuldades previstas. Os tempos não foram medidos porque não houve participante.

**Perfil considerado:** adulto que usa o celular no dia a dia, tem pouca prática com
computador e nunca usou um terminal.

| Tarefa | Passos | Conclui sem ajuda? | Dificuldade prevista |
|---|---|---|---|
| T1 — telefone do INSS | 2 | Sim | Nenhuma relevante: "1. Fazer uma pergunta" é a primeira opção e o exemplo mostra como escrever |
| T2 — arrependimento pelos temas | 4 | Provavelmente | A pessoa precisa saber que "arrependimento" fica em "Direitos do consumidor"; quem não conhece o termo pode abrir outro tema antes |
| T3 — assunto relacionado | 3 | Sim | A resposta é longa e a lista de assuntos relacionados aparece no fim; em tela pequena, a pessoa pode não perceber a lista sem rolar |
| T4 — pergunta fora do tema | 3 | Sim | A mensagem é clara; a pergunta "(s/n)" pode gerar dúvida em quem não está acostumado a responder com uma letra |
| T5 — pergunta ambígua | 3 | Sim | As opções são numeradas e têm nomes claros |
| T6 — formato curto | 1 | Com hesitação | O menu fala em "Modelo A - Direto" e "Modelo B - Estruturado", termos técnicos que não dizem nada ao cidadão |

**Resumo:** 4 das 6 tarefas devem ser concluídas sem dificuldade, T2 depende de a pessoa
conhecer o assunto e T6 tem um problema de linguagem no menu.

**Ajustes identificados:**

1. Trocar "Modelo A / Modelo B" no menu por **"Resposta curta / Resposta detalhada"**.
2. Repetir no fim de cada resposta a instrução "digite o número de um assunto ou 0 para
   voltar", para quem não notar a lista de assuntos relacionados.
3. No menu de temas, mostrar exemplos de assuntos ao lado de cada tema (ex.: "Direitos
   do consumidor: compras, defeitos, reclamações").

## 4. Teste com usuário real

**Participante:** pessoa de cerca de 60 anos que usa o notebook todos os dias no
trabalho. Ela trabalha na área de TI, mas não é desenvolvedora e não tem familiaridade
com programação nem com o uso de terminal. Não participou do desenvolvimento.

**Como foi aplicado:** o autor explicou rapidamente como funciona o menu (digitar o
número da opção e Enter). Depois disso, o participante fez as 6 tarefas sozinho, sem
indicação de qual opção escolher.

| Tarefa | Concluiu sozinho? | Tempo aproximado | Dificuldade observada |
|---|---|---|---|
| T1 — telefone do INSS | Sim | 10 a 20 s | Nenhuma |
| T2 — arrependimento pelos temas | Sim | 10 a 20 s | Nenhuma |
| T3 — assunto relacionado | Sim | 10 a 20 s | Nenhuma |
| T4 — pergunta fora do tema | Sim | 10 a 20 s | Nenhuma |
| T5 — pergunta ambígua | Sim | 10 a 20 s | Nenhuma |
| T6 — formato curto | Sim | 10 a 20 s | Nenhuma |

**Nota de facilidade de uso:** 5 de 5.

**Indicadores:** taxa de conclusão sem ajuda = 6 de 6 (100%); tempo de 10 a 20 segundos
por tarefa. O tempo foi estimado pelo autor, sem cronômetro tarefa a tarefa.

**Interpretação:**

- O teste confirma que o fluxo do menu é fácil de seguir: todas as tarefas foram
  concluídas sem ajuda, e a hesitação prevista na T6 ("Modelo A / Modelo B") não apareceu.
- O participante não programa e não tinha usado um terminal, o que indica que a
  interface de texto não exige conhecimento técnico depois de uma explicação curta.
- **Limitações do teste:** foi um único participante, acostumado a usar computador no
  trabalho, e houve uma explicação breve antes de começar. Por isso o resultado não mostra como seria
  o primeiro uso de alguém com pouca prática, que é o perfil considerado na seção 3.
- Os ajustes da seção 3 continuam válidos para esse público menos experiente, e o
  próximo teste deve incluir pelo menos uma pessoa com esse perfil, sem explicação prévia.
