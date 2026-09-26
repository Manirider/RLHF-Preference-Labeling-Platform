import React, { useEffect, useState, useCallback } from 'react';
import { Pair, ChoiceType, AnalyticsData } from '../types';
import ApiService from '../services/api';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { ProgressBar } from '../components/ProgressBar';
import { ResponseCard } from '../components/ResponseCard';

interface AnnotatorProps {
  annotatorId: string;
  onNavigateToAnalytics: () => void;
}

export const Annotator: React.FC<AnnotatorProps> = ({
  annotatorId,
  onNavigateToAnalytics,
}) => {
  const [pair, setPair] = useState<Pair | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [allDone, setAllDone] = useState<boolean>(false);
  const [feedbackFlash, setFeedbackFlash] = useState<string | null>(null);

  const [analytics, setAnalytics] = useState<AnalyticsData>({
    total_labels: 0,
    label_distribution: { A: 0, B: 0, tie: 0, skip: 0 },
    agreement_rate: 0.0,
    total_pairs: 72,
  });

  const loadAnalytics = useCallback(async () => {
    try {
      const data = await ApiService.getAnalytics();
      setAnalytics(data);
    } catch (err) {
      console.warn('Analytics fetch error:', err);
    }
  }, []);

  const loadNextPair = useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    setAllDone(false);

    try {
      const next = await ApiService.getNextPair(annotatorId);
      setPair(next);
      setAllDone(false);
    } catch (err: unknown) {
      setPair(null);
      const msg = err instanceof Error ? err.message : String(err);
      if (
        msg.includes('No unlabeled pairs') ||
        msg.includes('404')
      ) {
        setAllDone(true);
      } else {
        setErrorMessage(msg);
      }
    } finally {
      setLoading(false);
    }
  }, [annotatorId]);

  useEffect(() => {
    loadNextPair();
    loadAnalytics();
  }, [loadNextPair, loadAnalytics]);

  const handleChoice = useCallback(
    async (choice: ChoiceType) => {
      if (!pair || submitting) return;

      setSubmitting(true);
      const choiceLabels: Record<ChoiceType, string> = {
        A: 'Selected Response A',
        B: 'Selected Response B',
        tie: 'Marked as Tie / Equal',
        skip: 'Skipped pair',
      };
      setFeedbackFlash(choiceLabels[choice]);

      try {
        await ApiService.submitLabel({
          pair_id: pair.id,
          annotator_id: annotatorId,
          chosen: choice,
        });

        // Refresh stats immediately
        loadAnalytics();

        // Subtle animation timeout before loading next
        setTimeout(() => {
          setFeedbackFlash(null);
          loadNextPair();
          setSubmitting(false);
        }, 180);
      } catch (err: unknown) {
        setFeedbackFlash(null);
        setSubmitting(false);
        const msg = err instanceof Error ? err.message : 'Submission failed';
        setErrorMessage(`Submission failed: ${msg}`);
      }
    },
    [pair, submitting, annotatorId, loadAnalytics, loadNextPair]
  );

  // Bind keyboard shortcuts A, B, T, S
  useKeyboardShortcuts({
    onChoice: handleChoice,
    disabled: loading || submitting || !pair,
  });

  return (
    <div className="annotator-studio">
      <ProgressBar
        totalLabels={analytics.total_labels}
        totalPairs={analytics.total_pairs || 72}
        distribution={analytics.label_distribution}
      />

      {feedbackFlash && (
        <div className="feedback-banner" role="status" aria-live="polite">
          <span className="pulse-indicator"></span>
          <span>{feedbackFlash}</span>
        </div>
      )}

      {errorMessage && (
        <div className="error-card">
          <div className="error-icon">⚠️</div>
          <div className="error-text">
            <h4>Connection / Submission Error</h4>
            <p>{errorMessage}</p>
          </div>
          <button className="btn-retry" onClick={loadNextPair}>
            Retry Connection
          </button>
        </div>
      )}

      {loading && !pair && (
        <div className="skeleton-container">
          <div className="skeleton-prompt skeleton"></div>
          <div className="skeleton-grid">
            <div className="skeleton-card skeleton"></div>
            <div className="skeleton-card skeleton"></div>
          </div>
        </div>
      )}

      {allDone && (
        <div className="empty-state-card">
          <div className="empty-icon">🎉</div>
          <h3>All Caught Up!</h3>
          <p>
            Annotator <strong>{annotatorId}</strong> has labeled all currently available prompt-response pairs.
          </p>
          <div className="empty-actions">
            <button className="btn-primary" onClick={onNavigateToAnalytics}>
              View Analytics & Agreement Rate
            </button>
            <button className="btn-secondary" onClick={() => loadNextPair()}>
              Check for New Pairs
            </button>
          </div>
        </div>
      )}

      {pair && !loading && (
        <main className="annotation-main" aria-label="Preference Annotation Workspace">
          <section className="prompt-card">
            <div className="prompt-header">
              <span className="badge-category">{pair.category.replace(/_/g, ' ')}</span>
              <span className="pair-id-tag">Pair #{pair.id}</span>
            </div>
            <h2 className="prompt-text">{pair.prompt}</h2>
          </section>

          <section className="responses-grid">
            <ResponseCard
              variant="A"
              content={pair.response_a}
              onSelect={() => handleChoice('A')}
              disabled={submitting}
            />
            <ResponseCard
              variant="B"
              content={pair.response_b}
              onSelect={() => handleChoice('B')}
              disabled={submitting}
            />
          </section>

          <section className="actions-toolbar">
            <div className="primary-actions">
              <button
                className="btn-action btn-tie"
                onClick={() => handleChoice('tie')}
                disabled={submitting}
                title="Both responses are equally good or equally flawed (Key: T)"
                aria-label="Tie or Equal Quality"
              >
                <span>Tie / Equal Quality</span>
                <kbd className="key-hint">T</kbd>
              </button>

              <button
                className="btn-action btn-skip"
                onClick={() => handleChoice('skip')}
                disabled={submitting}
                title="Skip this pair without recording a preference (Key: S)"
                aria-label="Skip Pair"
              >
                <span>Skip Pair</span>
                <kbd className="key-hint">S</kbd>
              </button>
            </div>

            <div className="shortcuts-legend">
              <span className="legend-label">Keyboard Shortcuts:</span>
              <span className="legend-item"><kbd>A</kbd> Better A</span>
              <span className="legend-item"><kbd>B</kbd> Better B</span>
              <span className="legend-item"><kbd>T</kbd> Tie</span>
              <span className="legend-item"><kbd>S</kbd> Skip</span>
            </div>
          </section>
        </main>
      )}
    </div>
  );
};

export default Annotator;
