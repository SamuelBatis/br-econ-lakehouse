# br-econ-lakehouse

Pipeline de dados que coleta indicadores econômicos do Banco Central (dólar, Selic, IPCA)
e os organiza em um lakehouse. Projeto de estudo de Data Engineering.

## Como rodar

```bash
uv sync
uv run pytest -v
```

## Status
- [x] Fatiamento de períodos em janelas (limite de 10 anos da API SGS)
- [ ] Cliente HTTP com retry
- [ ] Parse e validação dos registros
- [ ] Watermark e carga incremental
- [ ] Camada bronze
- [ ] CLI
- [ ] Docker + CI