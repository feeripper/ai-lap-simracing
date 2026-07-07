# AI Lap Simracing

AI Lap Simracing é um coach de telemetria para simracing (iRacing) que compara sua volta contra voltas de referência e gera insights práticos de pilotagem.

## Objetivo do Produto

O objetivo é ajudar pilotos de simracing a melhorarem seus tempos de volta através de análise de telemetria comparativa. O sistema compara a volta do usuário com voltas de referência de pilotos rápidos e gera recomendações específicas sobre:

- Velocidade média
- Uso de acelerador
- Uso de freio
- Uso de volante
- Seleção de marchas
- Performance por setor

## Status Atual do MVP

O MVP local está funcional com:

- ✅ Normalização de voltas por distância
- ✅ Comparação numérica de telemetria
- ✅ Geração de insights de coaching
- ✅ Pipeline local ponta a ponta
- ✅ CLI para análise com CSVs
- ✅ Banco de dados para voltas de referência
- ✅ CLI para análise usando referência ativa do banco

## Documentação

- [Começando](getting-started.md) - Instalação e configuração
- [Uso Local](local-usage.md) - Como usar o pipeline local
- [Voltas de Referência](reference-laps.md) - Seed e cadastro de referências
- [Comandos CLI](cli-commands.md) - Lista de comandos disponíveis
- [Formato CSV](telemetry-csv-format.md) - Formato esperado dos CSVs
- [Arquitetura](architecture.md) - Fluxo técnico e módulos
- [Roadmap](roadmap.md) - Limitações e próximos passos

## Como Publicar no GitHub Pages

Para publicar esta documentação no GitHub Pages:

1. Vá em **Settings** do repositório
2. Entre em **Pages**
3. Em **Source**, escolha **Deploy from a branch**
4. Selecione o branch **main**
5. Selecione a pasta **/docs**
6. Clique em **Save**

A documentação será publicada automaticamente em `https://<usuario>.github.io/ai-lap-simracing/`
