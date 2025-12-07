import { useState, useCallback } from "react";
import { bibleService } from "../services/api";
import { StandaloneChatMessage } from "../types";

export function useStandaloneChat() {
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);
  const [currentChatPassage, setCurrentChatPassage] = useState<{
    text: string;
    reference: string;
    params?: {
      book: string;
      chapter: number;
      verseStart?: number;
      verseEnd?: number;
      translation?: string;
    };
  } | null>(null);
  const [messages, setMessages] = useState<StandaloneChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<string>("");
  const [pendingChatPassage, setPendingChatPassage] = useState<{
    text: string;
    reference: string;
    params?: {
      book: string;
      chapter: number;
      verseStart?: number;
      verseEnd?: number;
      translation?: string;
    };
  } | null>(null);

  const startNewChat = useCallback(
    (
      text: string,
      reference: string,
      params?: {
        book: string;
        chapter: number;
        verseStart?: number;
        verseEnd?: number;
        translation?: string;
      },
    ) => {
      const passageInfo = { text, reference, params };
      setPendingChatPassage(passageInfo);
      setCurrentChatPassage(passageInfo);
      setCurrentChatId(null);
      setMessages([]);
    },
    [],
  );

  const loadExistingChat = useCallback(
    async (chatId: number, passageText: string, passageReference: string) => {
      try {
        const chatMessages =
          await bibleService.getStandaloneChatMessages(chatId);
        setCurrentChatId(chatId);
        setMessages(chatMessages);
        setPendingChatPassage(null);

        const refMatch = passageReference.match(
          /^(.+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?\s*(?:\(([^)]+)\))?$/,
        );

        let params = undefined;
        if (refMatch) {
          const [, book, chapter, verseStart, verseEnd, translation] = refMatch;
          params = {
            book: book.trim(),
            chapter: parseInt(chapter),
            verseStart: verseStart ? parseInt(verseStart) : undefined,
            verseEnd: verseEnd ? parseInt(verseEnd) : undefined,
            translation: translation || undefined,
          };
        }

        setCurrentChatPassage({
          text: passageText,
          reference: passageReference,
          params,
        });
      } catch (err) {
        console.error("Failed to load chat messages:", err);
        throw err;
      }
    },
    [],
  );

  const sendMessage = useCallback(
    async (message: string) => {
      const tempId = -Date.now();
      const tempMessage: StandaloneChatMessage = {
        id: tempId,
        role: "user",
        content: message,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, tempMessage]);
      setLoading(true);
      setStreamingMessage("");

      try {
        if (!currentChatId) {
          let fullReference = pendingChatPassage?.reference;
          if (pendingChatPassage?.params) {
            const { book, chapter, verseStart, verseEnd, translation } =
              pendingChatPassage.params;
            fullReference = `${book} ${chapter}`;
            if (verseStart && verseEnd && verseStart !== verseEnd) {
              fullReference += `:${verseStart}-${verseEnd}`;
            } else if (verseStart) {
              fullReference += `:${verseStart}`;
            }
            if (translation) {
              fullReference += ` (${translation})`;
            }
          }

          const chatId = await bibleService.createStandaloneChat(
            message,
            (token: string) => {
              setStreamingMessage((prev) => prev + token);
            },
            pendingChatPassage?.text,
            fullReference,
          );

          setCurrentChatId(chatId);
          setPendingChatPassage(null);

          const chatMessages =
            await bibleService.getStandaloneChatMessages(chatId);
          setMessages(chatMessages);
          setStreamingMessage("");

          return chatId;
        } else {
          await bibleService.sendStandaloneChatMessage(
            currentChatId,
            message,
            (token: string) => {
              setStreamingMessage((prev) => prev + token);
            },
          );

          const chatMessages =
            await bibleService.getStandaloneChatMessages(currentChatId);
          setMessages(chatMessages);
          setStreamingMessage("");

          return currentChatId;
        }
      } catch (err) {
        setMessages((prev) => prev.filter((m) => m.id !== tempId));
        setStreamingMessage("");
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [currentChatId, pendingChatPassage],
  );

  const clearChat = useCallback(() => {
    setPendingChatPassage(null);
    setCurrentChatPassage(null);
    setCurrentChatId(null);
    setMessages([]);
    setStreamingMessage("");
  }, []);

  return {
    currentChatId,
    currentChatPassage,
    messages,
    loading,
    streamingMessage,
    startNewChat,
    loadExistingChat,
    sendMessage,
    clearChat,
  };
}
