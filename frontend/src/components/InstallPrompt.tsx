import { useState, useEffect } from "react";
import { Download, X } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { setupInstallPrompt, showInstallPrompt, isPWA } from "../lib/pwa";

/**
 * Component to prompt users to install the PWA
 */
export default function InstallPrompt() {
  const [showPrompt, setShowPrompt] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  useEffect(() => {
    // Don't show if already running as PWA
    if (isPWA()) {
      return;
    }

    // Check if user has previously dismissed the prompt
    const dismissed = localStorage.getItem("pwa-install-dismissed");
    if (dismissed) {
      const dismissedTime = parseInt(dismissed, 10);
      const daysSinceDismissed =
        (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);
      // Show again after 7 days
      if (daysSinceDismissed < 7) {
        return;
      }
    }

    // Set up the install prompt listener
    setupInstallPrompt((canInstall) => {
      setShowPrompt(canInstall);
    });
  }, []);

  const handleInstall = async () => {
    setIsInstalling(true);
    const outcome = await showInstallPrompt();

    if (outcome === "accepted") {
      console.log("User accepted the install prompt");
    } else if (outcome === "dismissed") {
      console.log("User dismissed the install prompt");
    }

    setShowPrompt(false);
    setIsInstalling(false);
  };

  const handleDismiss = () => {
    // Store dismissal time
    localStorage.setItem("pwa-install-dismissed", Date.now().toString());
    setShowPrompt(false);
  };

  if (!showPrompt) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md z-50 animate-in slide-in-from-bottom-5">
      <Card className="p-4 shadow-lg border-2">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
            <Download className="text-primary" size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-sm mb-1">Install Verse</h3>
            <p className="text-xs text-muted-foreground mb-3">
              Install Verse for a better experience with offline access and
              faster loading.
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={handleInstall}
                disabled={isInstalling}
                className="flex-1"
              >
                {isInstalling ? "Installing..." : "Install"}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleDismiss}
                className="flex-1"
              >
                Not now
              </Button>
            </div>
          </div>
          <Button
            size="icon"
            variant="ghost"
            onClick={handleDismiss}
            className="flex-shrink-0 h-8 w-8"
          >
            <X size={16} />
          </Button>
        </div>
      </Card>
    </div>
  );
}
