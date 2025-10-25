import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { BookMarked, Landmark, Lightbulb, Sparkles, CheckCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { Insight } from '../types';

interface InsightsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  insight: Insight | null;
  selectedText: string;
  reference: string;
}

const InsightsModal: React.FC<InsightsModalProps> = ({ 
  open, 
  onOpenChange, 
  insight,
  selectedText,
  reference 
}) => {
  const [tab, setTab] = React.useState<'historical' | 'theological' | 'practical'>('historical');
  if (!insight) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles size={24} />
            AI Insights
          </DialogTitle>
        </DialogHeader>
        
        {insight.cached && (
          <div className="flex items-center gap-2 text-green-600 text-sm">
            <CheckCircle size={16} />
            <span>Cached Result</span>
          </div>
        )}
        
        {selectedText && (
          <div className="mb-2 p-3 rounded bg-muted">
            <h3 className="font-semibold text-sm mb-1">{reference}</h3>
            <p className="italic text-sm">"{selectedText}"</p>
          </div>
        )}

        <Tabs value={tab} onValueChange={(v) => setTab(v as 'historical' | 'theological' | 'practical')} className="flex-1 overflow-hidden flex flex-col">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="historical" className="flex items-center gap-2">
              <BookMarked size={16} />
              Historical
            </TabsTrigger>
            <TabsTrigger value="theological" className="flex items-center gap-2">
              <Landmark size={16} />
              Theological
            </TabsTrigger>
            <TabsTrigger value="practical" className="flex items-center gap-2">
              <Lightbulb size={16} />
              Practical
            </TabsTrigger>
          </TabsList>
          
          <div key={`tab-content-${tab}`} className="flex-1 overflow-y-auto mt-4">
            <TabsContent value="historical" className="prose prose-sm dark:prose-invert max-w-none" role="tabpanel" aria-label="Historical context insights">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {insight.historical_context}
              </ReactMarkdown>
            </TabsContent>
            
            <TabsContent value="theological" className="prose prose-sm dark:prose-invert max-w-none" role="tabpanel" aria-label="Theological significance insights">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {insight.theological_significance}
              </ReactMarkdown>
            </TabsContent>
            
            <TabsContent value="practical" className="prose prose-sm dark:prose-invert max-w-none" role="tabpanel" aria-label="Practical application insights">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {insight.practical_application}
              </ReactMarkdown>
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default InsightsModal;
