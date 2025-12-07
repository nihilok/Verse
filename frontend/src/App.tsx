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
import DeviceLinkModal from "./components/DeviceLinkModal";
import InstallPrompt from "./components/InstallPrompt";
import UpdatePrompt from "./components/UpdatePrompt";
import LoadingOverlay from "./components/LoadingOverlay";
import { ModeToggle } from "./components/mode-toggle";
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
} from "./components/ui/sidebar";
import { Button } from "./components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { InsightHistory, StandaloneChat } from "./types";
import { useBiblePassage } from "./hooks/useBiblePassage";
import { useInsightGeneration } from "./hooks/useInsightGeneration";
import { useStandaloneChat } from "./hooks/useStandaloneChat";
import { useInsightChat } from "./hooks/useInsightChat";
import { useDevices } from "./hooks/useDevices";
import "./App.css";

function getUsageLimitErrorMessage(err: unknown): string | null {
  if (
    err &&
    typeof err === "object" &&
    "response" in err &&
    err.response &&
    typeof err.response === "object" &&
    "status" in err.response &&
    err.response.status === 429
  ) {
    const detail =
      "data" in err.response &&
      err.response.data &&
      typeof err.response.data === "object" &&
      "detail" in err.response.data
        ? err.response.data.detail
        : null;
    if (detail && typeof detail === "object" && "message" in detail) {
      return (
        (detail.message as string) ||
        "Daily limit reached. Please try again tomorrow or upgrade to pro."
      );
    }
    return "Daily limit reached. Please try again tomorrow or upgrade to pro.";
  }
  return null;
}

function App() {
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarFullyHidden, setSidebarFullyHidden] = useState(false);
  const [insightsModalOpen, setInsightsModalOpen] = useState(false);
  const [definitionModalOpen, setDefinitionModalOpen] = useState(false);
  const [chatModalOpen, setChatModalOpen] = useState(false);
  const [insightChatModalOpen, setInsightChatModalOpen] = useState(false);
  const [deviceLinkModalOpen, setDeviceLinkModalOpen] = useState(false);
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 1024);

  // Custom hooks
  const biblePassage = useBiblePassage();
  const insightGen = useInsightGeneration();
  const standaloneChat = useStandaloneChat();
  const insightChat = useInsightChat();
  const { devices, setDevices, loadDevices } = useDevices();

  useEffect(() => {
    const handleResize = () => {
      const desktop = window.innerWidth >= 1024;
      setIsDesktop(desktop);
      if (desktop) {
        setSidebarOpen(true);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const sidebarX = useMotionValue(0);

  useMotionValueEvent(sidebarX, "change", (latest) => {
    setSidebarFullyHidden(latest <= -320);
  });

  useEffect(() => {
    if (!biblePassage.loadFromURL()) {
      biblePassage.loadLastViewedPassage();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = async (
    book: string,
    chapter: number,
    verseStart?: number,
    verseEnd?: number,
    translation: string = "WEB",
  ) => {
    setError(null);
    try {
      await biblePassage.handleSearch(
        book,
        chapter,
        verseStart,
        verseEnd,
        translation,
      );
      if (!isDesktop) {
        setSidebarOpen(false);
      }
    } catch (err) {
      setError(
        "Failed to load passage. Please check your input and try again.",
      );
      console.error("Error loading passage:", err);
    }
  };

  const handleTextSelected = async (
    text: string,
    reference: string,
    isSingleWord: boolean,
    verseText?: string,
  ) => {
    if (isSingleWord && !verseText) {
      setError(
        "Unable to find the verse containing this word. Please try selecting the full verse.",
      );
      return;
    }

    setError(null);

    try {
      if (isSingleWord && verseText) {
        await insightGen.generateDefinition(text, verseText, reference);
        setDefinitionModalOpen(true);
      } else {
        await insightGen.generateInsight(text, reference);
        setInsightsModalOpen(true);
        await insightChat.loadMessages(insightGen.currentInsightId!);
      }
    } catch (err) {
      const usageLimitError = getUsageLimitErrorMessage(err);
      if (usageLimitError) {
        setError(usageLimitError);
      } else {
        setError(
          isSingleWord
            ? "Failed to generate definition. Please try again."
            : "Failed to generate insights. Please try again.",
        );
      }
      console.error("Error generating content:", err);
    }
  };

  const handleHistorySelect = async (item: InsightHistory) => {
    await insightGen.loadInsightFromHistory(
      parseInt(item.id),
      item.text,
      item.reference,
      item.insight,
    );
    await insightChat.loadMessages(parseInt(item.id));
    setInsightsModalOpen(true);
  };

  const handleAskQuestion = (
    text: string,
    _reference: string,
    verseStart?: number,
    verseEnd?: number,
  ) => {
    const start = verseStart || biblePassage.highlightVerseStart;
    const end = verseEnd || biblePassage.highlightVerseEnd;

    let fullReference = `${biblePassage.currentBook} ${biblePassage.currentChapter}`;
    if (start && end && start !== end) {
      fullReference += `:${start}-${end}`;
    } else if (start) {
      fullReference += `:${start}`;
    }
    if (biblePassage.currentTranslation) {
      fullReference += ` (${biblePassage.currentTranslation})`;
    }

    standaloneChat.startNewChat(text, fullReference, {
      book: biblePassage.currentBook,
      chapter: biblePassage.currentChapter,
      verseStart: start,
      verseEnd: end,
      translation: biblePassage.currentTranslation,
    });
    setChatModalOpen(true);
  };

  const handleChatHistorySelect = async (chat: StandaloneChat) => {
    try {
      await standaloneChat.loadExistingChat(
        chat.id,
        chat.passage_text || "",
        chat.passage_reference || "",
      );
      setChatModalOpen(true);
      if (!isDesktop) {
        setSidebarOpen(false);
      }
    } catch (err) {
      console.error("Failed to load chat messages:", err);
      setError("Failed to load chat. Please try again.");
    }
  };

  const handleSendStandaloneChatMessage = async (message: string) => {
    try {
      await standaloneChat.sendMessage(message);
    } catch (err) {
      console.error("Failed to send chat message:", err);
      const usageLimitError = getUsageLimitErrorMessage(err);
      if (usageLimitError) {
        setError(usageLimitError);
      } else {
        setError("Failed to send message. Please try again.");
      }
    }
  };

  const handleContinueChat = () => {
    setInsightsModalOpen(false);
    setInsightChatModalOpen(true);
  };

  const handleSendInsightChatMessage = async (message: string) => {
    if (!insightGen.currentInsightId || !insightGen.insight) return;

    try {
      await insightChat.sendMessage(
        insightGen.currentInsightId,
        message,
        insightGen.selectedText,
        insightGen.selectedReference,
        insightGen.insight,
      );
    } catch (err) {
      console.error("Failed to send chat message:", err);
      const usageLimitError = getUsageLimitErrorMessage(err);
      if (usageLimitError) {
        setError(usageLimitError);
      } else {
        setError("Failed to send message. Please try again.");
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
                  <TabsTrigger
                    value="search"
                    className="flex items-center gap-1"
                  >
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
                    onSelect={handleHistorySelect}
                    onError={(msg) => setError(msg)}
                  />
                </TabsContent>
                <TabsContent
                  value="chats"
                  className="mt-4 flex-1 overflow-y-auto px-4"
                >
                  <ChatHistory
                    onSelect={handleChatHistorySelect}
                    onError={(msg) => setError(msg)}
                  />
                </TabsContent>
                <TabsContent
                  value="settings"
                  className="mt-4 flex-1 overflow-y-auto px-4"
                >
                  <UserSettings
                    onError={(msg) => setError(msg)}
                    onSuccess={(msg) => setSuccessMessage(msg)}
                    onOpenDeviceLinking={() => {
                      loadDevices();
                      setDeviceLinkModalOpen(true);
                    }}
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
                passage={biblePassage.passage}
                onTextSelected={handleTextSelected}
                onAskQuestion={handleAskQuestion}
                onNavigate={biblePassage.handleNavigate}
                onTranslationChange={biblePassage.handleTranslationChange}
                loading={biblePassage.loading}
                highlightVerseStart={biblePassage.highlightVerseStart}
                highlightVerseEnd={biblePassage.highlightVerseEnd}
              />
            </div>
          </div>
        </main>
      </div>

      {/* Insights Modal */}
      <InsightsModal
        open={insightsModalOpen}
        onOpenChange={setInsightsModalOpen}
        insight={insightGen.insight}
        selectedText={insightGen.selectedText}
        reference={insightGen.selectedReference}
        insightId={insightGen.currentInsightId}
        chatMessages={insightChat.messages}
        onContinueChat={handleContinueChat}
      />

      {/* Definition Modal */}
      <DefinitionModal
        open={definitionModalOpen}
        onOpenChange={setDefinitionModalOpen}
        definition={insightGen.definition}
        word={insightGen.selectedWord}
        reference={insightGen.selectedReference}
      />

      {/* Standalone Chat Modal */}
      <ChatModal
        open={chatModalOpen}
        onOpenChange={(open) => {
          setChatModalOpen(open);
          if (!open) {
            standaloneChat.clearChat();
            setError(null);
          }
        }}
        title="Chat"
        passageText={standaloneChat.currentChatPassage?.text}
        passageReference={standaloneChat.currentChatPassage?.reference}
        passageParams={standaloneChat.currentChatPassage?.params}
        messages={standaloneChat.messages}
        onSendMessage={handleSendStandaloneChatMessage}
        loading={standaloneChat.loading}
        streamingMessage={standaloneChat.streamingMessage}
        error={error}
      />

      {/* Insight Chat Modal */}
      <ChatModal
        open={insightChatModalOpen}
        onOpenChange={(open) => {
          setInsightChatModalOpen(open);
          if (!open) setError(null);
        }}
        title="Continue Chat"
        subtitle={insightGen.selectedReference}
        passageText={insightGen.selectedText}
        passageReference={insightGen.selectedReference}
        passageParams={{
          book: biblePassage.currentBook,
          chapter: biblePassage.currentChapter,
          verseStart: biblePassage.highlightVerseStart,
          verseEnd: biblePassage.highlightVerseEnd,
          translation: biblePassage.currentTranslation,
        }}
        messages={insightChat.messages}
        onSendMessage={handleSendInsightChatMessage}
        loading={insightChat.loading}
        streamingMessage={insightChat.streamingMessage}
        error={error}
      />

      {/* Device Link Modal */}
      <DeviceLinkModal
        open={deviceLinkModalOpen}
        onOpenChange={setDeviceLinkModalOpen}
        devices={devices}
        onDevicesChange={setDevices}
        onSuccess={(msg) => setSuccessMessage(msg)}
        onError={(msg) => setError(msg)}
      />

      {/* Loading overlays */}
      {insightGen.insightLoading && (
        <LoadingOverlay message="Generating insights..." />
      )}
      {insightGen.definitionLoading && (
        <LoadingOverlay message="Generating definition..." />
      )}
      {standaloneChat.loading && !chatModalOpen && (
        <LoadingOverlay message="Starting chat..." />
      )}

      {/* PWA Install Prompt */}
      <InstallPrompt />

      {/* PWA Update Prompt */}
      <UpdatePrompt />
    </div>
  );
}

export default App;
