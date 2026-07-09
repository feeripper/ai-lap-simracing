import React from 'react';

export default function AnalyzeForm({
  catalog,
  simulator,
  car,
  track,
  onSimulatorChange,
  onCarChange,
  onTrackChange,
  onFileChange,
  onSubmit,
  loading,
  fileName,
}) {
  return (
    <form className="analyze-form" onSubmit={onSubmit}>
      <div className="field">
        <label htmlFor="simulator">Step 1: Select Simulator</label>
        <select
          id="simulator"
          value={simulator}
          onChange={(e) => onSimulatorChange(e.target.value)}
        >
          <option value="">Choose your simulator</option>
          {catalog.simulators.map((s) => (
            <option key={s.id} value={s.name}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="car">Step 2: Select Car</label>
        <select id="car" value={car} onChange={(e) => onCarChange(e.target.value)}>
          <option value="">Choose your car</option>
          {catalog.cars.map((c) => (
            <option key={c.id} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="track">Step 3: Select Track</label>
        <select id="track" value={track} onChange={(e) => onTrackChange(e.target.value)}>
          <option value="">Choose the track</option>
          {catalog.tracks.map((t) => (
            <option key={t.id} value={t.name}>
              {t.name}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="user_csv">Step 4: Upload Garage61 CSV</label>
        <input
          id="user_csv"
          type="file"
          accept=".csv"
          onChange={(e) => onFileChange(e.target.files[0] || null)}
        />
        <p className="field-help">Export your lap telemetry from Garage61 and upload the CSV file here.</p>
        {fileName && <span className="file-name">Selected: {fileName}</span>}
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Analyzing your lap...' : 'Analyze Lap'}
      </button>
    </form>
  );
}
