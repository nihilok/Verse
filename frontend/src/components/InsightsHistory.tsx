import React, { useEffect } from "react";
import { History } from "lucide-react";
import type { InsightHistory } from "../types";
import { useInsightsHistory } from "../hooks/useInsightsHistory";
import { HistorySkeleton } from "./HistorySkeleton";
import { SidebarTabWrapper } from "./SidebarTabWrapper";

interface InsightsHistoryProps {
  onSelect: (item: InsightHistory) => void;
}

const InsightsHistoryComponent: React.FC<InsightsHistoryProps> = ({
  onSelect,
}) => {
  const { insightsHistory, loadHistory, loading } = useInsightsHistory();

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const history = insightsHistory;

  return (
    <SidebarTabWrapper title="Insights History" icon={History}>
      {loading ? (
        <HistorySkeleton />
      ) : history.length === 0 ? (
        <div className="text-center text-muted-foreground py-8">
          <History size={32} className="mx-auto mb-2 opacity-40" />
          <p className="text-sm">No insights history yet</p>
        </div>
      ) : (
        <div className="flex-1 min-h-0">
          <div className="space-y-2">
            {history.map((item) => (
              <button
                key={item.id}
                onClick={() => onSelect(item)}
                className="w-full text-left p-3 rounded-lg border bg-card hover:bg-accent transition-colors"
                title={item.text}
              >
                <div className="font-semibold text-sm mb-1">
                  {item.reference}
                </div>
                <div className="text-xs text-muted-foreground line-clamp-2">
                  "{item.text}"
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {new Date(item.timestamp).toLocaleString()}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </SidebarTabWrapper>
  );
};

export default InsightsHistoryComponent;
