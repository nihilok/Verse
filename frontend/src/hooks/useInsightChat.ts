import { useState, useCallback } from "react";
import { bibleService } from "../services/api";
import { ChatMessage, Insight } from "../types";

export function useInsightChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<string>("");

  const loadMessages = useCallback(async (insightId: number) => {
    try {
      const chatMessages = await bibleService.getChatMessages(insightId);
      setMessages(chatMessages);
    } catch (err) {
      console.error("Failed to load chat messages:", err);
      setMessages([]);
    }
  }, []);

  const sendMessage = useCallback(
    async (
      insightId: number,
      message: string,
      selectedText: string,
      selectedReference: string,
      insight: Insight,
    ) => {
      const tempId = -Date.now();
      const tempMessage: ChatMessage = {
        id: tempId,
        role: "user",
        content: message,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, tempMessage]);
      setLoading(true);
      setStreamingMessage("");

      try {
        await bibleService.sendChatMessage(
          insightId,
          message,
          selectedText,
          selectedReference,
          insight,
          (token: string) => {
            setStreamingMessage((prev) => prev + token);
          },
        );

        const chatMessages = await bibleService.getChatMessages(insightId);
        setMessages(chatMessages);
        setStreamingMessage("");
      } catch (err) {
        setMessages((prev) => prev.filter((m) => m.id !== tempId));
        setStreamingMessage("");
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  return {
    messages,
    loading,
    streamingMessage,
    loadMessages,
    sendMessage,
    setMessages,
  };
}
