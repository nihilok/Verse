import { useState, useCallback } from "react";
import { bibleService } from "../services/api";
import { UserDevice } from "../types";
import { useLoadOnce } from "./useLoadOnce";

export function useDevices() {
  const [devices, setDevices] = useState<UserDevice[]>([]);
  const { executeLoad } = useLoadOnce();

  const loadDevices = useCallback(async () => {
    await executeLoad(async () => {
      const deviceList = await bibleService.getUserDevices();
      setDevices(deviceList);
    });
  }, [executeLoad]);

  return {
    devices,
    setDevices,
    loadDevices,
  };
}
