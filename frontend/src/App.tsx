import { useState, useEffect } from 'react';
import { BookOpen, AlertCircle, X, Loader2, Menu, History as HistoryIcon } from 'lucide-react';
import PassageSearch from './components/PassageSearch';
import BibleReader from './components/BibleReader';
import InsightsModal from './components/InsightsModal';
import InsightsHistoryComponent from './components/InsightsHistory';
import { ModeToggle } from './components/mode-toggle';
import { bibleService } from './services/api';
import { BiblePassage, Insight, InsightHistory } from './types';
import { Sidebar, SidebarHeader, SidebarContent } from './components/ui/sidebar';
import { Button } from './components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import './App.css';

// Maximum number of insights to keep in history
const MAX_HISTORY_ITEMS = 50;

function App() {
  const [passage, setPassage] = useState<BiblePassage | null>(null);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(false);
  const [insightLoading, setInsightLoading] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [selectedReference, setSelectedReference] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [currentBook, setCurrentBook] = useState('John');
  const [currentChapter, setCurrentChapter] = useState(3);
  const [currentTranslation, setCurrentTranslation] = useState('WEB');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [insightsModalOpen, setInsightsModalOpen] = useState(false);
  const [insightsHistory, setInsightsHistory] = useState<InsightHistory[]>([]);

  // Load insights history from backend on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await bibleService.getInsightsHistory(MAX_HISTORY_ITEMS);
        setInsightsHistory(history);
      } catch (e) {
        console.error('Failed to load insights history:', e);
      }
    };
    loadHistory();
  }, []);

  const handleSearch = async (
    book: string,
    chapter: number,
    _verseStart?: number,
    _verseEnd?: number,
    translation: string = 'WEB'
  ) => {
    setLoading(true);
    setError(null);
    setCurrentBook(book);
    setCurrentChapter(chapter);
    setCurrentTranslation(translation);

    try {
      // Load full chapter by default for better reading experience
      const result = await bibleService.getChapter(book, chapter, translation);
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

    await handleSearch(currentBook, newChapter, undefined, undefined, currentTranslation);
  };

  const handleTextSelected = async (text: string, reference: string) => {
    setInsightLoading(true);
    setSelectedText(text);
    setSelectedReference(reference);
    setError(null);

    try {
      const result = await bibleService.getInsights(text, reference);
      setInsight(result);
      setInsightsModalOpen(true);
      
      // Reload history from backend to get the latest insights
      try {
        const history = await bibleService.getInsightsHistory(MAX_HISTORY_ITEMS);
        setInsightsHistory(history);
      } catch (historyErr) {
        console.error('Failed to reload insights history:', historyErr);
      }
    } catch (err) {
      setError('Failed to generate insights. Please try again.');
      console.error('Error generating insights:', err);
    } finally {
      setInsightLoading(false);
    }
  };

  const handleHistorySelect = (item: InsightHistory) => {
    setInsight(item.insight);
    setSelectedText(item.text);
    setSelectedReference(item.reference);
    setInsightsModalOpen(true);
  };

  const handleClearHistory = async () => {
    if (confirm('Are you sure you want to clear all insights history?')) {
      try {
        await bibleService.clearInsightsHistory();
        setInsightsHistory([]);
      } catch (err) {
        console.error('Failed to clear insights history:', err);
        setError('Failed to clear history. Please try again.');
      }
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="bg-gradient-to-r from-primary to-blue-600 text-primary-foreground shadow-lg">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden text-primary-foreground hover:bg-primary-foreground/10"
              >
                <Menu size={24} />
              </Button>
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

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className={`${sidebarOpen ? 'block' : 'hidden'} lg:block fixed lg:relative inset-0 lg:inset-auto z-40 bg-black/50 lg:bg-transparent`}
             onClick={(e) => {
               if (e.target === e.currentTarget) setSidebarOpen(false);
             }}>
          <Sidebar className="h-full w-80 bg-card shadow-lg lg:shadow-none">
            <SidebarHeader className="flex items-center justify-between">
              <h2 className="font-semibold text-lg">Navigation</h2>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden"
              >
                <X size={20} />
              </Button>
            </SidebarHeader>
            <SidebarContent>
              <Tabs defaultValue="search" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="search">Search</TabsTrigger>
                  <TabsTrigger value="history" className="flex items-center gap-1">
                    <HistoryIcon size={16} />
                    History
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="search" className="mt-4">
                  <PassageSearch onSearch={handleSearch} />
                </TabsContent>
                <TabsContent value="history" className="mt-4">
                  <InsightsHistoryComponent
                    history={insightsHistory}
                    onSelect={handleHistorySelect}
                    onClear={handleClearHistory}
                  />
                </TabsContent>
              </Tabs>
            </SidebarContent>
          </Sidebar>
        </div>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden p-6">
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive max-w-4xl mx-auto">
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

          <div className="max-w-4xl mx-auto h-full">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-96 text-muted-foreground">
                <Loader2 size={48} className="animate-spin mb-4" />
                <p>Loading passage...</p>
              </div>
            ) : (
              <div className="bg-card rounded-lg shadow-sm border h-full overflow-y-auto">
                <BibleReader
                  passage={passage}
                  onTextSelected={handleTextSelected}
                  onNavigate={handleNavigate}
                />
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Insights Modal */}
      <InsightsModal
        open={insightsModalOpen}
        onOpenChange={setInsightsModalOpen}
        insight={insight}
        selectedText={selectedText}
        reference={selectedReference}
      />

      {/* Loading overlay for insights */}
      {insightLoading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card p-6 rounded-lg shadow-lg flex flex-col items-center gap-4">
            <Loader2 size={48} className="animate-spin text-primary" />
            <p className="text-lg">Generating insights...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
