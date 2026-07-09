---
title: Fluxo Web MVP
---

# Fluxo Web MVP

Este documento descreve como subir e testar o fluxo web ponta a ponta do
`ai-lap-simracing`: frontend em `web/`, backend FastAPI, provider local de referência,
pipeline de análise e persistência.

## Visão geral do fluxo

```
Frontend (web/)
  seleciona simulador + carro + pista
  envia CSV da volta do usuário
        |
        v
Backend (FastAPI)  POST /analyze-with-reference
        |
        v
LocalReferenceLapProvider  (busca referência ativa no banco)
        |
        v
Pipeline (analyze_lap_files)
        |
        v
Persistência (AnalysisRun)
        |
        v
Response  ->  Frontend renderiza summary / priority / recommendations / sector_insights
```

## Endpoints do backend

- `GET /health` — status do serviço.
- `GET /catalog` — catálogo (simuladores, carros, pistas) do banco.
- `GET /simulators`, `GET /cars`, `GET /tracks` — listas individuais.
- `GET /reference-laps` — voltas de referência cadastradas.
- `POST /analyze` — análise direta com dois CSVs (fluxo manual/debug).
- `POST /analyze-with-reference` — fluxo principal do MVP (CSV do usuário + referência ativa).
- `GET /analyses` — histórico resumido das análises persistidas.
- `GET /analyses/{id}` — análise completa persistida.

## Requisitos

- Python 3.12+
- Node.js 20+
- Dependências Python instaladas (`requirements.txt`).

## 1. Subir o backend

Instale as dependências e rode a API:

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

A API sobe em `http://127.0.0.1:8000`. A documentação interativa fica em
`http://127.0.0.1:8000/docs`.

## 2. Rodar o seed do banco

Cria simulador (iRacing), carro (Toyota GR86) e pista (Spa):

```bash
python scripts/seed_db.py
```

## 3. Cadastrar uma volta de referência

Cadastre um CSV de referência ativo para a combinação do seed:

```bash
python scripts/add_reference_lap.py <caminho_do_csv> "Nome do Piloto" <tempo_em_segundos>
```

Exemplo:

```bash
python scripts/add_reference_lap.py data/referencia_1.csv "Fast Driver" 120.5
```

## 4. Subir o frontend

Em outro terminal:

```bash
cd web
npm install
npm run dev
```

O frontend sobe em `http://localhost:5173`. A URL do backend pode ser ajustada via
variável `VITE_API_BASE_URL` (padrão `http://127.0.0.1:8000`).

## 5. Testar o fluxo MVP

1. Abra `http://localhost:5173`.
2. Confirme que o status do backend aparece como `online`.
3. Selecione `iRacing`, `Toyota GR86` e `Spa`.
4. Faça upload do CSV da sua volta.
5. Clique em **Analyze Lap**.
6. Valide que aparecem: `summary`, `priority`, `recommendations` e `sector_insights`.

## Tratamento de erros

O frontend exibe mensagens claras para os principais casos:

- **CSV inválido** — arquivo sem extensão `.csv` ou conteúdo inválido (HTTP 400).
- **Referência não encontrada** — não há volta de referência ativa para a seleção (HTTP 404).
- **Backend offline** — a API não está no ar (falha de conexão).
- **Erro inesperado** — qualquer outra falha (HTTP 500).

## Observações

- O Garage61 ainda **não** é integrado. O MVP usa o `LocalReferenceLapProvider`.
- O core de análise permanece genérico e aceita caminhos de CSV; fontes externas
  entram futuramente via provider (ver o spike Garage61).
