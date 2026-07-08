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

A documentação completa está disponível em `docs-site/` e é publicada automaticamente via GitHub Pages em: https://feeripper.github.io/ai-lap-simracing/

> A documentação é publicada via Docusaurus e GitHub Actions. Em **Settings → Pages**, selecione **GitHub Actions** como source.

Para rodar a documentação localmente:

```powershell
cd docs-site
npm install
npm start
```

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