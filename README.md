# Pull, otimização e avaliação de prompts com LangChain e LangSmith

## Técnicas Aplicadas (Fase 2)

O prompt otimizado está em `prompts/bug_to_user_story_v2.yml`. O v1 pedia uma user story em uma frase vaga, repetia `{bug_report}` no system e no user e não definia persona, formato nem exemplos. A v2 separa system e user: a variável `{bug_report}` fica só no user prompt.

### Few-shot Learning

Escolhi Few-shot porque a saída esperada muda com a complexidade do bug. Um bug de painel pede história e critérios curtos; um bug com log e endpoint pede contexto técnico; um bug com cálculo pede a conta; um bug com várias falhas pede seções, tasks e impacto. Quatro exemplos sintéticos, que não copiam o dataset, mostram entrada e saída nesse formato.

Exemplo prático: o exemplo médio recebe um timeout em `GET /api/contacts/export` e devolve a user story, critérios Given-When-Then e um bloco "Contexto Técnico" só com endpoint, status, log e causa que já estavam no relato.

### Role Prompting

Escolhi Role Prompting porque o v1 se apresentava como "um assistente" e o texto saía genérico. A v2 abre com "Você é um Product Manager sênior e analista ágil", pede tom profissional e empático e exige persona específica (cliente, administrador, analista de compras), em vez de "usuário" quando o relato indica o papel.

Exemplo prático: no exemplo simples, a persona da saída é "administrador no painel de chamados", não um usuário genérico.

### Chain of Thought

Escolhi Chain of Thought porque converter um bug complexo exige separar persona, fatos, problemas e complexidade antes de escrever. O modelo segue seis passos internos (persona, fatos, problemas, complexidade, formato, revisão) e a resposta visível traz só a User Story. O raciocínio não entra no texto final, para não divergir da referência avaliada.

Exemplo prático: a regra de complexidade manda usar contexto técnico só quando há endpoint, log, cálculo ou impacto medido, e o formato com `===` só quando há dois ou mais problemas.

Regras que acompanham as três técnicas: não inventar stack, número ou impacto; preservar literalmente códigos, paths e logs; cobrir todos os problemas do relato; tratar segurança, performance e cálculo como edge cases.

## Como Executar

### Pré-requisitos

- Python 3.10+
- Conta no LangSmith com handle público já criado (`USERNAME_LANGSMITH_HUB`)
- `LANGSMITH_API_KEY`
- `OPENAI_API_KEY`
- Modelos que aceitem `temperature=0`. O `src/evaluate.py` sempre envia temperatura 0; um modelo de raciocínio que recuse esse parâmetro interrompe a avaliação.

### Configuração

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

No `.env`:

- `LANGSMITH_API_KEY` — chave do LangSmith
- `LANGSMITH_PROJECT=mba-ia-pull-evaluation-prompt`
- `USERNAME_LANGSMITH_HUB` — handle público do Hub
- `OPENAI_API_KEY` — chave da OpenAI
- `LLM_PROVIDER=openai`
- `LLM_MODEL=gpt-4o-mini` — gera a user story
- `EVAL_MODEL=gpt-4o` — julga as respostas

### Fases

Na raiz do repositório, com o virtualenv ativo:

```bash
python src/pull_prompts.py
pytest tests/test_prompts.py
python src/push_prompts.py
python src/evaluate.py
```

1. O pull grava `prompts/bug_to_user_story_v1.yml` a partir de `leonanluppi/bug_to_user_story_v1`.
2. A otimização já está em `prompts/bug_to_user_story_v2.yml`.
3. O push publica `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` como prompt público, com descrição e tags.
4. A avaliação cria o dataset `{LANGSMITH_PROJECT}-eval`, roda os 15 bugs e imprime as cinco métricas e o link do experimento.

O critério de aprovação é cada métrica em 0.8 ou mais: Helpfulness, Correctness, F1-Score, Clarity e Precision.

## Resultados Finais

Avaliação aprovada com `gpt-4o-mini` gerando a user story e `gpt-4o` julgando. As notas abaixo são a média dos 15 exemplos.

| Métrica     | Nota |
| ----------- | ---- |
| Helpfulness | 0.91 |
| Correctness | 0.88 |
| F1-Score    | 0.85 |
| Clarity     | 0.91 |
| Precision   | 0.91 |
| Média geral | 0.89 |

Dataset público, com os experimentos: [mba-ia-pull-evaluation-prompt-eval](https://smith.langchain.com/public/01daffda-39c7-4fb4-919a-405a0c44ea92/d)

Experimento no workspace: [renanholler-bug_to_user_story_v2-8661c1a9](https://smith.langchain.com/o/2f954f55-8c4b-464c-b82a-6183d669512e/datasets/03bc333e-5ba2-4003-937e-d6eae7ed4d92/compare?selectedSessions=451c9df5-1af2-4580-8f65-5bf59f36108e)

Tracing público de três exemplos:

- [Exemplo 1](https://smith.langchain.com/public/441f4e67-c98f-4ec8-9a51-5eec9e6981dc/r/01a13a39-e2d0-76e3-bcd2-0bcbf89a4f95?start_time=2026-10-14T11%3A43%3A54.57676Z)
- [Exemplo 2](https://smith.langchain.com/public/19d8bbdf-7253-44bc-be56-637ea9db14d9/r/01a13a3a-1c15-79c1-a8e4-c536f1f0496a?start_time=2026-10-14T11%3A44%3A09.237137Z)
- [Exemplo 3](https://smith.langchain.com/public/ede3e5b7-4191-488b-926e-1da5ac4a9833/r/01a13a39-6eec-7751-b29e-8d17782aaf96?start_time=2026-10-14T11%3A43%3A24.908097Z)

As três rodadas no dataset. A terceira, `renanholler-bug_to_user_story_v2-8661c1a9`, é a aprovada: clarity 0.91, correctness 0.88, f1_score 0.85, helpfulness 0.91, precision 0.91.

![Médias das três rodadas no LangSmith](docs/evidencias/evidencia-1.png)

Os 15 exemplos da rodada aprovada, com as notas de cada um.

![Notas por exemplo na rodada aprovada](docs/evidencias/evidencia-2.png)

### O que mudou do v1 para o v2

O v1 se apresentava como assistente, repetia o relato no system e no user e pedia uma user story sem formato, persona nem exemplo. A saída ficava curta e genérica.

A v2 separa system e user, deixa `{bug_report}` só no user e define persona, formato e exemplos. O raciocínio fica interno. A resposta visível é a User Story.

Foram três rodadas. Na primeira, F1 ficou em 0.74 e Correctness em 0.79: a história cobria pouco do que a referência espera. Na segunda, a média não mudou, porque o prompt passou a repetir o número do bug (contagem errada, id do produto, tempo do timeout) e o juiz tratou isso como detalhe fora do critério. Na terceira, o critério descreve o comportamento corrigido: persona do papel certo, meta de tempo melhor que a falha, e complementos como confirmação, auditoria e reserva de estoque. As cinco médias ficaram em 0.8 ou mais.
