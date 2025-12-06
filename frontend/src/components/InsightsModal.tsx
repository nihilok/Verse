import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  BookMarked,
  Landmark,
  Lightbulb,
  Sparkles,
  CheckCircle,
  MessageCircle,
} from "lucide-react";
import MarkdownLink from "./MarkdownLink";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import type { Insight, ChatMessage } from "../types";

interface InsightsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  insight: Insight | null;
  selectedText: string;
  reference: string;
  insightId: number | null;
  chatMessages: ChatMessage[];
  onContinueChat: () => void;
}

const InsightsModal: React.FC<InsightsModalProps> = ({
  open,
  onOpenChange,
  insight,
  selectedText,
  reference,
  insightId,
  chatMessages,
  onContinueChat,
}) => {
  const [tab, setTab] = React.useState<
    "historical" | "theological" | "practical"
  >("historical");

  const hasChatMessages = chatMessages && chatMessages.length > 0;

  if (!insight) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            <Sparkles size={28} className="text-primary" />
            AI Insights
          </DialogTitle>
        </DialogHeader>

        {insight.cached && (
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400 text-sm bg-green-50 dark:bg-green-950/30 px-3 py-1.5 rounded-md">
            <CheckCircle size={16} />
            <span className="font-medium">Cached Result</span>
          </div>
        )}

        {selectedText && (
          <div className="mb-2 p-4 rounded-lg bg-muted/50 border border-border">
            <h3 className="font-semibold text-sm mb-2 text-primary">
              {reference}
            </h3>
            <p className="italic text-sm leading-relaxed">"{selectedText}"</p>
          </div>
        )}

        <Tabs
          value={tab}
          onValueChange={(v) =>
            setTab(v as "historical" | "theological" | "practical")
          }
          className="flex-1 overflow-hidden flex flex-col"
        >
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="historical" className="flex items-center gap-2">
              <BookMarked size={16} />
              Historical
            </TabsTrigger>
            <TabsTrigger
              value="theological"
              className="flex items-center gap-2"
            >
              <Landmark size={16} />
              Theological
            </TabsTrigger>
            <TabsTrigger value="practical" className="flex items-center gap-2">
              <Lightbulb size={16} />
              Practical
            </TabsTrigger>
          </TabsList>

          <div
            key={`tab-content-${tab}`}
            className="flex-1 overflow-y-auto mt-0 px-3 scrollbar-thin"
          >
            <TabsContent
              value="historical"
              className="prose prose-sm dark:prose-invert max-w-none"
              role="tabpanel"
              aria-label="Historical context insights"
            >
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{ a: MarkdownLink }}
              >
                {insight.historical_context}
              </ReactMarkdown>
            </TabsContent>

            <TabsContent
              value="theological"
              className="prose prose-sm dark:prose-invert max-w-none"
              role="tabpanel"
              aria-label="Theological significance insights"
            >
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{ a: MarkdownLink }}
              >
                {insight.theological_significance}
              </ReactMarkdown>
            </TabsContent>

            <TabsContent
              value="practical"
              className="prose prose-sm dark:prose-invert max-w-none"
              role="tabpanel"
              aria-label="Practical application insights"
            >
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{ a: MarkdownLink }}
              >
                {insight.practical_application}
              </ReactMarkdown>
            </TabsContent>
          </div>
        </Tabs>

        {/* Chat Button - Start or Continue */}
        {insightId && (
          <div className="border-t pt-4 mt-4">
            <Button
              onClick={onContinueChat}
              className="w-full flex items-center gap-2"
              variant="outline"
            >
              <MessageCircle size={18} />
              {hasChatMessages
                ? `Continue Chat (${chatMessages.length} message${chatMessages.length !== 1 ? "s" : ""})`
                : "Ask Follow-up Question"}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default InsightsModal;
