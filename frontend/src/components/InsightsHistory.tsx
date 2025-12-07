import React, { useEffect } from "react";
import { History, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { InsightHistory } from "../types";
import { useInsightsHistory } from "../hooks/useInsightsHistory";
import { HistorySkeleton } from "./HistorySkeleton";

interface InsightsHistoryProps {
  onSelect: (item: InsightHistory) => void;
  onError?: (msg: string) => void;
}

const InsightsHistoryComponent: React.FC<InsightsHistoryProps> = ({
  onSelect,
  onError,
}) => {
  const { insightsHistory, loadHistory, clearHistory, loading } =
    useInsightsHistory();

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleClear = async () => {
    try {
      await clearHistory();
    } catch {
      onError?.("Failed to clear history. Please try again.");
    }
  };

  const history = insightsHistory;

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="flex items-center justify-between flex-shrink-0">
        <h3 className="font-semibold flex items-center gap-2">
          <History size={20} />
          Insights History
        </h3>
        {history.length > 0 && !loading && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            className="text-destructive"
          >
            <Trash2 size={16} />
          </Button>
        )}
      </div>

      {loading ? (
        <HistorySkeleton />
      ) : history.length === 0 ? (
        <div className="text-center text-muted-foreground py-8">
          <History size={32} className="mx-auto mb-2 opacity-40" />
          <p className="text-sm">No insights history yet</p>
        </div>
      ) : (
        <div className="space-y-2 flex-1 overflow-y-auto min-h-0">
          {history.map((item) => (
            <button
              key={item.id}
              onClick={() => onSelect(item)}
              className="w-full text-left p-3 rounded-lg border bg-card hover:bg-accent transition-colors"
              title={item.text}
            >
              <div className="font-semibold text-sm mb-1">{item.reference}</div>
              <div className="text-xs text-muted-foreground line-clamp-2">
                "{item.text}"
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {new Date(item.timestamp).toLocaleString()}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default InsightsHistoryComponent;
