import { useState, useEffect } from 'react';

/**
 * Standard interface for the backend API provided by pywebview.
 * This should be extended as we define more backend functions.
 */
interface BackendAPI {
  reset_session: () => Promise<void>;
  stop_session: () => Promise<void>;
  get_positions: () => Promise<any[]>;
  get_logs: () => Promise<string[]>;
  // Add more as needed
}

declare global {
  interface Window {
    pywebview?: {
      api: BackendAPI;
    };
  }
}

export function useBackend() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const checkApi = () => {
      if (window.pywebview?.api) {
        setIsReady(true);
      } else {
        // Retry after a short delay if not yet ready
        setTimeout(checkApi, 100);
      }
    };

    checkApi();
  }, []);

  const callBackend = async <T,>(fn: (api: BackendAPI) => Promise<T>): Promise<T | null> => {
    if (window.pywebview?.api) {
      try {
        return await fn(window.pywebview.api);
      } catch (error) {
        console.error('Backend call failed:', error);
        return null;
      }
    }
    console.warn('Backend API not available');
    return null;
  };

  return { isReady, callBackend };
}
