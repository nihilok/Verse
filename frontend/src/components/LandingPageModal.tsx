import React, { useState, useEffect } from "react";
import { BookOpen, Highlighter, MessageSquare, Sparkles } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

const LANDING_MODAL_DISMISSED_KEY = "verse-landing-modal-dismissed";

interface LandingPageModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const LandingPageModal: React.FC<LandingPageModalProps> = ({
  open,
  onOpenChange,
}) => {
  const [dontShowAgain, setDontShowAgain] = useState(false);

  const handleClose = () => {
    if (dontShowAgain) {
      localStorage.setItem(LANDING_MODAL_DISMISSED_KEY, "true");
    }
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            <BookOpen className="text-primary" size={28} />
            Welcome to Verse
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <p className="text-muted-foreground">
            Discover deeper meaning in Scripture with AI-powered insights.
            Here's how to get started:
          </p>

          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="flex-shrink-0 mt-0.5">
                <div className="rounded-full bg-primary/10 p-2">
                  <BookOpen className="text-primary" size={18} />
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-1">Search for a passage</h3>
                <p className="text-sm text-muted-foreground">
                  Use the search tab to find any Bible passage across multiple
                  translations.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex-shrink-0 mt-0.5">
                <div className="rounded-full bg-primary/10 p-2">
                  <Highlighter className="text-primary" size={18} />
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-1">
                  Highlight text for insights
                </h3>
                <p className="text-sm text-muted-foreground">
                  Select any verse or passage to get AI-powered historical,
                  theological, and practical insights.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex-shrink-0 mt-0.5">
                <div className="rounded-full bg-primary/10 p-2">
                  <MessageSquare className="text-primary" size={18} />
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-1">Chat with Verse AI</h3>
                <p className="text-sm text-muted-foreground">
                  Ask questions about passages and engage in thoughtful
                  conversations about Scripture.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex-shrink-0 mt-0.5">
                <div className="rounded-full bg-primary/10 p-2">
                  <Sparkles className="text-primary" size={18} />
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-1">Single word definitions</h3>
                <p className="text-sm text-muted-foreground">
                  Highlight a single word to get contextual definitions and
                  deeper understanding.
                </p>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-col gap-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="dont-show-again"
              checked={dontShowAgain}
              onCheckedChange={(checked: boolean | "indeterminate") =>
                setDontShowAgain(checked === true)
              }
            />
            <Label
              htmlFor="dont-show-again"
              className="text-sm font-normal cursor-pointer"
            >
              Don't show this again
            </Label>
          </div>
          <Button onClick={handleClose} className="w-full">
            Get Started
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Hook to check if modal should be shown
// eslint-disable-next-line react-refresh/only-export-components
export const useLandingModal = () => {
  const [shouldShow, setShouldShow] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem(LANDING_MODAL_DISMISSED_KEY);
    if (!dismissed) {
      setShouldShow(true);
    }
  }, []);

  return shouldShow;
};

export default LandingPageModal;
