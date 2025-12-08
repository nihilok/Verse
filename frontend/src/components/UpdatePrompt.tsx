import { useState, useEffect } from "react";
import { RefreshCw, X } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";

/**
 * Component to prompt users to update the PWA when a new version is available
 */
export default function UpdatePrompt() {
  const [showPrompt, setShowPrompt] = useState(false);
  const [newWorker, setNewWorker] = useState<ServiceWorker | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    if (!("serviceWorker" in navigator)) {
      return;
    }

    const checkForUpdates = async () => {
      const registration = await navigator.serviceWorker.getRegistration();
      if (!registration) {
        return;
      }

      // Check for updates periodically
      const updateInterval = setInterval(
        () => {
          registration.update();
        },
        60 * 60 * 1000, // Check every hour
      );

      // Handle updates
      registration.addEventListener("updatefound", () => {
        const installingWorker = registration.installing;
        if (!installingWorker) {
          return;
        }

        installingWorker.addEventListener("statechange", () => {
          if (
            installingWorker.state === "installed" &&
            navigator.serviceWorker.controller
          ) {
            // New service worker available, show update prompt
            setNewWorker(installingWorker);
            setShowPrompt(true);
          }
        });
      });

      return () => {
        clearInterval(updateInterval);
      };
    };

    checkForUpdates();
  }, []);

  const handleUpdate = async () => {
    if (!newWorker) {
      return;
    }

    setIsUpdating(true);

    // Tell the service worker to skip waiting
    newWorker.postMessage({ type: "SKIP_WAITING" });

    // Wait a moment for the service worker to activate
    setTimeout(() => {
      window.location.reload();
    }, 100);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
  };

  if (!showPrompt) {
    return null;
  }

  return (
    <div className="fixed top-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md z-50 animate-in slide-in-from-top-5">
      <Card className="p-4 shadow-lg border-2 border-primary/20 bg-card">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
            <RefreshCw className="text-primary" size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-sm mb-1">Update Available</h3>
            <p className="text-xs text-muted-foreground mb-3">
              A new version of Verse is available. Update now for the latest
              features and improvements.
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={handleUpdate}
                disabled={isUpdating}
                className="flex-1"
              >
                {isUpdating ? "Updating..." : "Update Now"}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleDismiss}
                className="flex-1"
              >
                Later
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
