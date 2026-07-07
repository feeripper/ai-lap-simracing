# AI Lap Simracing Tasks

## Database Setup (MVP Web)

- [x] Add SQLAlchemy to requirements.txt
- [x] Create database models (Simulator, Car, Track, ReferenceLap)
- [x] Create repository functions for CRUD operations
- [x] Create seed script for iRacing, Toyota GR86, Spa
- [x] Add unit tests for database layer
- [x] Create script to add reference laps from CSV files

**How to run the seed:**
```bash
# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env
cp .env.example .env

# Run the seed script
python scripts/seed_db.py
```

This will create:
- Simulator: iRacing
- Car: Toyota GR86
- Track: Spa

**How to add a reference lap:**
```bash
# After running the seed, add a reference lap with:
python scripts/add_reference_lap.py <csv_path> <driver_name> <lap_time_seconds>

# Example:
python scripts/add_reference_lap.py data/reference_lap.csv "Max Verstappen" 145.234
```

Note: Adding a new active reference lap automatically deactivates any previous active lap for the same combination.

## Phase 1 — Local MVP

- [x] Create project structure
- [ ] Read Garage61 CSV files
- [ ] Detect available columns
- [ ] Map likely telemetry columns
- [ ] Generate telemetry summary JSON
- [ ] Normalize laps by distance
- [ ] Compare user lap against reference 1
- [ ] Compare user lap against 3 references
- [ ] Load manual track corners from JSON
- [ ] Analyze telemetry by corner
- [ ] Generate insights JSON
- [ ] Generate text report

## Phase 2 — Audio

- [ ] Generate short coaching script
- [ ] Generate MP3 audio

## Phase 3 — Simple UI

- [ ] Create Streamlit upload screen
- [ ] Show report in UI
- [ ] Download report
- [ ] Download audio

## Not now

- [ ] Frontend Next.js
- [ ] Login Google
- [ ] Production database / PostgreSQL
- [ ] Garage61 automatic integration
- [ ] iRacing OAuth