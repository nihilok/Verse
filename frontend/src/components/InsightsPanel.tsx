import React from 'react';
import { Insight } from '../types';

interface InsightsPanelProps {
  insight: Insight | null;
  loading: boolean;
  selectedText: string;
}

const InsightsPanel: React.FC<InsightsPanelProps> = ({ insight, loading, selectedText }) => {
  if (loading) {
    return (
      <div className="insights-panel">
        <h2>AI Insights</h2>
        <div className="loading">
          <div className="spinner"></div>
          <p>Generating insights...</p>
        </div>
      </div>
    );
  }

  if (!insight) {
    return (
      <div className="insights-panel empty">
        <h2>AI Insights</h2>
        <p>Highlight any passage in the Bible reader to explore its meaning</p>
      </div>
    );
  }

  return (
    <div className="insights-panel">
      <h2>AI Insights</h2>
      {insight.cached && (
        <div className="cached-badge">
          <span>✓ Cached Result</span>
        </div>
      )}
      
      {selectedText && (
        <div className="selected-passage">
          <h3>Selected Passage</h3>
          <p className="passage-text">"{selectedText}"</p>
        </div>
      )}

      <div className="insight-section">
        <h3>📜 Historical Context</h3>
        <p>{insight.historical_context}</p>
      </div>

      <div className="insight-section">
        <h3>⛪ Theological Significance</h3>
        <p>{insight.theological_significance}</p>
      </div>

      <div className="insight-section">
        <h3>💡 Practical Application</h3>
        <p>{insight.practical_application}</p>
      </div>
    </div>
  );
};

export default InsightsPanel;
