import React, { useState } from 'react';
import './App.css';
import PassageSearch from './components/PassageSearch';
import BibleReader from './components/BibleReader';
import InsightsPanel from './components/InsightsPanel';
import { bibleService } from './services/api';
import { BiblePassage, Insight } from './types';

function App() {
  const [passage, setPassage] = useState<BiblePassage | null>(null);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(false);
  const [insightLoading, setInsightLoading] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (
    book: string,
    chapter: number,
    verseStart: number,
    verseEnd?: number
  ) => {
    setLoading(true);
    setError(null);
    setInsight(null);

    try {
      const result = await bibleService.getPassage({
        book,
        chapter,
        verse_start: verseStart,
        verse_end: verseEnd,
        translation: 'WEB',
      });
      setPassage(result);
    } catch (err) {
      setError('Failed to load passage. Please check your input and try again.');
      console.error('Error loading passage:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTextSelected = async (text: string, reference: string) => {
    setInsightLoading(true);
    setSelectedText(text);
    setError(null);

    try {
      const result = await bibleService.getInsights(text, reference);
      setInsight(result);
    } catch (err) {
      setError('Failed to generate insights. Please try again.');
      console.error('Error generating insights:', err);
    } finally {
      setInsightLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>📖 Verse</h1>
        <p className="tagline">Interactive Bible Reader with AI-Powered Insights</p>
      </header>

      <div className="app-content">
        <aside className="sidebar">
          <PassageSearch onSearch={handleSearch} />
        </aside>

        <main className="main-content">
          {error && (
            <div className="error-banner">
              <span>⚠️ {error}</span>
              <button onClick={() => setError(null)}>✕</button>
            </div>
          )}

          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading passage...</p>
            </div>
          ) : (
            <BibleReader passage={passage} onTextSelected={handleTextSelected} />
          )}
        </main>

        <aside className="insights-sidebar">
          <InsightsPanel
            insight={insight}
            loading={insightLoading}
            selectedText={selectedText}
          />
        </aside>
      </div>
    </div>
  );
}

export default App;
