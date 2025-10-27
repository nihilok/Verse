import { useState, useEffect } from "react";
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useMotionValueEvent,
} from "framer-motion";
import {
  BookOpen,
  AlertCircle,
  X,
  Loader2,
  History as HistoryIcon,
  Menu,
} from "lucide-react";
import PassageSearch from "./components/PassageSearch";
import BibleReader from "./components/BibleReader";
import InsightsModal from "./components/InsightsModal";
import InsightsHistoryComponent from "./components/InsightsHistory";
import InstallPrompt from "./components/InstallPrompt";
import { ModeToggle } from "./components/mode-toggle";
import { bibleService } from "./services/api";
import { BiblePassage, Insight, InsightHistory } from "./types";
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
} from "./components/ui/sidebar";
import { Button } from "./components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { loadLastPassage, saveLastPassage } from "./lib/storage";
import { BIBLE_BOOKS, getBookIndex } from "./lib/bibleStructure";
import "./App.css";

// Maximum number of insights to keep in history
const MAX_HISTORY_ITEMS = 50;

function App() {
  const [passage, setPassage] = useState<BiblePassage | null>(null);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(false);
  const [insightLoading, setInsightLoading] = useState(false);
  const [selectedText, setSelectedText] = useState("");
  const [selectedReference, setSelectedReference] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [currentBook, setCurrentBook] = useState("John");
  const [currentChapter, setCurrentChapter] = useState(3);
  const [currentTranslation, setCurrentTranslation] = useState("WEB");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarFullyHidden, setSidebarFullyHidden] = useState(false);
  const [insightsModalOpen, setInsightsModalOpen] = useState(false);
  const [insightsHistory, setInsightsHistory] = useState<InsightHistory[]>([]);

  // Check if we're on desktop (lg breakpoint)
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 1024);

  useEffect(() => {
    const handleResize = () => {
      const desktop = window.innerWidth >= 1024;
      setIsDesktop(desktop);
      // Keep sidebar open on desktop
      if (desktop) {
        setSidebarOpen(true);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Track sidebar x position for precise visibility control
  const sidebarX = useMotionValue(0);

  // Update button visibility based on sidebar position
  useMotionValueEvent(sidebarX, "change", (latest) => {
    // Button appears when sidebar is at -320 (fully hidden) or beyond
    setSidebarFullyHidden(latest <= -320);
  });

  // Load insights history from backend on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history =
          await bibleService.getInsightsHistory(MAX_HISTORY_ITEMS);
        setInsightsHistory(history);
      } catch (e) {
        console.error("Failed to load insights history:", e);
      }
    };
    loadHistory();
  }, []);

  // Load last viewed passage on mount
  useEffect(() => {
    const lastPassage = loadLastPassage();
    if (lastPassage) {
      // Auto-load the last passage the user was viewing
      handleSearch(
        lastPassage.book,
        lastPassage.chapter,
        undefined,
        undefined,
        lastPassage.translation,
      );
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = async (
    book: string,
    chapter: number,
    _verseStart?: number,
    _verseEnd?: number,
    translation: string = "WEB",
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

      // Save the current passage to localStorage for persistence
      saveLastPassage({ book, chapter, translation });

      // Close sidebar on mobile after successfully loading passage
      if (!isDesktop) {
        setSidebarOpen(false);
      }
    } catch (err) {
      setError(
        "Failed to load passage. Please check your input and try again.",
      );
      console.error("Error loading passage:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = async (direction: "prev" | "next") => {
    const bookIdx = getBookIndex(currentBook);
    if (bookIdx === -1) return;
    const currentBookInfo = BIBLE_BOOKS[bookIdx];
    let newBook = currentBook;
    let newChapter = currentChapter;

    if (direction === "next") {
      if (currentChapter < currentBookInfo.chapters) {
        newChapter = currentChapter + 1;
      } else if (bookIdx < BIBLE_BOOKS.length - 1) {
        // Move to first chapter of next book
        newBook = BIBLE_BOOKS[bookIdx + 1].name;
        newChapter = 1;
      } else {
        // At last chapter of last book, do nothing or loop (optional)
        return;
      }
    } else if (direction === "prev") {
      if (currentChapter > 1) {
        newChapter = currentChapter - 1;
      } else if (bookIdx > 0) {
        // Move to last chapter of previous book
        newBook = BIBLE_BOOKS[bookIdx - 1].name;
        newChapter = BIBLE_BOOKS[bookIdx - 1].chapters;
      } else {
        // At first chapter of first book, do nothing or loop (optional)
        return;
      }
    }

    await handleSearch(
      newBook,
      newChapter,
      undefined,
      undefined,
      currentTranslation,
    );
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
        const history =
          await bibleService.getInsightsHistory(MAX_HISTORY_ITEMS);
        setInsightsHistory(history);
      } catch (historyErr) {
        console.error("Failed to reload insights history:", historyErr);
      }
    } catch (err) {
      setError("Failed to generate insights. Please try again.");
      console.error("Error generating insights:", err);
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
    if (confirm("Are you sure you want to clear all insights history?")) {
      try {
        await bibleService.clearInsightsHistory();
        setInsightsHistory([]);
      } catch (err) {
        console.error("Failed to clear insights history:", err);
        setError("Failed to clear history. Please try again.");
      }
    }
  };

  return (
    <div className="mobile-viewport-height flex flex-col bg-background">
      {/* Book tab for opening sidebar on mobile, only visible when sidebar is fully hidden */}
      {!sidebarOpen && sidebarFullyHidden && (
        <button
          aria-label="Open sidebar"
          onClick={() => setSidebarOpen(true)}
          className="fixed left-0 top-15 -translate-y-1/2 z-50 lg:hidden"
          style={{
            width: 20,
            height: 60,
            borderTopRightRadius: 40,
            borderBottomRightRadius: 40,
            background: "var(--color-card)",
            boxShadow: "0 2px 8px rgba(0,0,0,0.12)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            border: "1px solid var(--color-border)",
            borderLeft: "none",
            padding: 0,
          }}
        >
          <span
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              width: "100%",
              height: "100%",
              color: "var(--primary)",
              fontWeight: 600,
              fontSize: 18,
              letterSpacing: 1,
              userSelect: "none",
            }}
            className="p-5 text-muted"
          >
            <Menu className="text-muted" />
          </span>
        </button>
      )}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="lg:hidden fixed inset-0 z-40 bg-black/50"
              onClick={() => setSidebarOpen(false)}
            />
          )}
        </AnimatePresence>

        <motion.div
          initial={false}
          animate={{
            x: sidebarOpen ? 0 : -320,
          }}
          transition={{
            type: "spring",
            damping: 30,
            stiffness: 300,
          }}
          style={{ x: sidebarX }}
          className="fixed lg:relative z-40 h-full"
        >
          <Sidebar className="h-full w-80 bg-card shadow-lg lg:shadow-none flex flex-col">
            <SidebarHeader className="flex flex-col gap-2 flex-shrink-0 pb-4 border-b relative">
              {!isDesktop && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSidebarOpen(false)}
                  className="absolute top-0 right-0"
                >
                  <X size={20} />
                </Button>
              )}
              <div className="flex gap-2 w-full items-center justify-between">
                <div className="flex gap-2 items-center">
                  <BookOpen
                    size={28}
                    className="text-primary"
                    strokeWidth={1.5}
                  />
                  <h2 className="font-semibold text-xl tracking-tight text-primary">
                    Verse
                  </h2>
                </div>
              </div>
              <p className="w-full text-xs text-muted-foreground italic">
                Discover wisdom through AI-powered insights
              </p>
            </SidebarHeader>
            <SidebarContent className="flex-1 min-h-0 overflow-y-auto">
              <Tabs
                defaultValue="search"
                className="w-full h-full flex flex-col"
              >
                <TabsList className="grid w-full grid-cols-2 flex-shrink-0">
                  <TabsTrigger value="search">Search</TabsTrigger>
                  <TabsTrigger
                    value="history"
                    className="flex items-center gap-1"
                  >
                    <HistoryIcon size={16} />
                    History
                  </TabsTrigger>
                </TabsList>
                <TabsContent
                  value="search"
                  className="mt-4 flex-1 overflow-y-auto"
                >
                  <PassageSearch onSearch={handleSearch} />
                </TabsContent>
                <TabsContent
                  value="history"
                  className="mt-4 flex-1 overflow-y-auto px-4"
                >
                  <InsightsHistoryComponent
                    history={insightsHistory}
                    onSelect={handleHistorySelect}
                    onClear={handleClearHistory}
                  />
                </TabsContent>
              </Tabs>
            </SidebarContent>
            {/* ModeToggle at the bottom of the sidebar */}
            <div className="w-full flex justify-center py-4 border-t mt-auto">
              <ModeToggle />
            </div>
          </Sidebar>
        </motion.div>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden p-6 min-h-0">
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive max-w-4xl mx-auto flex-shrink-0">
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

          <div className="max-w-4xl mx-auto flex-1 w-full min-h-0">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Loader2 size={48} className="animate-spin mb-4" />
                <p>Loading passage...</p>
              </div>
            ) : (
              <div className="bg-card rounded-lg shadow-sm border h-full flex flex-col">
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

      {/* PWA Install Prompt */}
      <InstallPrompt />
    </div>
  );
}

export default App;
