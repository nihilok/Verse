import React from "react";
import { MessageCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import ChatInterface from "./ChatInterface";
import type { ChatMessage, StandaloneChatMessage } from "../types";

interface ChatModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  subtitle?: string;
  passageText?: string;
  passageReference?: string;
  messages: ChatMessage[] | StandaloneChatMessage[];
  onSendMessage: (message: string) => Promise<void>;
  loading: boolean;
}

const ChatModal: React.FC<ChatModalProps> = ({
  open,
  onOpenChange,
  title = "Chat",
  subtitle,
  passageText,
  passageReference,
  messages,
  onSendMessage,
  loading,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
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
        {passageText && passageReference && (
          <div className="mb-2 p-4 rounded-lg bg-muted/50 border border-border">
            <h3 className="font-semibold text-sm mb-2 text-primary">
              {passageReference}
            </h3>
            <p className="italic text-sm leading-relaxed">"{passageText}"</p>
          </div>
        )}

        <div className="flex-1 overflow-hidden flex flex-col min-h-0">
          <ChatInterface
            messages={messages}
            onSendMessage={onSendMessage}
            loading={loading}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ChatModal;
