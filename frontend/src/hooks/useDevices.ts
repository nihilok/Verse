import { useState, useCallback } from "react";
import { bibleService } from "../services/api";
import { UserDevice } from "../types";
import { useLoadOnce } from "./useLoadOnce";

export function useDevices() {
  const [devices, setDevices] = useState<UserDevice[]>([]);
  const { loading, executeLoad } = useLoadOnce();

  const loadDevices = useCallback(async () => {
    await executeLoad(async () => {
      try {
        const deviceList = await bibleService.getUserDevices();
        setDevices(deviceList);
      } catch (err) {
        console.error("Failed to load devices:", err);
        throw err;
      }
    });
  }, [executeLoad]);

  return {
    devices,
    setDevices,
    loadDevices,
    loading,
  };
}
