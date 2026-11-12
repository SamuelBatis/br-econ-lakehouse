# br-econ-lakehouse

Pipeline de dados de indicadores econômicos brasileiros (Banco Central / IBGE), construído
em fases: ingestão → dbt → Airflow → Spark/Delta → Azure. Projeto de portfólio de Data Engineering.

## Stack
- Python 3.12, gerenciado com `uv` (nunca usar pip diretamente)
- Testes: `pytest`
- Lint/format: `ruff`
- Containers: Docker

## Comandos
- Instalar/sincronizar: `uv sync`
- Testes: `uv run pytest -v`
- Lint: `uv run ruff check . && uv run ruff format --check .`
- Adicionar dependência: `uv add <pacote>` (dev: `uv add --dev <pacote>`)

## Estrutura (src layout)
```
src/br_econ_lakehouse/
  ingestion/
    windows.py   # fatiamento de períodos (função pura)
    client.py    # HTTP para a API SGS + retry
    models.py    # parse e validação dos registros
    state.py     # watermark por série
    writer.py    # escrita na camada bronze
    run.py       # CLI
tests/           # espelha a estrutura de src/
config/          # configuração (YAML), sem segredos
data/            # saída local (no .gitignore)
```

## Fatos da fonte (API SGS do Banco Central)
- Endpoint: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial=dd/MM/aaaa&dataFinal=dd/MM/aaaa`
- Janela maior que 10 anos ou sem datas em série diária → HTTP 406. Sempre fatiar o período.
- `data` e `valor` vêm como TEXTO: data `dd/MM/aaaa`, valor com ponto decimal.
- Séries diárias de mercado (ex.: código 1, dólar) só têm dias úteis: buracos são esperados.
- Séries mensais (ex.: 433, IPCA) usam `01/MM/aaaa` como mês de referência; o dado é publicado
  semanas depois. Data de referência ≠ data de disponibilidade.

## Convenções de código
- TDD: escrever/ajustar o teste ANTES da implementação.
- Type hints em todas as funções públicas; funções pequenas e com responsabilidade única.
- Parse explícito de datas (`datetime.strptime(..., "%d/%m/%Y")`) e valores (`Decimal`). Nunca inferência de tipos.
- Retry apenas em timeout, HTTP 5xx e 429, com backoff exponencial. Outros 4xx falham rápido com mensagem clara.
- Logging com o módulo `logging` (nunca `print`).
- Configuração em `config/` ou variáveis de ambiente; nada hardcoded.
- Testes NUNCA fazem chamadas reais de rede: mockar o HTTP.
- Não adicionar dependências novas sem perguntar antes.

## Regras para o Claude
- Trabalhe em passos pequenos e mostre os testes antes da implementação.
- Não edite a seção "Decisões de design" do README: ela é escrita pelo Samuel.
- Ao tomar uma decisão de design não óbvia, explique a alternativa descartada.
- Período sem dados → HTTP 404 com JSON contendo "Value(s) not found" (tratar como lista vazia).
- Série inexistente → HTTP 404 com texto puro "A serie nao existe!" (erro de configuração, falhar).