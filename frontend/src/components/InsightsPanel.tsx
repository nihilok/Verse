import React from "react";
import { CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Sparkles,
  Loader,
  CheckCircle,
  BookMarked,
  Landmark,
  Lightbulb,
} from "lucide-react";
import type { Insight } from "../types";

interface InsightsPanelProps {
  insight: Insight | null;
  loading: boolean;
  selectedText: string;
}

const InsightsPanel: React.FC<InsightsPanelProps> = ({
  insight,
  loading,
  selectedText,
}) => {
  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <CardHeader className="flex flex-row items-center gap-2 pb-4 border-b">
          <Sparkles size={24} />
          <CardTitle className="text-lg">AI Insights</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col items-center justify-center">
          <Loader size={40} className="animate-spin mb-4" />
          <p>Generating insights...</p>
        </CardContent>
      </div>
    );
  }

  if (!insight) {
    return (
      <div className="flex flex-col h-full">
        <CardHeader className="flex flex-row items-center gap-2 pb-4 border-b">
          <Sparkles size={24} />
          <CardTitle className="text-lg">AI Insights</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col items-center justify-center text-center text-muted-foreground">
          <Sparkles size={48} className="mb-4 opacity-40" />
          <p>
            Highlight any passage in the Bible reader to explore its meaning
          </p>
        </CardContent>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <CardHeader className="flex flex-row items-center gap-2 pb-4 border-b">
        <Sparkles size={24} />
        <CardTitle className="text-lg">AI Insights</CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        {insight.cached && (
          <div className="flex items-center gap-2 mb-4 text-green-600">
            <CheckCircle size={16} />
            <span>Cached Result</span>
          </div>
        )}
        {selectedText && (
          <div className="mb-4 p-3 rounded bg-muted">
            <h3 className="font-semibold text-sm mb-1">Selected Passage</h3>
            <p className="italic">"{selectedText}"</p>
          </div>
        )}

        <div className="insight-section">
          <h3 className="flex items-center gap-2 mb-2">
            <BookMarked size={20} />
            Historical Context
          </h3>
          <p>{insight.historical_context}</p>
        </div>

        <div className="insight-section">
          <h3 className="flex items-center gap-2 mb-2">
            <Landmark size={20} />
            Theological Significance
          </h3>
          <p>{insight.theological_significance}</p>
        </div>

        <div className="insight-section">
          <h3 className="flex items-center gap-2 mb-2">
            <Lightbulb size={20} />
            Practical Application
          </h3>
          <p>{insight.practical_application}</p>
        </div>
      </CardContent>
    </div>
  );
};

export default InsightsPanel;
