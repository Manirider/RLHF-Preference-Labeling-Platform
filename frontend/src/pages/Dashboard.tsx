import React, { useEffect, useState } from 'react';
import { AnalyticsData } from '../types';
import ApiService from '../services/api';

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await ApiService.getAnalytics();
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading && !data) {
    return (
      <div className="dashboard-loading">
        <div className="skeleton-card skeleton" style={{ height: '300px' }}></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-card">
        <h4>Failed to load analytics</h4>
        <p>{error}</p>
        <button className="btn-retry" onClick={fetchAnalytics}>
          Retry
        </button>
      </div>
    );
  }

  const total = data?.total_labels || 0;
  const dist = data?.label_distribution || { A: 0, B: 0, tie: 0, skip: 0 };
  const agreementRate = data?.agreement_rate ?? 0.0;
  const agreementPct = Math.round(agreementRate * 100);

  const getPct = (val: number) => (total > 0 ? ((val / total) * 100).toFixed(1) : '0.0');

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h2>Evaluation Analytics & Alignment Quality</h2>
          <p className="subtitle">
            Telemetry metrics tracking annotator consensus, distribution balance, and labeling throughput.
          </p>
        </div>
        <button className="btn-secondary" onClick={fetchAnalytics} title="Refresh data">
          ↻ Refresh Metrics
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="stats-kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Total Annotations</div>
          <div className="kpi-value">{total}</div>
          <div className="kpi-subtext">Cumulative preference labels</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Inter-Rater Agreement</div>
          <div className="kpi-value text-accent">{agreementPct}%</div>
          <div className="kpi-subtext">Consensus rate on multi-annotator pairs</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Active Annotators</div>
          <div className="kpi-value">{data?.active_annotators || 1}</div>
          <div className="kpi-subtext">Independent evaluators contributing</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Labeled Pairs Coverage</div>
          <div className="kpi-value">
            {data?.labeled_pairs || 0} / {data?.total_pairs || 72}
          </div>
          <div className="kpi-subtext">Unique prompts with ≥1 label</div>
        </div>
      </div>

      {/* Distribution Bars */}
      <div className="dashboard-grid">
        <div className="card dashboard-card">
          <div className="card-header">
            <h3>Preference Choice Distribution</h3>
            <span className="card-tag">A vs B vs Tie vs Skip</span>
          </div>

          <div className="distribution-bars-list">
            <div className="dist-bar-item">
              <div className="dist-bar-meta">
                <span className="dist-name">Response A (Preferred)</span>
                <span className="dist-count">{dist.A} ({getPct(dist.A)}%)</span>
              </div>
              <div className="meter-track">
                <div className="meter-fill fill-a" style={{ width: `${getPct(dist.A)}%` }}></div>
              </div>
            </div>

            <div className="dist-bar-item">
              <div className="dist-bar-meta">
                <span className="dist-name">Response B (Preferred)</span>
                <span className="dist-count">{dist.B} ({getPct(dist.B)}%)</span>
              </div>
              <div className="meter-track">
                <div className="meter-fill fill-b" style={{ width: `${getPct(dist.B)}%` }}></div>
              </div>
            </div>

            <div className="dist-bar-item">
              <div className="dist-bar-meta">
                <span className="dist-name">Tie / Equal Quality</span>
                <span className="dist-count">{dist.tie} ({getPct(dist.tie)}%)</span>
              </div>
              <div className="meter-track">
                <div className="meter-fill fill-tie" style={{ width: `${getPct(dist.tie)}%` }}></div>
              </div>
            </div>

            <div className="dist-bar-item">
              <div className="dist-bar-meta">
                <span className="dist-name">Skipped</span>
                <span className="dist-count">{dist.skip} ({getPct(dist.skip)}%)</span>
              </div>
              <div className="meter-track">
                <div className="meter-fill fill-skip" style={{ width: `${getPct(dist.skip)}%` }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Agreement Methodology Card */}
        <div className="card dashboard-card">
          <div className="card-header">
            <h3>Inter-Rater Consensus Methodology</h3>
            <span className="card-tag">Statistical Formula</span>
          </div>

          <div className="methodology-content">
            <p>
              Inter-rater agreement measures reliability across multiple human raters evaluating the identical prompt-response pair:
            </p>
            <div className="formula-box">
              <code>Agreement Rate = Σ(Majority Annotations) / Σ(Total Multi-Rater Annotations)</code>
            </div>
            <ul className="methodology-notes">
              <li>Pairs with a single annotator are excluded from consensus calculation.</li>
              <li>When 3 annotators independently choose A on the same pair: <strong>Agreement = 1.0 (100%)</strong>.</li>
              <li>Values range strictly between <strong>0.0 and 1.0</strong>.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Category Breakdown */}
      {data?.category_breakdown && Object.keys(data.category_breakdown).length > 0 && (
        <div className="card dashboard-card mt-4">
          <div className="card-header">
            <h3>Distribution by Prompt Category</h3>
            <span className="card-tag">Cross-Domain Coverage</span>
          </div>

          <div className="category-chips-grid">
            {Object.entries(data.category_breakdown).map(([cat, count]) => (
              <div key={cat} className="category-stat-pill">
                <span className="cat-name">{cat.replace(/_/g, ' ')}</span>
                <span className="cat-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
