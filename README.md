# AI Lap Simracing

AI Lap Simracing is an AI telemetry coach for iRacing.

It uses Garage61 telemetry to compare your lap against 3 fast laps from fast drivers in the same car and track, then generates practical coaching insights about braking, steering, throttle, gear usage and corner performance.

## MVP

The first MVP is local and simple.

Input:

- `data/minha_volta.csv`
- `data/referencia_1.csv`
- `data/referencia_2.csv`
- `data/referencia_3.csv`
- `tracks/<track>.json`

Output:

- `outputs/telemetry_summary.json`
- `outputs/insights.json`
- `outputs/relatorio.txt`

## Initial stack

- Python 3.12
- pandas
- numpy
- pydantic
- pytest

## Main rule

Do not start with frontend, login, database, API or automatic Garage61 integration.

Start with local CSV analysis.