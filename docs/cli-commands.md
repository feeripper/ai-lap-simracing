# Comandos CLI

## Rodar Testes

```powershell
pytest -v
```

## Seed do Banco

```powershell
python scripts/seed_db.py
```

## Cadastrar Volta de Referência

```powershell
python scripts/add_reference_lap.py path/to/reference.csv "Reference Driver" 120.0
```

## Analisar com CSV de Referência Direto

```powershell
python scripts/analyze_lap.py path/to/user.csv path/to/reference.csv
```

### Opções

- `--num-points 51`: Número de pontos para normalização (default: 101)
- `--distance-column lap_dist_pct`: Coluna de distância (default: lap_dist_pct)

## Analisar com Referência Ativa do Banco

```powershell
python scripts/analyze_lap_with_reference.py path/to/user.csv --simulator iRacing --car "Toyota GR86" --track Spa
```

### Opções

- `--simulator`: Nome do simulador (obrigatório)
- `--car`: Nome do carro (obrigatório)
- `--track`: Nome da pista (obrigatório)
- `--num-points 51`: Número de pontos para normalização (default: 101)
- `--distance-column lap_dist_pct`: Coluna de distância (default: lap_dist_pct)
