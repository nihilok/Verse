import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import BibleReader from "./components/BibleReader";
import InstallPrompt from "./components/InstallPrompt";
import UpdatePrompt from "./components/UpdatePrompt";
import LoadingOverlay from "./components/LoadingOverlay";
import { UIProvider, useUI } from "./context/UIContext";
import { ModalProvider, useModal } from "./context/ModalContext";
import ModalManager from "./components/ModalManager";
import RootLayout from "./layouts/RootLayout";
import MainSidebar from "./components/MainSidebar";
import { InsightHistory, StandaloneChat } from "./types";
import { useBiblePassage } from "./hooks/useBiblePassage";
import { useInsightGeneration } from "./hooks/useInsightGeneration";
import { useStandaloneChat } from "./hooks/useStandaloneChat";
import { useInsightChat } from "./hooks/useInsightChat";
import { useDevices } from "./hooks/useDevices";
import {
  loadFontSize,
  loadFontFamily,
  type FontSize,
  type FontFamily,
} from "./lib/storage";
import "./App.css";

function getApiErrorMessage(err: unknown): string | null {
  if (err instanceof Error) {
    const errorType = (err as Error & { errorType?: string }).errorType;
    if (errorType === "auth_error") {
      return err.message;
    }
  }
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
  const [searchParams] = useSearchParams();
  const [chatError, setChatError] = useState<string | null>(null);
  const [insightChatError, setInsightChatError] = useState<string | null>(null);
  const [fontSize, setFontSize] = useState<FontSize>(loadFontSize);
  const [fontFamily, setFontFamily] = useState<FontFamily>(loadFontFamily);

  // Custom hooks
  const biblePassage = useBiblePassage();
  const insightGen = useInsightGeneration();
  const standaloneChat = useStandaloneChat();
  const insightChat = useInsightChat();
  const { devices, setDevices, loadDevices } = useDevices();

  const { loadFromURL, loadLastViewedPassage } = biblePassage;

  useEffect(() => {
    if (!loadFromURL()) {
      loadLastViewedPassage();
    }
  }, [searchParams, loadFromURL, loadLastViewedPassage]);

  // Handlers need access to hooks.
  // We will define them in AppContent or pass them down.
  // Since AppContent is inside providers, better to keep logic there or pass hooks result.

  return (
    <UIProvider>
      <ModalProvider>
        <AppContent
          biblePassage={biblePassage}
          insightGen={insightGen}
          standaloneChat={standaloneChat}
          insightChat={insightChat}
          devices={devices}
          setDevices={setDevices}
          loadDevices={loadDevices}
          chatError={chatError}
          setChatError={setChatError}
          insightChatError={insightChatError}
          setInsightChatError={setInsightChatError}
          fontSize={fontSize}
          setFontSize={setFontSize}
          fontFamily={fontFamily}
          setFontFamily={setFontFamily}
        />
      </ModalProvider>
    </UIProvider>
  );
}

function AppContent({
  biblePassage,
  insightGen,
  standaloneChat,
  insightChat,
  devices,
  setDevices,
  loadDevices,
  chatError,
  setChatError,
  insightChatError,
  setInsightChatError,
  fontSize,
  setFontSize,
  fontFamily,
  setFontFamily,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
}: any) {
  const { setSidebarOpen, isDesktop } = useUI();
  const { openModal, closeModal, isModalOpen } = useModal();

  const handleSearch = async (
    book: string,
    chapter: number,
    verseStart?: number,
    verseEnd?: number,
    translation: string = "WEB",
  ) => {
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
      toast.error(
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
      toast.error(
        "Unable to find the verse containing this word. Please try selecting the full verse.",
      );
      return;
    }

    try {
      if (isSingleWord && verseText) {
        await insightGen.generateDefinition(text, verseText, reference);
        openModal("definition");
      } else {
        await insightGen.generateInsight(text, reference);
        openModal("insights");
        if (insightGen.currentInsightId) {
          await insightChat.loadMessages(insightGen.currentInsightId);
        } else {
          toast.error(
            "Failed to load insight messages. Insight ID was not set. Please try again.",
          );
          console.error("Insight ID is null after generateInsight");
        }
      }
    } catch (err) {
      toast.error(
        getApiErrorMessage(err) ??
          (isSingleWord
            ? "Failed to generate definition. Please try again."
            : "Failed to generate insights. Please try again."),
      );
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
    openModal("insights");
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
    openModal("chat");
  };

  const handleChatHistorySelect = async (chat: StandaloneChat) => {
    try {
      await standaloneChat.loadExistingChat(
        chat.id,
        chat.passage_text || "",
        chat.passage_reference || "",
      );
      openModal("chat");
      if (!isDesktop) {
        setSidebarOpen(false);
      }
    } catch (err) {
      console.error("Failed to load chat messages:", err);
      toast.error("Failed to load chat. Please try again.");
    }
  };

  const handleSendStandaloneChatMessage = async (message: string) => {
    try {
      await standaloneChat.sendMessage(message);
    } catch (err) {
      console.error("Failed to send chat message:", err);
      const apiError = getApiErrorMessage(err);
      setChatError(apiError ?? "Failed to send message. Please try again.");
    }
  };

  const handleContinueChat = () => {
    closeModal("insights");
    openModal("insightChat");
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
      const apiError = getApiErrorMessage(err);
      setInsightChatError(
        apiError ?? "Failed to send message. Please try again.",
      );
    }
  };

  return (
    <RootLayout
      sidebar={
        <MainSidebar
          onSearch={handleSearch}
          onHistorySelect={handleHistorySelect}
          onChatHistorySelect={handleChatHistorySelect}
          onError={(msg: string) => toast.error(msg)}
          onSuccess={(msg: string) => toast.success(msg)}
          onOpenDeviceLinking={() => {
            loadDevices();
            openModal("deviceLink");
          }}
          onFontSizeChange={setFontSize}
          onFontFamilyChange={setFontFamily}
        />
      }
    >
      <div className="max-w-4xl lg:mx-auto flex-1 w-full min-h-0 p-0 lg:p-6">
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
            fontSize={fontSize}
            fontFamily={fontFamily}
          />
        </div>
      </div>

      <ModalManager
        biblePassage={biblePassage}
        insightGen={insightGen}
        standaloneChat={standaloneChat}
        insightChat={insightChat}
        devices={devices}
        setDevices={setDevices}
        setError={(msg: string | null) => {
          if (msg) toast.error(msg);
        }}
        chatError={chatError}
        setChatError={setChatError}
        insightChatError={insightChatError}
        setInsightChatError={setInsightChatError}
        setSuccessMessage={(msg: string | null) => {
          if (msg) toast.success(msg);
        }}
        handleSendStandaloneChatMessage={handleSendStandaloneChatMessage}
        handleSendInsightChatMessage={handleSendInsightChatMessage}
        handleContinueChat={handleContinueChat}
      />

      {/* Loading overlays */}
      {insightGen.insightLoading && (
        <LoadingOverlay message="Generating insights..." />
      )}
      {insightGen.definitionLoading && (
        <LoadingOverlay message="Generating definition..." />
      )}
      {standaloneChat.loading && !isModalOpen("chat") && (
        <LoadingOverlay message="Starting chat..." />
      )}

      {/* PWA Install Prompt */}
      <InstallPrompt />

      {/* PWA Update Prompt */}
      <UpdatePrompt />
    </RootLayout>
  );
}

export default App;
