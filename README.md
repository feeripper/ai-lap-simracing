# AI Lap Simracing

AI Lap Simracing é um coach de telemetria para simracing (iRacing) que compara sua volta contra voltas de referência e gera insights práticos de pilotagem.

## Status do MVP

O MVP local está funcional com:
- Normalização de voltas por distância
- Comparação numérica de telemetria
- Geração de insights de coaching
- Pipeline local ponta a ponta
- CLI para análise com CSVs
- Banco de dados para voltas de referência

## Documentação

A documentação completa está disponível em `docs/` e pode ser publicada via GitHub Pages.

- [Visão Geral](docs/index.md)
- [Começando](docs/getting-started.md)
- [Uso Local](docs/local-usage.md)
- [Voltas de Referência](docs/reference-laps.md)
- [Comandos CLI](docs/cli-commands.md)
- [Formato CSV](docs/telemetry-csv-format.md)
- [Arquitetura](docs/architecture.md)
- [Roadmap](docs/roadmap.md)

## Comandos Rápidos

```powershell
# Criar ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt

# Rodar testes
pytest -v
```