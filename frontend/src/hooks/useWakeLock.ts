import { useEffect, useRef, useCallback } from "react";

// Default timeout in milliseconds (5 minutes)
const DEFAULT_WAKE_LOCK_TIMEOUT = 5 * 60 * 1000;

interface UseWakeLockOptions {
  timeout?: number; // Timeout in milliseconds
}

/**
 * Custom hook to manage the Screen Wake Lock API
 * Automatically releases the wake lock after a configurable period of inactivity
 *
 * @param options - Configuration options
 * @returns Object with methods to request and release wake lock
 */
export function useWakeLock(options: UseWakeLockOptions = {}) {
  const { timeout = DEFAULT_WAKE_LOCK_TIMEOUT } = options;
  const wakeLockRef = useRef<WakeLockSentinel | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isRequestingRef = useRef(false);

  /**
   * Request a wake lock from the browser
   */
  const requestWakeLock = useCallback(async () => {
    // Check if Wake Lock API is supported
    if (!("wakeLock" in navigator)) {
      console.debug("Wake Lock API not supported in this browser");
      return false;
    }

    // Don't request if already requesting - use a more robust check
    if (isRequestingRef.current) {
      return false;
    }

    // Set flag immediately to prevent race conditions
    isRequestingRef.current = true;

    try {
      // Release existing wake lock if any
      if (wakeLockRef.current) {
        await wakeLockRef.current.release();
        wakeLockRef.current = null;
      }

      // Request a new wake lock
      wakeLockRef.current = await navigator.wakeLock.request("screen");
      console.debug("Wake Lock acquired");

      // Set up event listener for when wake lock is released
      wakeLockRef.current.addEventListener("release", () => {
        console.debug("Wake Lock released");
      });

      return true;
    } catch (err) {
      // Wake lock request can fail for various reasons:
      // - Document is not visible
      // - Battery is low
      // - User denied permission
      console.debug("Failed to acquire Wake Lock:", err);
      return false;
    } finally {
      isRequestingRef.current = false;
    }
  }, []);

  /**
   * Release the current wake lock
   */
  const releaseWakeLock = useCallback(async () => {
    if (wakeLockRef.current) {
      try {
        await wakeLockRef.current.release();
        wakeLockRef.current = null;
      } catch (err) {
        console.debug("Error releasing Wake Lock:", err);
      }
    }
  }, []);

  /**
   * Refresh the wake lock timeout
   * This should be called on user activity (scroll, page turn, etc.)
   */
  const refreshWakeLock = useCallback(async () => {
    // Don't activate wake lock if disabled
    if (timeout === 0) {
      return;
    }

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Request wake lock if not already active
    await requestWakeLock();

    // Set up new timeout to release wake lock
    timeoutRef.current = setTimeout(async () => {
      await releaseWakeLock();
    }, timeout);
  }, [timeout, requestWakeLock, releaseWakeLock]);

  /**
   * Handle visibility change - reacquire wake lock when page becomes visible again
   */
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (
        timeout > 0 &&
        document.visibilityState === "visible" &&
        wakeLockRef.current?.released
      ) {
        // Reacquire wake lock if it was released due to visibility change
        await refreshWakeLock();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [refreshWakeLock, timeout]);

  /**
   * Clean up on unmount
   */
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (wakeLockRef.current) {
        wakeLockRef.current.release().catch(() => {
          // Ignore errors during cleanup
        });
      }
    };
  }, []);

  return {
    refreshWakeLock,
    releaseWakeLock,
    isSupported: "wakeLock" in navigator,
  };
}
