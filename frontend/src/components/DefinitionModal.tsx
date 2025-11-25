import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  BookOpen,
  BookMarked,
  Languages,
  CheckCircle,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Definition } from "../types";

interface DefinitionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  definition: Definition | null;
  word: string;
  reference: string;
}

const DefinitionModal: React.FC<DefinitionModalProps> = ({
  open,
  onOpenChange,
  definition,
  word,
  reference,
}) => {
  const [tab, setTab] = React.useState<
    "definition" | "biblical" | "original"
  >("definition");
  
  if (!definition) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            <BookOpen size={28} className="text-primary" />
            Definition
          </DialogTitle>
        </DialogHeader>

        {definition.cached && (
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400 text-sm bg-green-50 dark:bg-green-950/30 px-3 py-1.5 rounded-md">
            <CheckCircle size={16} />
            <span className="font-medium">Cached Result</span>
          </div>
        )}

        <div className="mb-2 p-4 rounded-lg bg-muted/50 border border-border">
          <h3 className="font-semibold text-sm mb-2 text-primary">
            {reference}
          </h3>
          <p className="text-lg font-semibold">"{word}"</p>
        </div>

        <Tabs
          value={tab}
          onValueChange={(v) =>
            setTab(v as "definition" | "biblical" | "original")
          }
          className="flex-1 overflow-hidden flex flex-col"
        >
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="definition" className="flex items-center gap-2">
              <BookOpen size={16} />
              Definition
            </TabsTrigger>
            <TabsTrigger
              value="biblical"
              className="flex items-center gap-2"
            >
              <BookMarked size={16} />
              Biblical Usage
            </TabsTrigger>
            <TabsTrigger value="original" className="flex items-center gap-2">
              <Languages size={16} />
              Original Language
            </TabsTrigger>
          </TabsList>

          <div
            key={`tab-content-${tab}`}
            className="flex-1 overflow-y-auto mt-0 px-3 scrollbar-thin"
          >
            <TabsContent
              value="definition"
              className="prose prose-sm dark:prose-invert max-w-none"
              role="tabpanel"
              aria-label="Word definition"
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {definition.definition}
              </ReactMarkdown>
            </TabsContent>

            <TabsContent
              value="biblical"
              className="prose prose-sm dark:prose-invert max-w-none"
              role="tabpanel"
              aria-label="Biblical usage"
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {definition.biblical_usage}
              </ReactMarkdown>
            </TabsContent>

            <TabsContent
              value="original"
              className="prose prose-sm dark:prose-invert max-w-none"
              role="tabpanel"
              aria-label="Original language information"
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {definition.original_language}
              </ReactMarkdown>
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default DefinitionModal;
