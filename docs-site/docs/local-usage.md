# Uso Local

## Fluxo Local

O pipeline local funciona da seguinte forma:

1. **CSV do usuário** + **CSV de referência**
2. Normalização das voltas por distância
3. Comparação numérica de telemetria
4. Geração de insights de coaching
5. Análise de perda de tempo e recomendações de treinamento
6. Saída em JSON com metadata, comparação, insights e coaching

## Analisar com CSVs Diretos

Para analisar uma volta do usuário contra uma volta de referência usando CSVs diretamente:

```powershell
python scripts/analyze_lap.py path/to/user.csv path/to/reference.csv
```

### Opções Adicionais

```powershell
# Usar número de pontos diferente
python scripts/analyze_lap.py path/to/user.csv path/to/reference.csv --num-points 51

# Usar coluna de distância diferente
python scripts/analyze_lap.py path/to/user.csv path/to/reference.csv --distance-column lap_dist_pct
```

## Saída

O script imprime um JSON formatado no stdout com a seguinte estrutura:

```json
{
  "metadata": {
    "user_csv_path": "...",
    "reference_csv_path": "...",
    "num_points": 101,
    "distance_column": "lap_dist_pct",
    "user_rows_raw": 123,
    "reference_rows_raw": 123,
    "normalized_points": 101
  },
  "comparison": {
    "overall": {...},
    "sectors": [...]
  },
  "insights": {
    "summary": "...",
    "priority": "...",
    "recommendations": [...],
    "sector_insights": [...]
  },
  "coaching": {
    "time_loss": {
      "total_time_loss_seconds": 2.5,
      "sectors": [
        {"name": "Sector 1", "time_loss_seconds": 0.8, "severity": "high"},
        ...
      ]
    },
    "strongest_loss_areas": [...],
    "driving_issue": "...",
    "training_recommendation": "..."
  }
}
```

## Análise de Coaching

A nova seção `coaching` fornece:

- **time_loss**: Estimativa de tempo perdido por setor, baseada em diferenças de velocidade
- **strongest_loss_areas**: Setores com maior perda de tempo, ordenados por gravidade
- **driving_issue**: Descrição do problema de condução mais provável (ex: velocidade abaixo da referência, excesso de freio)
- **training_recommendation**: Recomendação específica de treinamento baseada na análise

## Formato de CSV

O pipeline suporta tanto o formato interno quanto o formato do Garage61:

- **Interno**: `lap_dist_pct` (0-100), `speed`, `throttle`, `brake`, etc.
- **Garage61**: `LapDistPct` (0-1), `Speed`, `Throttle`, `Brake`, etc.

A coluna de distância é automaticamente normalizada para 0-100% durante o processamento.
