---
title: Spike Garage61
---

# Spike Garage61 — Investigação de Referência de Voltas

Este documento é um **spike técnico investigativo**. Ele não implementa integração
real com o Garage61. O objetivo é registrar o que sabemos, os riscos e a arquitetura
proposta para, futuramente, obter voltas de referência automaticamente.

## Contexto de produto

No fluxo web do MVP, o usuário seleciona:

- simulador
- carro
- pista

O backend precisa encontrar uma boa volta de referência para comparar. Hoje isso
depende de um CSV cadastrado manualmente no banco (`ReferenceLap`). A visão futura é
que o backend consiga buscar automaticamente uma volta rápida no Garage61, sem o
usuário precisar exportar CSV manualmente.

## Perguntas de investigação

As perguntas abaixo devem ser confirmadas antes de qualquer implementação real.
Enquanto não confirmadas, elas são tratadas como **incertas**.

### O Garage61 possui API pública?

- Situação: **a confirmar**.
- O Garage61 é primariamente uma plataforma web/desktop de compartilhamento de
  telemetria para iRacing. Não há garantia documentada publicamente de uma API
  aberta e estável para terceiros.
- Ação: verificar documentação oficial, painel de desenvolvedor e termos de uso.

### Existe wrapper Python confiável?

- Situação: **a confirmar**.
- Não assumir a existência de biblioteca oficial. Qualquer wrapper de terceiros deve
  ser avaliado quanto a manutenção, licença e estabilidade antes de adotar.

### É necessário autenticação?

- Situação: **provável que sim**.
- Dados de telemetria e voltas geralmente pertencem a contas/equipes. É provável que
  seja necessário token de acesso ou login. Isso implica gestão segura de credenciais
  e não commitar segredos.

### É possível buscar laps por car/track?

- Situação: **a confirmar**.
- Esse é o requisito central. Precisamos confirmar se a API/serviço permite filtrar
  voltas por combinação de carro e pista (e idealmente simulador).

### É possível ordenar por melhor tempo?

- Situação: **a confirmar**.
- Necessário para escolher automaticamente uma "boa" referência (ex.: melhor volta
  limpa).

### É possível exportar telemetria em CSV?

- Situação: **a confirmar**.
- O pipeline atual (`analyze_lap_files`) consome CSV normalizável por distância.
  Precisamos confirmar formato e disponibilidade de exportação.

### Quais colunas o CSV exportado possui?

- Situação: **a confirmar**.
- O pipeline espera, no mínimo, uma coluna de distância (`lap_dist_pct`) e canais como
  `speed`, `throttle`, `brake`, `steering`, `gear`. Ver `telemetry-csv-format`.
- Ação: mapear as colunas reais exportadas para o formato canônico do projeto.

## Riscos

### Riscos técnicos

- API pode não existir, ser instável ou não documentada.
- Formato de exportação pode divergir do formato canônico do pipeline.
- Autenticação e rate limiting podem complicar automação.
- Dependência de wrapper de terceiros pode gerar dívida técnica.

### Riscos legais / termos de uso

- Uso automatizado pode violar os termos de serviço do Garage61.
- Dados de telemetria podem ter restrições de propriedade/privacidade.
- Necessário revisar licenciamento antes de redistribuir ou cachear dados.

## Plano de fallback

Se o Garage61 **não** puder ser automatizado com segurança:

- Manter o fluxo atual de **CSV manual** cadastrado como `ReferenceLap`.
- Permitir upload manual de referência via script/admin.
- Tratar Garage61 como fonte **opcional** e não bloqueante.

## Arquitetura proposta

O core de análise deve permanecer **genérico** e continuar aceitando um caminho de CSV.
O Garage61 entra por uma camada de **provider**, nunca acoplado ao pipeline.

```
Frontend (car + track selecionados)
        |
        v
Backend  ->  ReferenceLapProvider
                 |
     ------------------------------
     |                            |
LocalReferenceProvider     Garage61ReferenceProvider (futuro)
 (banco atual / CSV)        (API externa + cache local)
        |
        v
Analysis pipeline (analyze_lap_files)
```

### Componentes

- **`ReferenceLapProvider`**: interface/protocolo com:
  - `find_reference_lap(simulator, car, track)`
  - `get_reference_csv_path(reference_lap)`
- **`LocalReferenceProvider`**: usa o banco atual (`ReferenceLap` ativa). É a fonte
  real do MVP.
- **`Garage61ReferenceProvider`** (futuro): busca voltas externas, ordena por melhor
  tempo, exporta CSV e mantém **cache local** no banco.
- **Fallback manual por CSV**: sempre disponível caso a fonte externa falhe.
- **Cache local no banco**: evita refazer chamadas externas e reduz risco de rate
  limit / indisponibilidade.

## Modelo de dados futuro (proposta)

Estes campos são apenas propostos neste documento. **Não** são implementados neste
spike. Serviriam para rastrear a origem de uma volta de referência externa:

- `source` — origem da volta (ex.: `local`, `garage61`).
- `source_lap_id` — id da volta na fonte externa.
- `source_url` — URL de origem, quando aplicável.
- `external_driver_name` — nome do piloto na fonte externa.
- `external_lap_time` — tempo de volta reportado pela fonte.
- `fetched_at` — quando o dado foi buscado/cacheado.
- `raw_metadata_json` — metadados brutos retornados pela fonte.

## Próximos passos

1. Confirmar oficialmente as perguntas de investigação (API, auth, exportação).
2. Revisar termos de uso e implicações legais.
3. Implementar a camada `ReferenceLapProvider` com `LocalReferenceProvider` real e
   `Garage61ReferenceProvider` como stub (ver PR seguinte).
4. Só então avaliar implementação real do provider Garage61 com cache local.

## Reference Collector Spike

Enquanto o `ReferenceLapProvider` resolve **como consumir** uma volta de referência já
existente no banco, o **Reference Collector** resolve **como popular** o banco com voltas
externas. Ele é uma camada separada (`src/reference_collectors/`) que **não é acoplada ao
pipeline de análise** e roda somente sob demanda (script/admin), nunca no fluxo web.

### Princípios

- **Fonte externa experimental**: o Garage61 é tratado como uma fonte opcional e
  experimental. Nada no fluxo principal depende dele.
- **Token esperado**: `GARAGE61_ACCESS_TOKEN`. O collector tenta ler essa variável de
  ambiente quando um token não é passado explicitamente. Sem token, os métodos que
  precisam do Garage61 levantam `Garage61TokenMissingError`.
- **Import opcional**: qualquer biblioteca/wrapper do Garage61 é importada de forma
  **opcional e defensiva**. Se a dependência não estiver instalada, o collector levanta
  `Garage61DependencyMissingError` com mensagem clara, sem quebrar o resto do sistema.
  A dependência **não** é adicionada ao `requirements.txt` nesta fase.
- **Sem scraping / sem browser**: não fazemos scraping de HTML nem automação de browser,
  e não burlamos autenticação. Apenas API/cliente oficial, quando/se disponível.
- **Sem internet em testes**: todos os testes usam mocks do cliente Garage61. Nenhum
  teste faz chamada real de rede.

### Fluxo de coleta

```
Reference target (simulator + car + track)
        |
        v
Garage61ReferenceCollector.search_lap_candidates()
        |
        v
Candidate laps (Garage61LapCandidate)
        |
        v
download_lap_csv()  ->  cache local (data/references/...)
        |
        v
Validação de CSV (reaproveita telemetry_columns)
        |
        v
create_reference_lap()  ->  ReferenceLap (source="garage61")
        |
        v
Ativação manual/controlada (somente com --activate-best)
```

### Regras do collector

- **Salva CSV localmente** em `data/references/<sim>/<car-slug>/<track-slug>/` antes de
  cadastrar no banco. Esse diretório está no `.gitignore` (não commitamos CSVs).
- **Referências coletadas** entram com `source="garage61"` e `validation_status` igual a
  `"validated"` (CSV passou na validação) ou `"rejected"` (CSV inválido).
- **Sem duplicidade**: se já existir `ReferenceLap` com `source="garage61"` e o mesmo
  `source_lap_id`, o registro existente é reutilizado.
- **Ativação não é automática**: por padrão o collector **não** altera a referência ativa.
  A ativação só acontece quando o script recebe a flag explícita `--activate-best`, que
  ativa a melhor volta **validada** (menor `lap_time_seconds`).
- **Fallback manual continua existindo**: `scripts/add_reference_lap.py` e o cadastro
  manual permanecem válidos e independentes do Garage61.

### Script

`scripts/sync_reference_laps.py` orquestra a coleta:

```
python -m scripts.sync_reference_laps --simulator "iRacing" --car "Toyota GR86" --track "Spa" --limit 5
```

Flags: `--simulator`, `--car`, `--track`, `--limit`, `--activate-best`. O script exibe
mensagens claras quando o token não está configurado, a dependência externa não está
instalada, nenhum candidato é encontrado ou o CSV é inválido.
