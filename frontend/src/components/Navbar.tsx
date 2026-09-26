import React, { useState } from 'react';

interface NavbarProps {
  activeTab: 'annotate' | 'analytics' | 'export';
  setActiveTab: (tab: 'annotate' | 'analytics' | 'export') => void;
  annotatorId: string;
  setAnnotatorId: (id: string) => void;
  systemHealthy: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  annotatorId,
  setAnnotatorId,
  systemHealthy,
}) => {
  const [isEditingAnnotator, setIsEditingAnnotator] = useState(false);
  const [tempAnnotator, setTempAnnotator] = useState(annotatorId);

  const handleSaveAnnotator = () => {
    const trimmed = tempAnnotator.trim() || 'test_user';
    setAnnotatorId(trimmed);
    setIsEditingAnnotator(false);
  };

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <div className="brand-logo">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
        </div>
        <div className="brand-text">
          <span className="brand-title">RLHF Preference Lab</span>
          <span className="brand-subtitle">v1.0 • Reward Model Engine</span>
        </div>
      </div>

      <nav className="nav-tabs" role="tablist">
        <button
          className={`nav-tab ${activeTab === 'annotate' ? 'active' : ''}`}
          onClick={() => setActiveTab('annotate')}
          role="tab"
          aria-selected={activeTab === 'annotate'}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          Annotation Studio
        </button>

        <button
          className={`nav-tab ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
          role="tab"
          aria-selected={activeTab === 'analytics'}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="20" x2="18" y2="10" />
            <line x1="12" y1="20" x2="12" y2="4" />
            <line x1="6" y1="20" x2="6" y2="14" />
          </svg>
          Analytics & Metrics
        </button>

        <button
          className={`nav-tab ${activeTab === 'export' ? 'active' : ''}`}
          onClick={() => setActiveTab('export')}
          role="tab"
          aria-selected={activeTab === 'export'}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          JSONL Export
        </button>
      </nav>

      <div className="navbar-controls">
        <div className={`status-pill ${systemHealthy ? 'online' : 'offline'}`} title={systemHealthy ? "Backend connected" : "Backend unreachable"}>
          <span className="status-dot"></span>
          <span className="status-text">{systemHealthy ? 'Connected' : 'Offline'}</span>
        </div>

        <div className="annotator-badge-container">
          {isEditingAnnotator ? (
            <div className="annotator-edit-form">
              <input
                type="text"
                className="annotator-input"
                value={tempAnnotator}
                onChange={(e) => setTempAnnotator(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSaveAnnotator()}
                autoFocus
                placeholder="Annotator ID"
              />
              <button className="btn-icon" onClick={handleSaveAnnotator} title="Save ID">
                ✓
              </button>
            </div>
          ) : (
            <div
              className="annotator-chip"
              onClick={() => {
                setTempAnnotator(annotatorId);
                setIsEditingAnnotator(true);
              }}
              title="Click to switch annotator"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
              <span className="annotator-label">Annotator:</span>
              <strong className="annotator-id">{annotatorId}</strong>
              <span className="edit-hint">✎</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
