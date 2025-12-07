import React, { useState, useEffect } from "react";
import {
  Download,
  Upload,
  Trash2,
  Info,
  Link2,
  Copy,
  Check,
  Moon,
} from "lucide-react";
import { Button } from "./ui/button";
import { bibleService } from "../services/api";
import type { UserSession } from "../types";
import { loadWakeLockTimeout, saveWakeLockTimeout } from "../lib/storage";

interface UserSettingsProps {
  onError: (message: string) => void;
  onSuccess: (message: string) => void;
  onOpenDeviceLinking?: () => void;
}

export default function UserSettings({
  onError,
  onSuccess,
  onOpenDeviceLinking,
}: UserSettingsProps) {
  const [loading, setLoading] = useState(false);
  const [userSession, setUserSession] = useState<UserSession | null>(null);
  const [copied, setCopied] = useState(false);
  const [wakeLockTimeout, setWakeLockTimeout] = useState<number>(5);

  useEffect(() => {
    const loadSession = async () => {
      try {
        const session = await bibleService.getUserSession();
        setUserSession(session);
      } catch (err) {
        console.error("Failed to load user session:", err);
      }
    };
    loadSession();

    // Load wake lock timeout from localStorage
    const savedTimeout = loadWakeLockTimeout();
    setWakeLockTimeout(savedTimeout);
  }, []);

  const handleWakeLockTimeoutChange = (
    e: React.ChangeEvent<HTMLSelectElement>,
  ) => {
    const newTimeout = parseInt(e.target.value);
    setWakeLockTimeout(newTimeout);
    saveWakeLockTimeout(newTimeout);
    onSuccess("Wake lock timeout updated. Reload the page for changes to take effect.");
  };

  const handleClearData = async () => {
    if (
      !confirm(
        "Are you sure you want to clear all your data? This action cannot be undone.",
      )
    ) {
      return;
    }

    setLoading(true);
    try {
      const result = await bibleService.clearUserData();
      if (result.deleted) {
        onSuccess(
          `Cleared ${result.deleted.insights} insights, ${result.deleted.chat_messages} chat messages, and ${result.deleted.standalone_chats} chats.`,
        );
      } else {
        onSuccess("Data cleared successfully!");
      }
    } catch (err) {
      console.error("Failed to clear data:", err);
      onError("Failed to clear data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    setLoading(true);
    try {
      const data = await bibleService.exportUserData();

      // Create a blob and download it
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `verse-data-${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      onSuccess("Data exported successfully!");
    } catch (err) {
      console.error("Failed to export data:", err);
      onError("Failed to export data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleImportData = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "application/json";
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      setLoading(true);
      try {
        const text = await file.text();
        let data;
        try {
          data = JSON.parse(text);
        } catch {
          onError(
            "Invalid JSON file. Please select a valid Verse export file.",
          );
          setLoading(false);
          return;
        }

        const result = await bibleService.importUserData(data);
        if (result.imported) {
          onSuccess(
            `Imported ${result.imported.insights} insights, ${result.imported.chat_messages} chat messages, and ${result.imported.standalone_chats} chats.`,
          );
        } else {
          onSuccess("Data imported successfully!");
        }

        // Reload the page to show imported data after user has time to read message
        setTimeout(() => window.location.reload(), 2500);
      } catch (err) {
        console.error("Failed to import data:", err);
        onError(
          "Failed to import data. Please check the file format and try again.",
        );
      } finally {
        setLoading(false);
      }
    };
    input.click();
  };

  const handleCopyUserId = async () => {
    if (!userSession?.anonymous_id) return;

    try {
      await navigator.clipboard.writeText(userSession.anonymous_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy user ID:", err);
      onError("Failed to copy user ID. Please try again.");
    }
  };

  return (
    <div className="space-y-6">
      {/* User ID Section */}
      {userSession && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium">User ID</h3>
          <p className="text-xs text-muted-foreground">
            Your anonymous user ID for pro subscription management.
          </p>
          <div className="flex gap-2">
            <div className="flex-1 bg-muted rounded-md px-3 py-2 text-xs font-mono break-all">
              {userSession.anonymous_id}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyUserId}
              className="flex-shrink-0"
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4" />
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Wake Lock Settings */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium flex items-center gap-2">
          <Moon className="h-4 w-4" />
          Wake Lock
        </h3>
        <p className="text-xs text-muted-foreground">
          Keep your device awake while reading. The wake lock will automatically
          release after the specified timeout period of inactivity.
        </p>
        <div className="flex items-center gap-2">
          <label
            htmlFor="wake-lock-timeout"
            className="text-xs text-muted-foreground"
          >
            Timeout:
          </label>
          <select
            id="wake-lock-timeout"
            value={wakeLockTimeout}
            onChange={handleWakeLockTimeoutChange}
            className="flex h-8 rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="1">1 minute</option>
            <option value="2">2 minutes</option>
            <option value="5">5 minutes</option>
            <option value="10">10 minutes</option>
            <option value="15">15 minutes</option>
            <option value="30">30 minutes</option>
            <option value="0">Disabled</option>
          </select>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-medium">Data Management</h3>
        <p className="text-xs text-muted-foreground">
          Export, import, or clear your personal data. Your data is stored
          locally on your device via cookies.
        </p>
      </div>

      <div className="space-y-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleExportData}
          disabled={loading}
          className="w-full justify-start"
        >
          <Download className="mr-2 h-4 w-4" />
          Export Data
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={handleImportData}
          disabled={loading}
          className="w-full justify-start"
        >
          <Upload className="mr-2 h-4 w-4" />
          Import Data
        </Button>

        {onOpenDeviceLinking && (
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenDeviceLinking}
            disabled={loading}
            className="w-full justify-start"
          >
            <Link2 className="mr-2 h-4 w-4" />
            Link Devices
          </Button>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={handleClearData}
          disabled={loading}
          className="w-full justify-start text-destructive hover:text-destructive"
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Clear All Data
        </Button>
      </div>

      <div className="bg-muted rounded-md p-3 text-xs space-y-1">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
          <div className="space-y-1 text-muted-foreground">
            <p>
              Your data is stored anonymously and linked to your device via a
              secure cookie.
            </p>
            <p>Export your data to back it up or transfer to another device.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
