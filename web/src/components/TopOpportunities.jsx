import React from 'react';

export default function TopOpportunities({ opportunities }) {
  if (!opportunities || opportunities.length === 0) {
    return null;
  }

  return (
    <div className="top-opportunities">
      <h2>Top Opportunities</h2>
      <ul>
        {opportunities.map((opp) => (
          <li key={opp.rank} className={`opportunity severity-${opp.confidence || 'low'}`}>
            <div className="opportunity-header">
              <div className="opportunity-title">
                <span className="opportunity-rank">#{opp.rank}</span>
                <span className="opportunity-corner">{opp.corner_name || opp.corner}</span>
              </div>
              <div className="opportunity-meta">
                <span className="opportunity-confidence">{opp.confidence}</span>
                <span className="opportunity-loss">-{opp.estimated_time_loss}s</span>
              </div>
            </div>

            <div className="opportunity-body">
              <p className="opportunity-recommendation">{opp.recommendation}</p>

              <div className="opportunity-details">
                <span className="opportunity-cause">{opp.probable_cause}</span>
                <span className="opportunity-phase">{opp.phase}</span>
                <span className="opportunity-focus">{opp.training_focus}</span>
              </div>

              {opp.evidence && Object.keys(opp.evidence).length > 0 && (
                <div className="opportunity-evidence">
                  {Object.entries(opp.evidence).map(([metric, values]) => (
                    <div key={metric} className="evidence-metric">
                      <span className="evidence-metric-name">{metric}</span>
                      <span className="evidence-metric-diff">
                        {values.mean_diff != null ? values.mean_diff : '-'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
