import React, { useEffect, useState } from 'react';
import { analyzeWithReference, getCatalog, getHealth } from './api/client.js';
import AnalyzeForm from './components/AnalyzeForm.jsx';
import ResultSummary from './components/ResultSummary.jsx';
import RecommendationsList from './components/RecommendationsList.jsx';
import SectorInsights from './components/SectorInsights.jsx';

export default function App() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [catalog, setCatalog] = useState({ simulators: [], cars: [], tracks: [] });

  const [simulator, setSimulator] = useState('');
  const [car, setCar] = useState('');
  const [track, setTrack] = useState('');
  const [userCsv, setUserCsv] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    getHealth()
      .then((data) => setBackendStatus(data.status === 'ok' ? 'online' : 'error'))
      .catch(() => setBackendStatus('offline'));

    getCatalog()
      .then((data) => setCatalog(data))
      .catch(() => {
        // Catalog will remain empty; backend status already reflects issues.
      });
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setResult(null);

    if (!simulator || !car || !track) {
      setError('Please select a simulator, car and track to continue.');
      return;
    }
    if (!userCsv) {
      setError('Please upload your Garage61 CSV file to analyze your lap.');
      return;
    }

    setLoading(true);
    try {
      const data = await analyzeWithReference({ userCsv, simulator, car, track });
      setResult(data);
    } catch (err) {
      if (err.status === 404) {
        setError(err.message || 'No reference lap found for this car/track combination. Try a different selection.');
      } else if (err.status === 400) {
        setError(err.message || 'The CSV file is invalid. Please export a valid Garage61 telemetry file.');
      } else if (err.message === 'Failed to fetch') {
        setError('Unable to connect to the server. Please ensure the backend is running.');
      } else {
        setError(err.message || 'Something went wrong during analysis. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-titles">
          <h1>AI Lap Coach</h1>
          <p className="header-subtitle">Telemetry analysis powered by Garage61 data</p>
        </div>
        <div className={`backend-status status-${backendStatus}`}>
          {backendStatus === 'online' ? '● Online' : '● Offline'}
        </div>
      </header>

      <main className="app-main">
        <section className="form-section">
          <AnalyzeForm
            catalog={catalog}
            simulator={simulator}
            car={car}
            track={track}
            onSimulatorChange={setSimulator}
            onCarChange={setCar}
            onTrackChange={setTrack}
            onFileChange={setUserCsv}
            onSubmit={handleSubmit}
            loading={loading}
            fileName={userCsv ? userCsv.name : ''}
          />
          {error && <div className="error-message">{error}</div>}
        </section>

        {result && (
          <section className="result-section">
            <ResultSummary result={result} />
            <RecommendationsList recommendations={result.insights?.recommendations} />
            <SectorInsights sectorInsights={result.insights?.sector_insights} />
          </section>
        )}
      </main>
    </div>
  );
}
