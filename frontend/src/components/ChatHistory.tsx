import React, { useEffect } from "react";
import { MessageCircle, Trash2, Calendar } from "lucide-react";
import type { StandaloneChat } from "../types";
import { Button } from "@/components/ui/button";
import { useChatHistory } from "../hooks/useChatHistory";
import { HistorySkeleton } from "./HistorySkeleton";

interface ChatHistoryProps {
  onSelect: (chat: StandaloneChat) => void;
  onError?: (msg: string) => void;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ onSelect, onError }) => {
  const { chatHistory, loadHistory, deleteChat, loading } = useChatHistory();

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleDelete = async (chatId: number) => {
    try {
      await deleteChat(chatId);
    } catch {
      onError?.("Failed to delete chat. Please try again.");
    }
  };

  const chats = chatHistory;
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="flex items-center justify-between flex-shrink-0">
        <h3 className="font-semibold flex items-center gap-2">
          <MessageCircle size={20} />
          Chat History
        </h3>
      </div>

      {loading ? (
        <HistorySkeleton />
      ) : chats.length === 0 ? (
        <div className="text-center text-muted-foreground py-8">
          <MessageCircle size={48} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">No chat history yet</p>
          <p className="text-xs mt-1">
            Start a chat by selecting text and clicking "Ask a Question"
          </p>
        </div>
      ) : (
        <div className="space-y-2 flex-1 overflow-y-auto min-h-0">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className="group relative rounded-lg border border-border bg-card p-3 hover:bg-accent transition-colors cursor-pointer"
              onClick={() => onSelect(chat)}
            >
              <div className="flex items-start gap-2">
                <MessageCircle
                  size={16}
                  className="mt-0.5 text-primary flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium truncate mb-1">
                    {chat.title || "Untitled Chat"}
                  </h4>
                  {chat.passage_reference && (
                    <p className="text-xs text-muted-foreground mb-1">
                      {chat.passage_reference}
                    </p>
                  )}
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Calendar size={12} />
                    <span>{formatDate(chat.updated_at)}</span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="opacity-0 group-hover:opacity-100 transition-opacity h-7 w-7"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm("Are you sure you want to delete this chat?")) {
                      handleDelete(chat.id);
                    }
                  }}
                >
                  <Trash2 size={14} />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatHistory;
