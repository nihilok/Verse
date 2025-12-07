import { useState, useCallback } from "react";
import { bibleService } from "../services/api";
import { InsightHistory } from "../types";

const MAX_HISTORY_ITEMS = 50;

export function useInsightsHistory() {
  const [insightsHistory, setInsightsHistory] = useState<InsightHistory[]>([]);
  const [loaded, setLoaded] = useState(false);

  const loadHistory = useCallback(async () => {
    if (loaded) return;
    try {
      const history = await bibleService.getInsightsHistory(MAX_HISTORY_ITEMS);
      setInsightsHistory(history);
      setLoaded(true);
    } catch (e) {
      console.error("Failed to load insights history:", e);
    }
  }, [loaded]);

  const reloadHistory = useCallback(async () => {
    try {
      const history = await bibleService.getInsightsHistory(MAX_HISTORY_ITEMS);
      setInsightsHistory(history);
      setLoaded(true);
    } catch (e) {
      console.error("Failed to reload insights history:", e);
    }
  }, []);

  const clearHistory = useCallback(async () => {
    if (confirm("Are you sure you want to clear all insights history?")) {
      try {
        await bibleService.clearInsightsHistory();
        setInsightsHistory([]);
      } catch (err) {
        console.error("Failed to clear insights history:", err);
        throw err;
      }
    }
  }, []);

  return {
    insightsHistory,
    loadHistory,
    reloadHistory,
    clearHistory,
  };
}
