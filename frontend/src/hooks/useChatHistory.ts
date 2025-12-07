import { useState, useCallback } from "react";
import { bibleService } from "../services/api";
import { StandaloneChat } from "../types";
import { useLoadOnce } from "./useLoadOnce";

const MAX_HISTORY_ITEMS = 50;

export function useChatHistory() {
  const [chatHistory, setChatHistory] = useState<StandaloneChat[]>([]);
  const { loading, executeLoad } = useLoadOnce();

  const loadHistory = useCallback(async () => {
    await executeLoad(async () => {
      try {
        const chats = await bibleService.getStandaloneChats(MAX_HISTORY_ITEMS);
        setChatHistory(chats);
      } catch (e) {
        console.error("Failed to load chat history:", e);
        throw e;
      }
    });
  }, [executeLoad]);

  const reloadHistory = useCallback(async () => {
    try {
      const chats = await bibleService.getStandaloneChats(MAX_HISTORY_ITEMS);
      setChatHistory(chats);
    } catch (e) {
      console.error("Failed to reload chat history:", e);
    }
  }, []);

  const deleteChat = useCallback(async (chatId: number) => {
    try {
      await bibleService.deleteStandaloneChat(chatId);
      setChatHistory((prev) => prev.filter((c) => c.id !== chatId));
    } catch (err) {
      console.error("Failed to delete chat:", err);
      throw err;
    }
  }, []);

  return {
    chatHistory,
    loadHistory,
    reloadHistory,
    deleteChat,
    loading,
  };
}
