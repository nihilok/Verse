import { useState, useCallback } from "react";

/**
 * A hook that manages loading state for data that should only be loaded once.
 * Tracks both whether data has been loaded and whether it's currently loading.
 *
 * @returns An object containing:
 *   - loading: boolean indicating if data is currently being loaded
 *   - loaded: boolean indicating if data has been loaded at least once
 *   - executeLoad: function to wrap your load function with loading state management
 */
export function useLoadOnce() {
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);

  /**
   * Wraps a load function with loading state management.
   * If already loaded, returns early without calling the load function.
   * Sets loading to true before calling, and false in finally block.
   * 
   * IMPORTANT: Sets loaded to true after execution, even if the function throws.
   * This prevents repeated failed attempts which could hammer a failing endpoint.
   * Errors are still propagated to the caller for proper error handling (logging, 
   * user notification, etc.), but the hook will not automatically retry.
   *
   * @param loadFn The async function to execute
   */
  const executeLoad = useCallback(
    async <T>(loadFn: () => Promise<T>): Promise<void> => {
      if (loaded) return;
      setLoading(true);
      try {
        await loadFn();
      } finally {
        setLoaded(true);
        setLoading(false);
      }
    },
    [loaded],
  );

  return { loading, loaded, executeLoad };
}
