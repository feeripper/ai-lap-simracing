# Arquitetura

## Fluxo Técnico

```
CSV (usuário) + CSV (referência)
    ↓
normalize_lap_by_distance()
    ↓
compare_laps()
    ↓
generate_insights()
    ↓
JSON final (metadata, comparison, insights)
```

## Módulos Principais

### src/analysis/normalizer.py

- Função: `normalize_lap_by_distance()`
- Responsabilidade: Normalizar voltas para o mesmo número de pontos por distância
- Usa: `numpy.linspace` e `numpy.interp` para interpolação robusta

### src/analysis/comparator.py

- Função: `compare_laps()`
- Responsabilidade: Comparar telemetria de duas voltas normalizadas
- Calcula: métricas overall e por setor (`mean_diff`, `min_diff`, `max_diff`, `mean_abs_diff`)
- Define 4 setores: `0-25%`, `25-50%`, `50-75%`, `75-100%`

### src/analysis/insight_generator.py

- Função: `generate_insights()`
- Responsabilidade: Gerar insights de coaching a partir da comparação
- Retorna: summary, priority, recommendations, sector_insights
- Define severidade: low, medium, high baseada em thresholds

### src/analysis/pipeline.py

- Função: `analyze_lap_files()`
- Responsabilidade: Pipeline ponta a ponta para análise de CSVs
- Integra: normalização, comparação e geração de insights
- Valida: existência de arquivos, CSVs vazios, colunas necessárias

### scripts/analyze_lap.py

- Função: CLI para análise com CSVs diretos
- Responsabilidade: Interface de linha de comando para o pipeline
- Imprime: JSON formatado no stdout
- Retorna: código 0 (sucesso) ou 1 (erro)

### scripts/analyze_lap_with_reference.py

- Função: CLI para análise usando referência ativa do banco
- Responsabilidade: Buscar referência no banco e executar pipeline
- Valida: simulator, car, track, referência ativa
- Imprime: JSON formatado no stdout

### src/db/models.py

- Responsabilidade: Definição dos modelos SQLAlchemy
- Modelos: Simulator, Car, Track, ReferenceLap

### src/db/repository.py

- Responsabilidade: Funções CRUD para o banco de dados
- Funções: create/get para Simulator, Car, Track, ReferenceLap

## Regra Central

Todas as comparações usam a fórmula:

```
diff = user - reference
```

## Interpretação das Diferenças

- **speed negativo**: usuário mais lento que referência
- **throttle negativo**: usuário usa menos acelerador (aceleração tardia ou saída fraca)
- **brake positivo**: usuário usa mais freio (excesso ou frenagem prolongada)
- **steering mean_abs_diff alto**: diferença de traçado ou correções excessivas
- **gear mean_abs_diff alto**: diferença de seleção de marchas

## Severidade

Para `speed`, `steering`, `gear`:
- `low`: `mean_abs_diff > 0` e `mean_abs_diff <= 5`
- `medium`: `mean_abs_diff > 5` e `mean_abs_diff <= 15`
- `high`: `mean_abs_diff > 15`

Para `throttle`, `brake` (valores 0-1):
- `low`: `mean_abs_diff > 0` e `mean_abs_diff <= 0.05`
- `medium`: `mean_abs_diff > 0.05` e `mean_abs_diff <= 0.15`
- `high`: `mean_abs_diff > 0.15`

## Camada de Reference Providers

A busca por voltas de referência é abstraída em `src/reference_providers/`, mantendo
o core de análise genérico:

- `ReferenceLapProvider` — interface/protocolo com `find_reference_lap(simulator, car, track)`
  e `get_reference_csv_path(reference_lap)`.
- `LocalReferenceLapProvider` — fonte real do MVP; busca a referência ativa no banco.
- `Garage61ReferenceLapProvider` — stub para integração futura (ver o spike Garage61).

O endpoint `POST /analyze-with-reference` usa o provider local para localizar o CSV de
referência antes de chamar o pipeline. Fontes externas (Garage61) entrarão futuramente
via provider, sem acoplar o pipeline.

O modelo `ReferenceLap` já possui campos opcionais (`source`, `source_lap_id`,
`source_url`, `track_layout`, `imported_at`, `file_checksum`, `validation_status`,
`raw_metadata_json`, `notes`) preparados para suportar um futuro coletor automático
de voltas (ex.: Garage61), sem afetar a criação manual existente.
