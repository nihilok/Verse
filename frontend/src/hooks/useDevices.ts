import { useState, useCallback } from "react";
import { bibleService } from "../services/api";
import { UserDevice } from "../types";

export function useDevices() {
  const [devices, setDevices] = useState<UserDevice[]>([]);
  const [loaded, setLoaded] = useState(false);

  const loadDevices = useCallback(async () => {
    if (loaded) return;
    try {
      const deviceList = await bibleService.getUserDevices();
      setDevices(deviceList);
      setLoaded(true);
    } catch (err) {
      console.error("Failed to load devices:", err);
    }
  }, [loaded]);

  return {
    devices,
    setDevices,
    loadDevices,
  };
}
