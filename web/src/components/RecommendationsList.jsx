import React from 'react';

export default function RecommendationsList({ recommendations }) {
  if (!recommendations || recommendations.length === 0) {
    return null;
  }

  return (
    <div className="recommendations">
      <h2>Recommendations</h2>
      <ul>
        {recommendations.map((rec, index) => (
          <li key={index} className={`rec severity-${rec.severity || 'low'}`}>
            <div className="rec-header">
              <span className="rec-title">{rec.title || rec.metric}</span>
              {rec.severity && <span className="rec-severity">{rec.severity}</span>}
            </div>
            {rec.message && <p className="rec-message">{rec.message}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}
