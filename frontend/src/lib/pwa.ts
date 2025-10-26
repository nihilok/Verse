// PWA utilities for service worker registration and installation

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

let deferredPrompt: BeforeInstallPromptEvent | null = null;

/**
 * Register the service worker
 */
export const registerServiceWorker =
  async (): Promise<ServiceWorkerRegistration | null> => {
    if ("serviceWorker" in navigator) {
      try {
        const registration = await navigator.serviceWorker.register(
          "/service-worker.js",
          {
            scope: "/",
          },
        );

        console.log(
          "Service Worker registered successfully:",
          registration.scope,
        );

        // Check for updates periodically
        setInterval(
          () => {
            registration.update();
          },
          60 * 60 * 1000,
        ); // Check every hour

        // Handle updates
        registration.addEventListener("updatefound", () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener("statechange", () => {
              if (
                newWorker.state === "installed" &&
                navigator.serviceWorker.controller
              ) {
                // New service worker available, prompt user to refresh
                if (
                  confirm(
                    "A new version of Verse is available. Would you like to update?",
                  )
                ) {
                  newWorker.postMessage({ type: "SKIP_WAITING" });
                  window.location.reload();
                }
              }
            });
          }
        });

        return registration;
      } catch (error) {
        console.error("Service Worker registration failed:", error);
        return null;
      }
    }
    return null;
  };

/**
 * Unregister the service worker (useful for development)
 */
export const unregisterServiceWorker = async (): Promise<boolean> => {
  if ("serviceWorker" in navigator) {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration) {
      return registration.unregister();
    }
  }
  return false;
};

/**
 * Check if the app is running as a PWA
 */
export const isPWA = (): boolean => {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (window.navigator as any).standalone === true ||
    document.referrer.includes("android-app://")
  );
};

/**
 * Check if the app can be installed
 */
export const canInstall = (): boolean => {
  return deferredPrompt !== null;
};

/**
 * Set up the install prompt listener
 */
export const setupInstallPrompt = (
  callback?: (canInstall: boolean) => void,
): void => {
  window.addEventListener("beforeinstallprompt", (e) => {
    // Prevent the default mini-infobar
    e.preventDefault();
    // Store the event for later use
    deferredPrompt = e as BeforeInstallPromptEvent;
    if (callback) {
      callback(true);
    }
  });

  window.addEventListener("appinstalled", () => {
    console.log("PWA was installed");
    deferredPrompt = null;
    if (callback) {
      callback(false);
    }
  });
};

/**
 * Show the install prompt
 */
export const showInstallPrompt = async (): Promise<
  "accepted" | "dismissed" | "unavailable"
> => {
  if (!deferredPrompt) {
    return "unavailable";
  }

  // Show the install prompt
  await deferredPrompt.prompt();

  // Wait for the user's response
  const { outcome } = await deferredPrompt.userChoice;

  // Clear the deferred prompt
  deferredPrompt = null;

  return outcome;
};

/**
 * Request notification permission (if needed for future features)
 */
export const requestNotificationPermission =
  async (): Promise<NotificationPermission> => {
    if ("Notification" in window) {
      return await Notification.requestPermission();
    }
    return "denied";
  };
