import { useEffect } from "react";
import { useModal } from "../context/ModalContext";
import InsightsModal from "./InsightsModal";
import DefinitionModal from "./DefinitionModal";
import ChatModal from "./ChatModal";
import DeviceLinkModal from "./DeviceLinkModal";
import LandingPageModal, { useLandingModal } from "./LandingPageModal";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyProps = any;

interface ModalManagerProps {
  biblePassage: AnyProps;
  insightGen: AnyProps;
  standaloneChat: AnyProps;
  insightChat: AnyProps;
  devices: AnyProps;
  setDevices: (devices: AnyProps) => void;
  // loadDevices removed as it was unused in logic here, passed to sidebar in App
  setError: (error: string | null) => void;
  chatError: string | null;
  setChatError: (error: string | null) => void;
  insightChatError: string | null;
  setInsightChatError: (error: string | null) => void;
  setSuccessMessage: (msg: string | null) => void;
  handleSendStandaloneChatMessage: (msg: string) => Promise<void>;
  handleSendInsightChatMessage: (msg: string) => Promise<void>;
  handleContinueChat: () => void;
}

export default function ModalManager({
  biblePassage,
  insightGen,
  standaloneChat,
  insightChat,
  devices,
  setDevices,
  setError,
  chatError,
  setChatError,
  insightChatError,
  setInsightChatError,
  setSuccessMessage,
  handleSendStandaloneChatMessage,
  handleSendInsightChatMessage,
  handleContinueChat,
}: ModalManagerProps) {
  const { openModals, closeModal, openModal } = useModal();
  const shouldShowLandingModal = useLandingModal();

  useEffect(() => {
    if (shouldShowLandingModal) {
      openModal("landing");
    }
  }, [shouldShowLandingModal, openModal]);

  return (
    <>
      {/* Insights Modal */}
      <InsightsModal
        open={openModals.insights}
        onOpenChange={(open) =>
          open ? openModal("insights") : closeModal("insights")
        }
        insight={insightGen.insight}
        selectedText={insightGen.selectedText}
        reference={insightGen.selectedReference}
        insightId={insightGen.currentInsightId}
        chatMessages={insightChat.messages}
        onContinueChat={handleContinueChat}
      />

      {/* Definition Modal */}
      <DefinitionModal
        open={openModals.definition}
        onOpenChange={(open) =>
          open ? openModal("definition") : closeModal("definition")
        }
        definition={insightGen.definition}
        word={insightGen.selectedWord}
        reference={insightGen.selectedReference}
      />

      {/* Standalone Chat Modal */}
      <ChatModal
        open={openModals.chat}
        onOpenChange={(open) => {
          if (open) {
            openModal("chat");
          } else {
            closeModal("chat");
            standaloneChat.clearChat();
            setChatError(null);
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
        error={chatError}
      />

      {/* Insight Chat Modal */}
      <ChatModal
        open={openModals.insightChat}
        onOpenChange={(open) => {
          if (open) {
            openModal("insightChat");
          } else {
            closeModal("insightChat");
            setInsightChatError(null);
          }
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
        error={insightChatError}
      />

      {/* Device Link Modal */}
      <DeviceLinkModal
        open={openModals.deviceLink}
        onOpenChange={(open) =>
          open ? openModal("deviceLink") : closeModal("deviceLink")
        }
        devices={devices}
        onDevicesChange={setDevices}
        onSuccess={(msg) => setSuccessMessage(msg)}
        onError={(msg) => setError(msg)}
      />

      {/* Landing Page Modal */}
      <LandingPageModal
        open={openModals.landing}
        onOpenChange={(open) =>
          open ? openModal("landing") : closeModal("landing")
        }
      />
    </>
  );
}
