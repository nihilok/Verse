import React from 'react';
import { Sparkles, Loader, BookMarked, Church, Lightbulb, CheckCircle } from 'lucide-react';
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
        <div className="insights-header">
          <Sparkles size={24} />
          <h2>AI Insights</h2>
        </div>
        <div className="loading">
          <Loader size={40} className="spinner-icon" />
          <p>Generating insights...</p>
        </div>
      </div>
    );
  }

  if (!insight) {
    return (
      <div className="insights-panel empty">
        <div className="insights-header">
          <Sparkles size={24} />
          <h2>AI Insights</h2>
        </div>
        <div className="empty-state">
          <Sparkles size={48} className="empty-icon" />
          <p>Highlight any passage in the Bible reader to explore its meaning</p>
        </div>
      </div>
    );
  }

  return (
    <div className="insights-panel">
      <div className="insights-header">
        <Sparkles size={24} />
        <h2>AI Insights</h2>
      </div>

      {insight.cached && (
        <div className="cached-badge">
          <CheckCircle size={16} />
          <span>Cached Result</span>
        </div>
      )}
      
      {selectedText && (
        <div className="selected-passage">
          <h3>Selected Passage</h3>
          <p className="passage-text">"{selectedText}"</p>
        </div>
      )}

      <div className="insight-section">
        <h3>
          <BookMarked size={20} />
          Historical Context
        </h3>
        <p>{insight.historical_context}</p>
      </div>

      <div className="insight-section">
        <h3>
          <Church size={20} />
          Theological Significance
        </h3>
        <p>{insight.theological_significance}</p>
      </div>

      <div className="insight-section">
        <h3>
          <Lightbulb size={20} />
          Practical Application
        </h3>
        <p>{insight.practical_application}</p>
      </div>
    </div>
  );
};

export default InsightsPanel;
