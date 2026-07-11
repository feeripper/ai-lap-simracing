import React from 'react';

export default function TrainingPlan({ plan }) {
  if (!plan || !plan.primary_focus) {
    return null;
  }

  const { primary_focus, suggested_laps, target_corners, instructions, measurable_target, secondary_focuses } = plan;

  return (
    <div className="training-plan">
      <h2>Training Plan</h2>

      <div className="training-plan-overview">
        <div className="training-focus">
          <span className="label">Primary focus</span>
          <span className="value">{primary_focus}</span>
        </div>

        {secondary_focuses && secondary_focuses.length > 0 && (
          <div className="training-focus">
            <span className="label">Secondary focuses</span>
            <span className="value">{secondary_focuses.join(', ')}</span>
          </div>
        )}

        {target_corners && target_corners.length > 0 && (
          <div className="training-targets">
            <span className="label">Target corners</span>
            <span className="value">{target_corners.join(', ')}</span>
          </div>
        )}

        {suggested_laps > 0 && (
          <div className="training-laps">
            <span className="label">Suggested laps</span>
            <span className="value">{suggested_laps}</span>
          </div>
        )}

        {measurable_target && (
          <div className="training-measurable">
            <span className="label">Measurable target</span>
            <span className="value">{measurable_target}</span>
          </div>
        )}
      </div>

      {instructions && instructions.length > 0 && (
        <ol className="training-instructions">
          {instructions.map((instruction, index) => (
            <li key={index} className="training-instruction">
              {instruction}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
