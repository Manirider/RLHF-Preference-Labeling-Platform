import React, { useState, useEffect } from 'react';
import ApiService from '../services/api';

export const ExportHub: React.FC = () => {
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [filterAnnotator, setFilterAnnotator] = useState<string>('');
  const [downloading, setDownloading] = useState<boolean>(false);

  useEffect(() => {
    ApiService.getCategories()
      .then(setCategories)
      .catch((err) => console.warn('Categories load error:', err));
  }, []);

  const handleDownload = () => {
    setDownloading(true);
    const url = ApiService.getExportUrl({
      category: selectedCategory || undefined,
      annotator_id: filterAnnotator.trim() || undefined,
    });

    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'labels.jsonl');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setTimeout(() => setDownloading(false), 1000);
  };

  const sampleJsonl = `{"prompt": "Explain the concept of quantum entanglement in simple terms.", "chosen": "Quantum entanglement is a phenomenon where two particles...", "rejected": "Entanglement means particles are magically linked...", "metadata": {"category": "factual_qa", "annotator_id": "annotator_1", "pair_id": 1, "label_id": 101}}`;

  return (
    <div className="export-hub-container">
      <div className="dashboard-header">
        <div>
          <h2>Reward-Model Preference Export Hub</h2>
          <p className="subtitle">
            Export pairwise human judgments in standard JSON Lines (JSONL) format for direct consumption by DPO, PPO, or Bradley-Terry reward model trainers.
          </p>
        </div>
      </div>

      <div className="export-card-grid">
        {/* Controls Card */}
        <div className="card export-controls-card">
          <div className="card-header">
            <h3>Export Configuration</h3>
            <span className="card-tag">Streaming Endpoint</span>
          </div>

          <div className="filter-group">
            <label className="filter-label" htmlFor="category-select">
              Filter by Prompt Category:
            </label>
            <select
              id="category-select"
              className="export-select"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="">All Categories (Full Dataset)</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label" htmlFor="annotator-filter">
              Filter by Annotator ID (Optional):
            </label>
            <input
              id="annotator-filter"
              type="text"
              className="export-input"
              value={filterAnnotator}
              onChange={(e) => setFilterAnnotator(e.target.value)}
              placeholder="e.g. annotator_1 or test_user"
            />
          </div>

          <div className="export-action-section">
            <button
              className="btn-primary btn-download"
              onClick={handleDownload}
              disabled={downloading}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              <span>{downloading ? 'Preparing Stream...' : 'Download labels.jsonl'}</span>
            </button>

            <span className="export-hint">
              Direct endpoint: <code>GET /api/export{selectedCategory ? `?category=${selectedCategory}` : ''}</code>
            </span>
          </div>
        </div>

        {/* Contract & Schema Card */}
        <div className="card export-schema-card">
          <div className="card-header">
            <h3>Reward Modeling Contract Rules</h3>
            <span className="card-tag">HuggingFace / TRL Format</span>
          </div>

          <div className="contract-rules-list">
            <div className="rule-item">
              <span className="rule-icon">✓</span>
              <div>
                <strong>Pairwise Mapping:</strong> When an annotator selects <em>A</em>, <code>chosen</code> becomes <code>response_a</code> and <code>rejected</code> becomes <code>response_b</code> (and vice versa for <em>B</em>).
              </div>
            </div>

            <div className="rule-item">
              <span className="rule-icon">✓</span>
              <div>
                <strong>Non-Binary Filtering:</strong> Judgments marked as <code>tie</code> or <code>skip</code> are strictly excluded from reward training export to prevent policy divergence.
              </div>
            </div>

            <div className="rule-item">
              <span className="rule-icon">✓</span>
              <div>
                <strong>Streaming Architecture:</strong> Backed by FastAPI <code>StreamingResponse</code> with chunked generator memory footprint.
              </div>
            </div>
          </div>

          <div className="json-preview-container">
            <div className="json-preview-header">
              <span>Expected Output Schema Preview</span>
              <span className="code-lang">JSONL</span>
            </div>
            <pre className="json-preview-body">
              <code>{sampleJsonl}</code>
            </pre>
          </div>

          <div className="validator-command-box">
            <span className="val-title">Downstream Verification CLI:</span>
            <code>python downstream/validate_data.py labels.jsonl</code>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportHub;
