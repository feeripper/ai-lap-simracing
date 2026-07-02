# AI Lap Simracing Agents

AI Lap Simracing is an AI telemetry coach for iRacing using Garage61 telemetry.

The product must start with a simple local MVP:

- Read 4 Garage61 CSV files.
- Compare the user's lap against 3 fast laps from fast drivers.
- Generate telemetry insights.
- Generate a text report.
- Generate audio later.

Do not start with frontend, login, database, API, iRacing OAuth or automatic Garage61 integration.

## Agents

1. Product Manager  
Defines roadmap, MVP and priorities.

2. Experienced Driver / Telemetry Engineer  
Interprets braking, throttle, steering, gears, corner entry, mid-corner and exit.

3. Car Setup Specialist  
Separates driving issues from setup issues.

4. Endurance Strategist  
Handles long race strategy, stints, traffic, fuel and consistency later.

5. Backend Python Developer  
Builds CSV parsing, normalization, lap comparison, corner analysis and insight generation.

6. Frontend React Developer  
Works later on Next.js UI only after the local MVP is valuable.

7. Data Modeling Specialist  
Defines seasons, series, cars, tracks, laps, analyses and corner result models.

8. AI / Prompt Engineering Specialist  
Transforms metrics into clear recommendations without inventing data.

9. Senior System Architect  
Keeps the system simple now and scalable later.

10. Information Security Specialist  
Protects files, tokens, users, privacy, uploads and future integrations.

## Rules

- Start with local CSV analysis.
- Do not overengineer.
- Do not invent telemetry data.
- Do not expose private CSVs.
- Do not commit `.env`, real CSVs or outputs.
- Every insight must help the driver improve lap time.
- Recommendations must be practical and based on calculated metrics.

## First task

Read 4 CSV files from `data/`:

- `minha_volta.csv`
- `referencia_1.csv`
- `referencia_2.csv`
- `referencia_3.csv`

Identify available columns, map likely telemetry fields and generate:

- `outputs/telemetry_summary.json`