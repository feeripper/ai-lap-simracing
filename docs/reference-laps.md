# Voltas de Referência

## Seed do Banco

Para inicializar o banco de dados com dados básicos:

```powershell
python scripts/seed_db.py
```

O seed cria:
- **Simulator**: iRacing
- **Car**: Toyota GR86
- **Track**: Spa

## Cadastrar Volta de Referência

Para cadastrar uma nova volta de referência no banco:

```powershell
python scripts/add_reference_lap.py path/to/reference.csv "Reference Driver" 120.0
```

### Argumentos

- `csv_path`: Caminho para o CSV da volta de referência
- `driver_name`: Nome do piloto de referência
- `lap_time_seconds`: Tempo da volta em segundos

### Comportamento

- Uma nova referência ativa desativa automaticamente a referência anterior para a mesma combinação de simulator/car/track
- Isso permite manter apenas uma referência ativa por combinação

## Analisar com Referência Ativa do Banco

Para analisar uma volta do usuário usando a referência ativa cadastrada no banco:

```powershell
python scripts/analyze_lap_with_reference.py path/to/user.csv --simulator iRacing --car "Toyota GR86" --track Spa
```

### Opções Adicionais

```powershell
# Usar número de pontos diferente
python scripts/analyze_lap_with_reference.py path/to/user.csv --simulator iRacing --car "Toyota GR86" --track Spa --num-points 51

# Usar coluna de distância diferente
python scripts/analyze_lap_with_reference.py path/to/user.csv --simulator iRacing --car "Toyota GR86" --track Spa --distance-column lap_dist_pct
```
