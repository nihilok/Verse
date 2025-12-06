import React, { useState, useEffect, useRef } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ChatMessage } from "../types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import MarkdownLink, { createMarkdownLinkWithCallback } from "./MarkdownLink";

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => Promise<void>;
  loading: boolean;
  streamingMessage?: string;
  onNavigate?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  loading,
  streamingMessage,
  onNavigate,
}) => {
  const [inputValue, setInputValue] = useState("");
  const [isMobile, setIsMobile] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Create link component with navigation callback if provided
  const LinkComponent = React.useMemo(
    () =>
      onNavigate ? createMarkdownLinkWithCallback(onNavigate) : MarkdownLink,
    [onNavigate],
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to get accurate scrollHeight
    textarea.style.height = "auto";

    // Calculate the line height (approximately 24px for text-base)
    const lineHeight = 24;
    const maxRows = 6;
    const maxHeight = lineHeight * maxRows;

    // Set height based on content, but cap at max height
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${newHeight}px`;
  };

  useEffect(() => {
    // Check if device is mobile (screen width < 768px)
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);

    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const message = inputValue;
    setInputValue("");

    // Reset textarea height after sending
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    await onSendMessage(message);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    adjustTextareaHeight();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      // Mobile: Enter adds newline, Shift+Enter sends
      // Desktop: Enter sends, Shift+Enter adds newline
      const shouldSend = isMobile ? e.shiftKey : !e.shiftKey;

      if (shouldSend) {
        e.preventDefault();
        handleSubmit(e);
      }
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto pb-2 space-y-4 scrollbar-thin min-h-0 relative chat-messages-container">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <p className="text-sm">Ask a question about this passage.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[95%] md:max-w-[85%] rounded-lg px-4 py-2 chat-message ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                {msg.role === "assistant" ? (
                  <div className="prose prose-sm llm-response dark:prose-invert max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{ a: LinkComponent }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
            </div>
          ))
        )}
        {streamingMessage && (
          <div className="flex justify-start">
            <div className="max-w-[95%] md:max-w-[85%] rounded-lg px-4 py-2 bg-muted">
              <div className="prose prose-sm llm-response dark:prose-invert max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{ a: LinkComponent }}
                >
                  {streamingMessage}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        )}
        {loading && !streamingMessage && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-4 py-2 flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              <span className="text-sm text-muted-foreground">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t p-4 flex-shrink-0">
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <Textarea
            ref={textareaRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            aria-label="Ask a question about the passage"
            disabled={loading}
            rows={1}
            className="flex-1 min-h-0 resize-none"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!inputValue.trim() || loading}
            aria-label="Send message"
          >
            {loading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <Send size={20} />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
