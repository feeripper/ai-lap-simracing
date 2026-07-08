# Uso Local

## Fluxo Local

O pipeline local funciona da seguinte forma:

1. **CSV do usuário** + **CSV de referência**
2. Normalização das voltas por distância
3. Comparação numérica de telemetria
4. Geração de insights de coaching
5. Saída em JSON com metadata, comparação e insights

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
  }
}
```
