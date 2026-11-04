# 🎸 Empório da Música — Agente de Atendimento com IA

Projeto desenvolvido para o **Desafio Técnico de AI Engineer na Artefact**. Consiste em um agente de atendimento virtual inteligente para a **Empório da Música**, loja especializada em instrumentos musicais localizada em Campo Grande/MS.

O agente é capaz de responder dúvidas de clientes, consultar estoque e catálogo em tempo real, rastrear pedidos, aplicar políticas de trocas e devoluções (CDC) e redirecionar adequadamente perguntas fora de escopo (como pedidos de acessórios avulsos).

---

## 📋 Sumário
- [Arquitetura da Solução](#-arquitetura-da-solução)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Como Executar](#-como-executar)
  - [Interface de Linha de Comando (CLI)](#1-interface-de-linha-de-comando-cli)
  - [Interface Web (Streamlit)](#2-interface-web-streamlit)
  - [Testes Automatizados](#3-testes-automatizados)
- [Justificativas das Decisões Técnicas](#-justificativas-das-decisões-técnicas)
- [Limitações Conhecidas e Próximos Passos](#-limitações-conhecidas-e-próximos-passos)
- [Uso de Assistentes de Código](#-uso-de-assistentes-de-código)

---

## 🏛️ Arquitetura da Solução

A solução adota uma abordagem **Híbrida (Function Calling / ReAct + RAG + Banco Relacional)**:

```text
                               +----------------------------+
                               |     Mensagem do Cliente    |
                               +--------------+-------------+
                                              |
                                              v
                               +----------------------------+
                               |   EmporioAgent (Loop ReAct)|
                               |  - Persona Empório Música  |
                               |  - Gestão de Memória       |
                               +--------------+-------------+
                                              |
                       +----------------------+----------------------+
                       | Decide ferramenta com base no contexto      |
                       v                                             v
        +-----------------------------+               +-----------------------------+
        |  Dados Operacionais (DB)    |               |  Políticas da Loja (RAG)    |
        |  - search_catalog           |               |  - consult_store_policies   |
        |  - get_product_details      |               |  - get_store_info           |
        |  - check_order_status       |               +--------------+--------------+
        +--------------+--------------+                              |
                       |                                             v
                       v                              +-----------------------------+
        +-----------------------------+               | BM25 + Boosting Semântico   |
        | SQLite Indexado (CSVs)      |               | Manual de Políticas (.pdf)  |
        | - produtos, preços, estoque |               | - trocas, fretes, horários  |
        | - clientes, pedidos, itens  |               +-----------------------------+
        | - promoções ativas/inativas |
        +--------------+--------------+
                       |
                       +----------------------+
                                              |
                                              v
                               +----------------------------+
                               |  Síntese da Resposta Final |
                               |  - Tom amigável de música  |
                               |  - Fidedignidade factual   |
                               +----------------------------+
```

1. **Camada de Dados Operacionais (SQLite)**: As tabelas operacionais (`products.csv`, `orders.csv`, `order_items.csv`, `customers.csv`, `categories.csv`, `promotions.csv`) são ingeridas em um banco SQLite indexado. Consultas numéricas (ex.: violões até R$ 1.000,00) ou filtros de estoque utilizam SQL direto com tipagem Pydantic, garantindo 0% de alucinação em preços e quantidades.
2. **Camada de Políticas (RAG)**: O documento `políticas_da_loja.pdf` é extraído e particionado em seções semânticas oficiais, indexadas via algoritmo **BM25Okapi** com expansão de sinônimos e boosting por tags contextuais (devoluções, CDC, horários, parcelamento, frete para Campo Grande).
3. **Agente e Roteador de Ferramentas**: Identifica a intenção do usuário e orquestra a chamada de ferramentas tipadas, mantendo a persona e aplicando as regras de transparência (ex.: informar promoções expiradas e redirecionar consultas de acessórios).

---

## 📁 Estrutura do Repositório

O projeto segue as melhores práticas da comunidade Python moderna, com empacotamento gerenciado via `uv`:

```text
.
├── .env.example                     # Modelo de variáveis de ambiente
├── .gitignore                       # Ignora venvs, caches e bancos locais
├── pyproject.toml                   # Especificação do pacote e dependências (PEP 621)
├── README.md                        # Documentação técnica completa
├── data/                            # Dados fornecidos pela loja
│   ├── desafio_tecnico_ai_eng - *.csv
│   └── políticas_da_loja.pdf
├── examples/                        # Exemplos de conversas reais (.md)
│   ├── 01_catalog_budget_search.md
│   ├── 02_store_info_and_hours.md
│   ├── 03_price_and_specs_check.md
│   ├── 04_refund_policy_non_trivial.md
│   └── 05_out_of_scope_redirection.md
├── src/
│   └── emporio_agent/
│       ├── __init__.py
│       ├── config.py                # Configurações com Pydantic Settings
│       ├── cli.py                   # Interface de terminal interativa (Rich)
│       ├── ui.py                    # Interface Web com Streamlit
│       ├── db/
│       │   ├── schema.py            # Modelos Pydantic (Product, Order, Promo, etc.)
│       │   └── database.py          # Ingestão e consultas ao SQLite
│       ├── rag/
│       │   ├── parser.py            # Extração de PDF e segmentação de seções
│       │   └── retriever.py         # Recuperador BM25 com boosting semântico
│       ├── tools/
│       │   └── definitions.py       # Registro e schemas de Function Calling
│       └── agent/
│           ├── prompts.py           # Persona da Empório da Música e System Prompt
│           ├── memory.py            # Histórico de mensagens da sessão
│           ├── llm_client.py        # Suporte a Gemini, Groq, Ollama e Mock
│           └── core.py              # Ciclo autônomo ReAct do agente
└── tests/
    ├── test_database.py             # Testes unitários do banco e filtros de catálogo
    ├── test_rag.py                  # Testes do recuperador de políticas
    └── test_agent.py                # Testes end-to-end dos cenários do desafio
```

---

## ⚙️ Instalação e Configuração

O projeto utiliza o [`uv`](https://docs.astral.sh/uv/), o gerenciador de pacotes e ambientes virtuais ultrarrápido em Rust para Python.

### Pré-requisitos
- Python `>= 3.11`
- `uv` instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh` ou `brew install uv`)

### 1. Clonar e sincronizar dependências
```bash
# Sincroniza todas as dependências e o ambiente de desenvolvimento (.venv)
uv sync --extra dev
```

### 2. Configurar Variáveis de Ambiente
Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

Abra o arquivo `.env` e escolha o provedor desejado:

#### Opção A: Google Gemini (Recomendado — Camada Gratuita)
O Google AI Studio oferece cotas gratuitas para os modelos `gemini-1.5-flash` e `gemini-2.0-flash`.
1. Gere sua chave gratuita em [aistudio.google.com](https://aistudio.google.com/).
2. No `.env`:
   ```ini
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=sua_chave_aqui
   GEMINI_MODEL=gemini-1.5-flash
   ```

#### Opção B: Groq (Gratuito via API)
1. Gere sua chave gratuita em [console.groq.com](https://console.groq.com/).
2. No `.env`:
   ```ini
   LLM_PROVIDER=groq
   GROQ_API_KEY=sua_chave_aqui
   GROQ_MODEL=llama-3.3-70b-versatile
   ```

#### Opção C: Ollama (100% Local e Gratuito)
Execute localmente sem necessidade de chaves:
```ini
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

#### Opção D: Modo Mock Determinístico (Zero Configuração / Testes Offline)
Caso nenhuma chave seja informada, o sistema entra automaticamente no modo `mock`. Este modo executa todas as ferramentas, calcula estoque e preços reais e gera as respostas na persona da loja sem fazer chamadas externas à internet.

---

## 🚀 Como Executar

### 1. Interface de Linha de Comando (CLI)
Uma interface rica e interativa desenvolvida com [Rich]:
```bash
uv run emporio-agent
```
*Comandos disponíveis durante o chat:*
- `/debug`: Ativa/desativa a visualização em tempo real das ferramentas chamadas pelo agente.
- `/reset`: Reinicia a memória e o histórico da conversa.
- `/sair`: Encerra o atendimento.

### 2. Interface Web (Streamlit)
Uma interface visual completa com painel lateral de status e botões de atalho para perguntas rápidas:
```bash
uv run streamlit run src/emporio_agent/ui.py
```
Acesse no navegador: `http://localhost:8501`.

### 3. Testes Automatizados
O repositório conta com uma suíte de 15 testes unitários e de integração cobrindo banco de dados, motor RAG e os cenários do agente:
```bash
uv run pytest -v
```

---

## 🧠 Justificativas das Decisões Técnicas

| Decisão | Escolha | Justificativa |
|---|---|---|
| **Abordagem do Agente** | **Tool Calling / ReAct com Pydantic** | O atendimento a uma loja de instrumentos exige exatidão em preços, estoque e status de remessa. Um LLM puro alucina números e não tem acesso a dados em tempo real. Com Function Calling tipado via Pydantic, o modelo decide de forma autônoma *quando* consultar o banco relacional e *quando* recorrer ao manual de políticas. |
| **Camada de Dados Operacionais** | **SQLite Relacional em Memória/Disco** | CSVs planos não oferecem indexação eficiente nem operações relacionais (ex.: associar `order_items` com `products` e `promotions`). O SQLite é leve, não requer servidores externos, é reproduzível em qualquer máquina e permite consultas com filtros combinados (`preço <= 1000`, `categoria = Violões` e `estoque > 0`). |
| **Camada de Políticas (RAG)** | **Chunking Semântico + BM25Okapi** | O manual de atendimento é um documento regulatório estruturado em 10 seções (regras de CDC, fretes locais, garantias). O particionamento respeita as fronteiras lógicas dos tópicos, e o BM25 com boosting garante precisão léxica exata em prazos numéricos (ex.: "7 dias", "30 dias", "90 dias", "R$ 500,00"), superando modelos de embeddings puros que frequentemente confundem prazos diferentes. |
| **Modelos e Provedores** | **Agnóstico (Gemini / Groq / Ollama / Mock)** | Atendendo à preferência por modelos gratuitos, a camada de abstração em `llm_client.py` suporta a API gratuita do Google Gemini e do Groq, além de modelos locais via Ollama e um provedor Mock para CI/CD sem dependência de internet. |
| **Estratégia de Prompt & Persona** | **Persona Empática Musical com Guardrails** | A identidade da loja requer um atendente que pareça "um amigo que entende de música", sem ser frio ou excessivamente cerimonioso. O prompt orienta ativamente a honestidade em promoções expiradas e o redirecionamento cordial para parceiros quando o cliente busca acessórios (não vendidos pela loja). |

---

## ⚠️ Limitações Conhecidas e Próximos Passos

Caso houvesse mais tempo de desenvolvimento no projeto, as seguintes evoluções seriam priorizadas:

1. **Busca Híbrida Vetorial Densa (Dense + Sparse Retrieval)**:
   - Integrar embeddings densos (ex.: `text-embedding-3-small` ou `all-MiniLM-L6-v2`) combinados com Cross-Encoder Re-ranker para perguntas com vocabulário mais distante do manual.
2. **Integração Real com WhatsApp Business**:
   - Conectar o agente a um webhook oficial do WhatsApp Cloud API ou Evolution API, permitindo envio de mensagens de áudio (transcritas via Whisper) e imagens dos instrumentos.
3. **Persistência de Sessões em Cache Distribuído**:
   - Armazenar histórico de conversas e estado dos carrinhos em um Redis para suportar múltiplos usuários simultâneos com retenção entre dias.
4. **Framework de Avaliação Contínua (LLM-as-a-Judge)**:
   - Implementar pipeline com Ragas ou DeepEval para pontuar automaticamente métricas de fidelidade factual (*faithfulness*), precisão de recuperação (*context precision*) e aderência ao tom de voz (*tone adherence*).

---

## 🤖 Uso de Assistentes de Código

Em total conformidade com as diretrizes do processo seletivo da Artefact, este projeto foi desenvolvido com o auxílio do assistente de engenharia de software da plataforma (Antigravity):

- **Planejamento Arquitetural**: Estruturação inicial do plano de desenvolvimento em tarefas atômicas e definição da árvore de módulos.
- **Implementação e Pair Programming**: Escrita dos componentes de ingestão de dados, normalização de texto do PDF via `pypdf` e schemas de validação Pydantic.
- **Testes Unitários (TDD)**: Criação das fixtures do `pytest` e validação dos 5 cenários do desafio.
- **Transparência**: O assistente acelerou o ciclo de scaffolding e implementação, enquanto todas as decisões conceituais, lógica de negócio da Empório da Música e validação técnica foram rigorosamente guiadas pelos requisitos do desafio.
