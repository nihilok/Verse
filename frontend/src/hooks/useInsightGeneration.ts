import { useState, useCallback } from "react";
import { bibleService } from "../services/api";
import { Insight, Definition, ChatMessage } from "../types";

const normaliseWhitespace = (text: string) => {
  return text.replace(/\s+/g, " ").trim();
};

export function useInsightGeneration() {
  const [insight, setInsight] = useState<Insight | null>(null);
  const [definition, setDefinition] = useState<Definition | null>(null);
  const [insightLoading, setInsightLoading] = useState(false);
  const [definitionLoading, setDefinitionLoading] = useState(false);
  const [selectedText, setSelectedText] = useState("");
  const [selectedReference, setSelectedReference] = useState("");
  const [selectedWord, setSelectedWord] = useState("");
  const [currentInsightId, setCurrentInsightId] = useState<number | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

  const generateInsight = useCallback(
    async (text: string, reference: string) => {
      const normalizedText = text.trim();
      setInsightLoading(true);
      setSelectedText(normalizedText);
      setSelectedReference(reference);

      try {
        const result = await bibleService.getInsights(
          normalizedText,
          reference,
        );
        setInsight(result);

        // Try to find the insight ID from backend
        try {
          const history = await bibleService.getInsightsHistory(50);
          const matchingInsight = history.find(
            (item) =>
              normaliseWhitespace(item.text) ===
                normaliseWhitespace(normalizedText) &&
              item.reference === reference,
          );
          if (matchingInsight) {
            const insightId = parseInt(matchingInsight.id);
            setCurrentInsightId(insightId);
            const messages = await bibleService.getChatMessages(insightId);
            setChatMessages(messages);
          } else {
            setCurrentInsightId(null);
            setChatMessages([]);
          }
        } catch (historyErr) {
          console.error("Failed to reload insights history:", historyErr);
        }

        return result;
      } finally {
        setInsightLoading(false);
      }
    },
    [],
  );

  const generateDefinition = useCallback(
    async (word: string, verseText: string, reference: string) => {
      const normalizedWord = word.trim();
      setDefinitionLoading(true);
      setSelectedWord(normalizedWord);
      setSelectedReference(reference);

      try {
        const result = await bibleService.getDefinition(
          normalizedWord,
          verseText,
          reference,
        );
        setDefinition(result);
        return result;
      } finally {
        setDefinitionLoading(false);
      }
    },
    [],
  );

  const loadInsightFromHistory = useCallback(
    async (
      insightId: number,
      text: string,
      reference: string,
      insightData: Insight,
    ) => {
      setInsight(insightData);
      setSelectedText(text);
      setSelectedReference(reference);
      setCurrentInsightId(insightId);

      try {
        const messages = await bibleService.getChatMessages(insightId);
        setChatMessages(messages);
      } catch (err) {
        console.error("Failed to load chat messages:", err);
        setChatMessages([]);
      }
    },
    [],
  );

  return {
    insight,
    definition,
    insightLoading,
    definitionLoading,
    selectedText,
    selectedReference,
    selectedWord,
    currentInsightId,
    chatMessages,
    generateInsight,
    generateDefinition,
    loadInsightFromHistory,
  };
}
