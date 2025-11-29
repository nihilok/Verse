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
  CheckCircle,
  X,
  History as HistoryIcon,
  MessageSquare,
  Menu,
  Settings as SettingsIcon,
  Search as SearchIcon,
} from "lucide-react";
import PassageSearch from "./components/PassageSearch";
import BibleReader from "./components/BibleReader";
import InsightsModal from "./components/InsightsModal";
import DefinitionModal from "./components/DefinitionModal";
import ChatModal from "./components/ChatModal";
import InsightsHistoryComponent from "./components/InsightsHistory";
import ChatHistory from "./components/ChatHistory";
import UserSettings from "./components/UserSettings";
import InstallPrompt from "./components/InstallPrompt";
import LoadingOverlay from "./components/LoadingOverlay";
import { ModeToggle } from "./components/mode-toggle";
import { bibleService } from "./services/api";
import { BiblePassage, Insight, Definition, InsightHistory, ChatMessage, StandaloneChat, StandaloneChatMessage } from "./types";
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
  const [definition, setDefinition] = useState<Definition | null>(null);
  const [loading, setLoading] = useState(false);
  const [insightLoading, setInsightLoading] = useState(false);
  const [definitionLoading, setDefinitionLoading] = useState(false);
  const [selectedText, setSelectedText] = useState("");
  const [selectedReference, setSelectedReference] = useState("");
  const [selectedWord, setSelectedWord] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [currentBook, setCurrentBook] = useState("John");
  const [currentChapter, setCurrentChapter] = useState(3);
  const [currentTranslation, setCurrentTranslation] = useState("WEB");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarFullyHidden, setSidebarFullyHidden] = useState(false);
  const [insightsModalOpen, setInsightsModalOpen] = useState(false);
  const [definitionModalOpen, setDefinitionModalOpen] = useState(false);
  const [insightsHistory, setInsightsHistory] = useState<InsightHistory[]>([]);
  const [currentInsightId, setCurrentInsightId] = useState<number | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatStreamingMessage, setChatStreamingMessage] = useState<string>("");

  // Standalone chat state
  const [chatHistory, setChatHistory] = useState<StandaloneChat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);
  const [currentChatPassage, setCurrentChatPassage] = useState<{ text: string; reference: string } | null>(null);
  const [standaloneChatMessages, setStandaloneChatMessages] = useState<StandaloneChatMessage[]>([]);
  const [standaloneChatLoading, setStandaloneChatLoading] = useState(false);
  const [standaloneChatStreamingMessage, setStandaloneChatStreamingMessage] = useState<string>("");
  const [chatModalOpen, setChatModalOpen] = useState(false);
  const [insightChatModalOpen, setInsightChatModalOpen] = useState(false);
  const [pendingChatPassage, setPendingChatPassage] = useState<{ text: string; reference: string } | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

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

  // Load insights history and chat history from backend on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history =
          await bibleService.getInsightsHistory(MAX_HISTORY_ITEMS);
        setInsightsHistory(history);
        
        const chats = await bibleService.getStandaloneChats(MAX_HISTORY_ITEMS);
        setChatHistory(chats);
      } catch (e) {
        console.error("Failed to load history:", e);
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
        lastPassage.verse_start,
        lastPassage.verse_end,
        lastPassage.translation,
      );
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = async (
    book: string,
    chapter: number,
    verseStart?: number,
    verseEnd?: number,
    translation: string = "WEB",
  ) => {
    setLoading(true);
    setError(null);
    setCurrentBook(book);
    setCurrentChapter(chapter);
    setCurrentTranslation(translation);

    try {
      let result: BiblePassage;
      if (verseStart !== undefined) {
        // Load specific verses
        result = await bibleService.getPassage({
          book,
          chapter,
          verse_start: verseStart,
          verse_end: verseEnd,
          translation,
        });
      } else {
        // Load full chapter for better reading experience
        result = await bibleService.getChapter(book, chapter, translation);
      }
      setPassage(result);

      // Save the current passage to localStorage for persistence
      saveLastPassage({
        book,
        chapter,
        verse_start: verseStart,
        verse_end: verseEnd,
        translation,
      });

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

  const normaliseWhitespace = (text: string) => {
    return text.replace(/\s+/g, " ").trim();
  };

  const handleTextSelected = async (text: string, reference: string, isSingleWord: boolean, verseText?: string) => {
    // Strip whitespace from text for consistent caching
    const normalizedText = text.trim();
    
    if (isSingleWord && !verseText) {
      setError("Unable to find the verse containing this word. Please try selecting the full verse.");
      return;
    }
    if (isSingleWord && verseText) {
      // Handle single word definition
      setDefinitionLoading(true);
      setSelectedWord(normalizedText);
      setSelectedReference(reference);
      setError(null);

      try {
        const result = await bibleService.getDefinition(normalizedText, verseText, reference);
        setDefinition(result);
        setDefinitionModalOpen(true);
      } catch (err) {
        setError("Failed to generate definition. Please try again.");
        console.error("Error generating definition:", err);
      } finally {
        setDefinitionLoading(false);
      }
    } else {
      // Handle multi-word insight
      setInsightLoading(true);
      setSelectedText(normalizedText);
      setSelectedReference(reference);
      setError(null);

      try {
        const result = await bibleService.getInsights(normalizedText, reference);
        setInsight(result);
        setInsightsModalOpen(true);

        // Reload history from backend to get the latest insights
        try {
          const history =
            await bibleService.getInsightsHistory(MAX_HISTORY_ITEMS);
          setInsightsHistory(history);

          // Get the insight ID from the history (it should be the most recent one)
          const matchingInsight = history.find(
            (item) =>
              normaliseWhitespace(item.text) === normaliseWhitespace(normalizedText) &&
              item.reference === reference,
          );
          if (matchingInsight) {
            const insightId = parseInt(matchingInsight.id);
            setCurrentInsightId(insightId);

            // Load chat messages for this insight
            const messages = await bibleService.getChatMessages(insightId);
            setChatMessages(messages);
          } else {
            setCurrentInsightId(null);
            setChatMessages([]);
          }
        } catch (historyErr) {
          console.error("Failed to reload insights history:", historyErr);
        }
      } catch (err) {
        setError("Failed to generate insights. Please try again.");
        console.error("Error generating insights:", err);
      } finally {
        setInsightLoading(false);
      }
    }
  };

  const handleHistorySelect = async (item: InsightHistory) => {
    setInsight(item.insight);
    setSelectedText(item.text);
    setSelectedReference(item.reference);
    const insightId = parseInt(item.id);
    setCurrentInsightId(insightId);

    // Load chat messages for this insight
    try {
      const messages = await bibleService.getChatMessages(insightId);
      setChatMessages(messages);
    } catch (err) {
      console.error("Failed to load chat messages:", err);
      setChatMessages([]);
    }

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

  const handleAskQuestion = (text: string, reference: string) => {
    // Store passage info and open chat modal without creating the chat yet
    const passageInfo = { text, reference };
    setPendingChatPassage(passageInfo);
    setCurrentChatPassage(passageInfo);
    setCurrentChatId(null);
    setStandaloneChatMessages([]);
    setChatModalOpen(true);
  };

  const handleChatHistorySelect = async (chat: StandaloneChat) => {
    try {
      const messages = await bibleService.getStandaloneChatMessages(chat.id);
      setCurrentChatId(chat.id);
      setStandaloneChatMessages(messages);
      setPendingChatPassage(null); // Clear any pending passage
      // Set passage from the chat object
      if (chat.passage_text && chat.passage_reference) {
        setCurrentChatPassage({ text: chat.passage_text, reference: chat.passage_reference });
      } else {
        setCurrentChatPassage(null);
      }
      setChatModalOpen(true);
    } catch (err) {
      console.error("Failed to load chat messages:", err);
      setError("Failed to load chat. Please try again.");
    }
    
    // Close sidebar on mobile after selecting chat
    if (!isDesktop) {
      setSidebarOpen(false);
    }
  };

  const handleSendStandaloneChatMessage = async (message: string) => {
    // Create a temporary optimistic message
    const tempId = -Date.now();
    const tempMessage: StandaloneChatMessage = {
      id: tempId,
      role: "user",
      content: message,
      timestamp: Date.now(),
    };

    // Optimistically add the user's message
    setStandaloneChatMessages((prev) => [...prev, tempMessage]);
    setStandaloneChatLoading(true);
    setStandaloneChatStreamingMessage("");

    try {
      // If no chat exists yet, create it with the first message (now with streaming!)
      if (!currentChatId) {
        const chatId = await bibleService.createStandaloneChat(
          message,
          (token: string) => {
            // Accumulate tokens as they arrive
            setStandaloneChatStreamingMessage((prev) => prev + token);
          },
          pendingChatPassage?.text,
          pendingChatPassage?.reference
        );

        setCurrentChatId(chatId);
        setPendingChatPassage(null); // Clear pending passage flag after creating chat
        // Note: currentChatPassage is kept so the passage stays visible

        // After successful send, reload authoritative messages from server
        const messages = await bibleService.getStandaloneChatMessages(chatId);
        setStandaloneChatMessages(messages);
        setStandaloneChatStreamingMessage("");

        // Reload chat history
        const chats = await bibleService.getStandaloneChats(MAX_HISTORY_ITEMS);
        setChatHistory(chats);
      } else {
        // Send message to existing chat with streaming
        await bibleService.sendStandaloneChatMessage(
          currentChatId,
          message,
          (token: string) => {
            // Accumulate tokens as they arrive
            setStandaloneChatStreamingMessage((prev) => prev + token);
          }
        );

        // After successful send, reload authoritative messages from server
        const messages = await bibleService.getStandaloneChatMessages(currentChatId);
        setStandaloneChatMessages(messages);
        setStandaloneChatStreamingMessage("");

        // Update chat history to reflect new message
        const chats = await bibleService.getStandaloneChats(MAX_HISTORY_ITEMS);
        setChatHistory(chats);
      }
    } catch (err) {
      console.error("Failed to send chat message:", err);
      setError("Failed to send message. Please try again.");

      // Remove the optimistic temp message on failure
      setStandaloneChatMessages((prev) => prev.filter((m) => m.id !== tempId));
      setStandaloneChatStreamingMessage("");
    } finally {
      setStandaloneChatLoading(false);
    }
  };

  const handleDeleteChat = async (chatId: number) => {
    try {
      await bibleService.deleteStandaloneChat(chatId);
      setChatHistory((prev) => prev.filter((c) => c.id !== chatId));
      
      // Close modal if the deleted chat is currently open
      if (currentChatId === chatId) {
        setChatModalOpen(false);
        setCurrentChatId(null);
        setStandaloneChatMessages([]);
      }
    } catch (err) {
      console.error("Failed to delete chat:", err);
      setError("Failed to delete chat. Please try again.");
    }
  };

  const handleContinueChat = () => {
    // Close insights modal and open insight chat modal
    setInsightsModalOpen(false);
    setInsightChatModalOpen(true);
  };

  const handleSendInsightChatMessage = async (message: string) => {
    if (!currentInsightId || !insight) return;

    // Create a temporary optimistic message
    const tempId = -Date.now();
    const tempMessage: ChatMessage = {
      id: tempId,
      role: "user",
      content: message,
      timestamp: Date.now(),
    };

    // Optimistically add the user's message
    setChatMessages((prev) => [...prev, tempMessage]);
    setChatLoading(true);
    setChatStreamingMessage("");

    try {
      // Send message to server with streaming
      await bibleService.sendChatMessage(
        currentInsightId,
        message,
        selectedText,
        selectedReference,
        insight,
        (token: string) => {
          // Accumulate tokens as they arrive
          setChatStreamingMessage((prev) => prev + token);
        }
      );

      // After successful send, reload authoritative messages from server
      const messages = await bibleService.getChatMessages(currentInsightId);
      setChatMessages(messages);
      setChatStreamingMessage("");
    } catch (err) {
      console.error("Failed to send chat message:", err);
      setError("Failed to send message. Please try again.");

      // Remove the optimistic temp message on failure
      setChatMessages((prev) => prev.filter((m) => m.id !== tempId));
      setChatStreamingMessage("");
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="mobile-viewport-height flex flex-col bg-background">
      {/* Book tab for opening sidebar on mobile, only visible when sidebar is fully hidden */}
      {!sidebarOpen && sidebarFullyHidden && (
        <button
          aria-label="Open sidebar"
          onClick={() => setSidebarOpen(true)}
          className="fixed left-0 top-32 -translate-y-1/2 z-50 lg:hidden"
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
            className="p-5 text-secondary"
          >
            <Menu />
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
                <TabsList className="grid w-full grid-cols-4 flex-shrink-0">
                  <TabsTrigger value="search" className="flex items-center gap-1">
                    <SearchIcon size={16} className="sm:hidden" />
                    <span className="hidden sm:inline">Search</span>
                  </TabsTrigger>
                  <TabsTrigger
                    value="insights"
                    className="flex items-center gap-1"
                  >
                    <HistoryIcon size={16} className="sm:hidden" />
                    <span className="hidden sm:inline">Insights</span>
                  </TabsTrigger>
                  <TabsTrigger
                    value="chats"
                    className="flex items-center gap-1"
                  >
                    <MessageSquare size={16} className="sm:hidden" />
                    <span className="hidden sm:inline">Chats</span>
                  </TabsTrigger>
                  <TabsTrigger
                    value="settings"
                    className="flex items-center gap-1"
                  >
                    <SettingsIcon size={16} className="sm:hidden" />
                    <span className="hidden sm:inline">Settings</span>
                  </TabsTrigger>
                </TabsList>
                <TabsContent
                  value="search"
                  className="mt-4 flex-1 overflow-y-auto"
                >
                  <PassageSearch onSearch={handleSearch} />
                </TabsContent>
                <TabsContent
                  value="insights"
                  className="mt-4 flex-1 overflow-y-auto px-4"
                >
                  <InsightsHistoryComponent
                    history={insightsHistory}
                    onSelect={handleHistorySelect}
                    onClear={handleClearHistory}
                  />
                </TabsContent>
                <TabsContent
                  value="chats"
                  className="mt-4 flex-1 overflow-y-auto px-4"
                >
                  <ChatHistory
                    chats={chatHistory}
                    onSelect={handleChatHistorySelect}
                    onDelete={handleDeleteChat}
                  />
                </TabsContent>
                <TabsContent
                  value="settings"
                  className="mt-4 flex-1 overflow-y-auto px-4"
                >
                  <UserSettings
                    onError={(msg) => setError(msg)}
                    onSuccess={(msg) => setSuccessMessage(msg)}
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
        <main className="flex-1 flex flex-col overflow-hidden p-0 lg:p-6 min-h-0">
          {error && (
            <div className="mb-0 lg:mb-4 mx-0 lg:mx-auto flex items-center gap-2 rounded-none lg:rounded-lg border-x-0 lg:border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive max-w-4xl flex-shrink-0">
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
          {successMessage && (
            <div className="mb-0 lg:mb-4 mx-0 lg:mx-auto flex items-center gap-2 rounded-none lg:rounded-lg border-x-0 lg:border border-green-500/50 bg-green-500/10 p-3 text-sm text-green-700 dark:text-green-400 max-w-4xl flex-shrink-0">
              <CheckCircle size={20} />
              <span className="flex-1">{successMessage}</span>
              <button
                onClick={() => setSuccessMessage(null)}
                className="hover:opacity-70 transition-opacity"
              >
                <X size={20} />
              </button>
            </div>
          )}

          <div className="max-w-4xl lg:mx-auto flex-1 w-full min-h-0">
            <div className="bg-card rounded-none lg:rounded-lg shadow-none lg:shadow-sm border-0 lg:border h-full flex flex-col">
              <BibleReader
                passage={passage}
                onTextSelected={handleTextSelected}
                onAskQuestion={handleAskQuestion}
                onNavigate={handleNavigate}
                loading={loading}
              />
            </div>
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
        insightId={currentInsightId}
        chatMessages={chatMessages}
        onContinueChat={handleContinueChat}
      />

      {/* Definition Modal */}
      <DefinitionModal
        open={definitionModalOpen}
        onOpenChange={setDefinitionModalOpen}
        definition={definition}
        word={selectedWord}
        reference={selectedReference}
      />

      {/* Standalone Chat Modal */}
      <ChatModal
        open={chatModalOpen}
        onOpenChange={(open) => {
          setChatModalOpen(open);
          if (!open) {
            // Clear both pending and current passage when modal closes
            setPendingChatPassage(null);
            setCurrentChatPassage(null);
          }
        }}
        title="Chat"
        passageText={currentChatPassage?.text}
        passageReference={currentChatPassage?.reference}
        messages={standaloneChatMessages}
        onSendMessage={handleSendStandaloneChatMessage}
        loading={standaloneChatLoading}
        streamingMessage={standaloneChatStreamingMessage}
      />

      {/* Insight Chat Modal */}
      <ChatModal
        open={insightChatModalOpen}
        onOpenChange={setInsightChatModalOpen}
        title="Continue Chat"
        subtitle={selectedReference}
        messages={chatMessages}
        onSendMessage={handleSendInsightChatMessage}
        loading={chatLoading}
        streamingMessage={chatStreamingMessage}
      />

      {/* Loading overlays */}
      {insightLoading && <LoadingOverlay message="Generating insights..." />}
      {definitionLoading && <LoadingOverlay message="Generating definition..." />}
      {standaloneChatLoading && !chatModalOpen && <LoadingOverlay message="Starting chat..." />}

      {/* PWA Install Prompt */}
      <InstallPrompt />
    </div>
  );
}

export default App;
