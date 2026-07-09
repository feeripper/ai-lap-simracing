import React from 'react';

export default function SectorInsights({ sectorInsights }) {
  if (!sectorInsights || sectorInsights.length === 0) {
    return null;
  }

  return (
    <div className="sector-insights">
      <h2>Sector Insights</h2>
      <ul>
        {sectorInsights.map((sector, index) => (
          <li key={index} className={`sector severity-${sector.severity || 'low'}`}>
            <div className="sector-header">
              <span className="sector-name">{sector.sector}</span>
              {sector.main_metric && (
                <span className="sector-metric">{sector.main_metric}</span>
              )}
            </div>
            {sector.message && <p className="sector-message">{sector.message}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}
