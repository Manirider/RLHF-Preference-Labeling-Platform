import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import Annotator from './pages/Annotator';
import Dashboard from './pages/Dashboard';
import ExportHub from './pages/ExportHub';
import ApiService from './services/api';

export default function App() {
  const [tab, setTab] = useState<'annotate' | 'analytics' | 'export'>('annotate');
  const [annotatorId, setAnnotatorId] = useState<string>(() => {
    return localStorage.getItem('annotator_id') || 'test_user';
  });
  const [systemHealthy, setSystemHealthy] = useState<boolean>(true);

  // Sync annotator ID changes to localStorage
  useEffect(() => {
    localStorage.setItem('annotator_id', annotatorId);
  }, [annotatorId]);

  // Check health on mount and periodically
  useEffect(() => {
    const checkStatus = async () => {
      try {
        await ApiService.checkHealth();
        setSystemHealthy(true);
      } catch {
        setSystemHealthy(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-layout">
      <Navbar
        activeTab={tab}
        setActiveTab={setTab}
        annotatorId={annotatorId}
        setAnnotatorId={setAnnotatorId}
        systemHealthy={systemHealthy}
      />

      <main className="content-container">
        {tab === 'annotate' && (
          <Annotator
            annotatorId={annotatorId}
            onNavigateToAnalytics={() => setTab('analytics')}
          />
        )}
        {tab === 'analytics' && <Dashboard />}
        {tab === 'export' && <ExportHub />}
      </main>

      <footer className="app-footer">
        <span>RLHF Human Preference Labeling Platform • Production-Grade Annotation Pipeline</span>
      </footer>
    </div>
  );
}
