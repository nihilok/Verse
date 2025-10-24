import { useState } from 'react';
import { BookOpen, AlertCircle, X, Loader2 } from 'lucide-react';
import PassageSearch from './components/PassageSearch';
import BibleReader from './components/BibleReader';
import InsightsPanel from './components/InsightsPanel';
import { ModeToggle } from './components/mode-toggle';
import { bibleService } from './services/api';
import { BiblePassage, Insight } from './types';
import './App.css';

function App() {
  const [passage, setPassage] = useState<BiblePassage | null>(null);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(false);
  const [insightLoading, setInsightLoading] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [currentBook, setCurrentBook] = useState('John');
  const [currentChapter, setCurrentChapter] = useState(3);
  const [currentTranslation, setCurrentTranslation] = useState('WEB');

  const handleSearch = async (
    book: string,
    chapter: number,
    verseStart: number,
    verseEnd?: number,
    translation: string = 'WEB'
  ) => {
    setLoading(true);
    setError(null);
    setInsight(null);
    setCurrentBook(book);
    setCurrentChapter(chapter);
    setCurrentTranslation(translation);

    try {
      const result = await bibleService.getPassage({
        book,
        chapter,
        verse_start: verseStart,
        verse_end: verseEnd,
        translation,
      });
      setPassage(result);
    } catch (err) {
      setError('Failed to load passage. Please check your input and try again.');
      console.error('Error loading passage:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = async (direction: 'prev' | 'next') => {
    const newChapter = direction === 'next' ? currentChapter + 1 : currentChapter - 1;
    if (newChapter < 1) return;

    await handleSearch(currentBook, newChapter, 1, undefined, currentTranslation);
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
    <div className="min-h-screen flex flex-col bg-background">
      <header className="bg-gradient-to-r from-primary to-blue-600 text-primary-foreground shadow-lg">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <BookOpen size={32} />
              <div>
                <h1 className="text-3xl font-bold">Verse</h1>
                <p className="text-sm opacity-90">Interactive Bible Reader with AI-Powered Insights</p>
              </div>
            </div>
            <ModeToggle />
          </div>
        </div>
      </header>

      <div className="flex-1 max-w-[1800px] mx-auto w-full p-6">
        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr_420px] gap-6 lg:h-[calc(100vh-180px)]">
          <aside className="lg:overflow-y-auto">
            <PassageSearch onSearch={handleSearch} />
          </aside>

          <main className="lg:overflow-y-auto bg-card rounded-lg border border-border shadow-sm p-6">
            {error && (
              <div className="mb-4 flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle size={20} />
                <span className="flex-1">{error}</span>
                <button
                  onClick={() => setError(null)}
                  className="hover:opacity-70 transition-opacity"
                >
                  <X size={20} />
                </button>
              </div>
            )}

            {loading ? (
              <div className="flex flex-col items-center justify-center h-96 text-muted-foreground">
                <Loader2 size={48} className="animate-spin mb-4" />
                <p>Loading passage...</p>
              </div>
            ) : (
              <BibleReader
                passage={passage}
                onTextSelected={handleTextSelected}
                onNavigate={handleNavigate}
              />
            )}
          </main>

          <aside className="lg:overflow-y-auto bg-card rounded-lg border border-border shadow-sm p-6">
            <InsightsPanel
              insight={insight}
              loading={insightLoading}
              selectedText={selectedText}
            />
          </aside>
        </div>
      </div>
    </div>
  );
}

export default App;
