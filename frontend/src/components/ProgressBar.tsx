import React from 'react';
import { LabelDistribution } from '../types';

interface ProgressBarProps {
  totalLabels: number;
  totalPairs: number;
  distribution: LabelDistribution;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  totalLabels,
  totalPairs,
  distribution,
}) => {
  const safeTotalPairs = totalPairs > 0 ? totalPairs : 72;
  const percentage = Math.min(Math.round((totalLabels / safeTotalPairs) * 100), 100);

  return (
    <div className="progress-card">
      <div className="progress-header">
        <div className="progress-title-group">
          <span className="progress-label">Batch Progress</span>
          <span className="progress-stats">
            <strong>{totalLabels}</strong> / {safeTotalPairs} labeled ({percentage}%)
          </span>
        </div>

        <div className="distribution-chips">
          <div className="dist-chip chip-a" title="Response A chosen">
            <span className="chip-indicator"></span>
            <span className="chip-label">A:</span>
            <span className="chip-value">{distribution?.A ?? 0}</span>
          </div>

          <div className="dist-chip chip-b" title="Response B chosen">
            <span className="chip-indicator"></span>
            <span className="chip-label">B:</span>
            <span className="chip-value">{distribution?.B ?? 0}</span>
          </div>

          <div className="dist-chip chip-tie" title="Equal quality / Tie">
            <span className="chip-indicator"></span>
            <span className="chip-label">Tie:</span>
            <span className="chip-value">{distribution?.tie ?? 0}</span>
          </div>

          <div className="dist-chip chip-skip" title="Skipped / Ambiguous">
            <span className="chip-indicator"></span>
            <span className="chip-label">Skip:</span>
            <span className="chip-value">{distribution?.skip ?? 0}</span>
          </div>
        </div>
      </div>

      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
};
