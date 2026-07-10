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
- Contrato canônico de análise com `top_opportunities`, `training_plan`, `diagnosis_version` e `processing_time_ms`
- Serialização segura de NumPy, Pandas e enums para JSON
- Endpoints de análise, listagem e consulta com schemas tipados

## Contrato de Análise

O backend expõe os endpoints `/analyze`, `/analyze-with-reference`, `/analyses` e `/analyses/{analysis_id}` retornando um contrato canônico.

### Resposta detalhada

```json
{
  "analysis_id": 1,
  "analysis_run_id": 1,
  "status": "completed",
  "diagnosis_version": "1.0",
  "processing_time_ms": 248,
  "simulator": "iRacing",
  "car": "Toyota GR86",
  "track": "Spa-Francorchamps",
  "top_opportunities": [
    {
      "rank": 1,
      "corner": "Sector 2",
      "corner_name": "Sector 2",
      "phase": "braking",
      "estimated_time_loss": 0.31,
      "confidence": "high",
      "evidence": {
        "speed": {"mean_diff": -14.0}
      },
      "probable_cause": "braking_too_early",
      "recommendation": "Você iniciou a frenagem antes da referência...",
      "training_focus": "brake_release"
    }
  ],
  "training_plan": {
    "primary_focus": "brake_release",
    "suggested_laps": 5,
    "target_corners": ["Sector 2"],
    "instructions": ["Prioridade 1: ..."],
    "measurable_target": "Reduzir aproximadamente 0.093 s em Sector 2.",
    "secondary_focuses": []
  },
  "warnings": []
}
```

### Listagem resumida

`GET /analyses` retorna apenas campos leves:
- `analysis_id`, `id`, `created_at`, `status`, `diagnosis_version`
- `simulator`, `car`, `track`, `analysis_type`, `summary`, `priority`
- `total_time_loss`, `number_of_opportunities`, `primary_focus`

### Registros antigos

Registros persistidos antes desta versão continuam legíveis. Os campos ausentes (`diagnosis_version`, `top_opportunities`, `training_plan`, `warnings`, `processing_time_ms`) são preenchidos com valores padrão na consulta.

### Versão do diagnóstico

O campo `diagnosis_version` identifica a versão das regras de coaching. A versão atual é `1.0` e é persistida junto com o resultado.

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