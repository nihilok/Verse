import { useState, useCallback } from "react";
import { bibleService } from "../services/api";
import { InsightHistory } from "../types";
import { useLoadOnce } from "./useLoadOnce";

const MAX_HISTORY_ITEMS = 50;

export function useInsightsHistory() {
  const [insightsHistory, setInsightsHistory] = useState<InsightHistory[]>([]);
  const { loading, executeLoad } = useLoadOnce();

  const loadHistory = useCallback(async () => {
    await executeLoad(async () => {
      const history = await bibleService.getInsightsHistory(MAX_HISTORY_ITEMS);
      setInsightsHistory(history);
    });
  }, [executeLoad]);

  const reloadHistory = useCallback(async () => {
    try {
      const history = await bibleService.getInsightsHistory(MAX_HISTORY_ITEMS);
      setInsightsHistory(history);
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
    loading,
  };
}
