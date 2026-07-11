import React from 'react';

export default function ResultSummary({ result }) {
  const insights = result.insights || {};
  const diagnosis = result.diagnosis || {};
  const summary = diagnosis.summary || insights.summary || 'No summary available.';
  const opportunities = result.top_opportunities || diagnosis.top_opportunities || [];
  const timeLoss = diagnosis.overall_lap_delta_seconds ?? 0;

  const warnings = result.warnings || diagnosis.warnings || [];

  return (
    <div className="result-summary">
      <h2>Coaching Summary</h2>
      <p className="summary-text">{summary}</p>

      <div className="result-stats">
        <div className="stat">
          <span className="stat-label">Opportunities</span>
          <span className="stat-value">{opportunities.length}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Estimated time loss</span>
          <span className="stat-value">{timeLoss.toFixed(3)}s</span>
        </div>
        <div className="stat">
          <span className="stat-label">Diagnosis version</span>
          <span className="stat-value">{result.diagnosis_version || '1.0'}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Processing time</span>
          <span className="stat-value">{result.processing_time_ms || 0}ms</span>
        </div>
      </div>

      {result.analysis_run_id != null && (
        <p className="analysis-run-id">
          <strong>Analysis run id:</strong> {result.analysis_run_id}
        </p>
      )}

      {warnings.length > 0 && (
        <div className="warnings">
          <strong>Warnings</strong>
          <ul>
            {warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
