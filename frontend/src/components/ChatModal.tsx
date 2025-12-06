import React from "react";
import { MessageCircle } from "lucide-react";
import { Link } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import ChatInterface from "./ChatInterface";
import type { ChatMessage, StandaloneChatMessage } from "../types";
import { generatePassageURL } from "@/lib/urlParser";

interface ChatModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  subtitle?: string;
  passageText?: string;
  passageReference?: string;
  passageParams?: {
    book: string;
    chapter: number;
    verseStart?: number;
    verseEnd?: number;
    translation?: string;
  };
  messages: ChatMessage[] | StandaloneChatMessage[];
  onSendMessage: (message: string) => Promise<void>;
  loading: boolean;
  streamingMessage?: string;
  error?: string | null;
}

const ChatModal: React.FC<ChatModalProps> = ({
  open,
  onOpenChange,
  title = "Chat",
  subtitle,
  passageText,
  passageReference,
  passageParams,
  messages,
  onSendMessage,
  loading,
  streamingMessage,
  error,
}) => {
  // Format reference with verse range if available
  const formattedReference = React.useMemo(() => {
    if (!passageParams) return passageReference;

    const { book, chapter, verseStart, verseEnd, translation } = passageParams;
    let ref = `${book} ${chapter}`;

    if (verseStart && verseEnd && verseStart !== verseEnd) {
      ref += `:${verseStart}-${verseEnd}`;
    } else if (verseStart) {
      ref += `:${verseStart}`;
    }

    if (translation) {
      ref += ` (${translation})`;
    }

    return ref;
  }, [passageParams, passageReference]);

  // Generate passage URL if we have params
  const passageUrl = React.useMemo(() => {
    if (!passageParams) return null;
    return generatePassageURL(passageParams);
  }, [passageParams]);

  const handleReferenceClick = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col gap-2">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            <MessageCircle size={28} className="text-primary" />
            {title}
          </DialogTitle>
          {subtitle && (
            <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
          )}
        </DialogHeader>

        {/* Passage quote - shown at top if provided */}
        {passageText && (formattedReference || passageReference) && (
          <div className="p-4 rounded-lg bg-muted/50 border border-border">
            {passageUrl ? (
              <Link
                to={passageUrl}
                onClick={handleReferenceClick}
                className="font-semibold text-sm mb-2 text-primary hover:underline block"
              >
                {formattedReference}
              </Link>
            ) : (
              <h3 className="font-semibold text-sm mb-2 text-primary">
                {formattedReference}
              </h3>
            )}
            <p className="italic text-sm leading-relaxed">"{passageText}"</p>
          </div>
        )}

        <div className="flex-1 overflow-hidden flex flex-col min-h-0">
          <ChatInterface
            messages={messages}
            onSendMessage={onSendMessage}
            loading={loading}
            streamingMessage={streamingMessage}
            onNavigate={() => onOpenChange(false)}
            error={error}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ChatModal;
