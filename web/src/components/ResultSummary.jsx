import React from 'react';

export default function ResultSummary({ result }) {
  const insights = result.insights || {};
  return (
    <div className="result-summary">
      <h2>Summary</h2>
      {insights.summary ? (
        <p className="summary-text">{insights.summary}</p>
      ) : (
        <p className="summary-text">No summary available.</p>
      )}

      {insights.priority && (
        <p className="priority">
          <strong>Priority:</strong> {insights.priority}
        </p>
      )}

      {result.analysis_run_id != null && (
        <p className="analysis-run-id">
          <strong>Analysis run id:</strong> {result.analysis_run_id}
        </p>
      )}
    </div>
  );
}
