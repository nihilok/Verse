import { useState, useEffect, type ChangeEvent } from "react";
import {
  Download,
  Upload,
  Trash2,
  Info,
  Link2,
  Copy,
  Check,
  Moon,
  Settings,
  Type,
} from "lucide-react";
import { Button } from "./ui/button";
import { bibleService } from "../services/api";
import type { UserSession } from "@/types";
import {
  loadWakeLockTimeout,
  saveWakeLockTimeout,
  loadFontSize,
  saveFontSize,
  loadFontFamily,
  saveFontFamily,
  type FontSize,
  type FontFamily,
} from "../lib/storage";
import { SidebarTabWrapper } from "./SidebarTabWrapper";
import { SettingsSection } from "./SettingsSection";
import { SettingsSelect } from "./SettingsSelect";

interface UserSettingsProps {
  onError: (message: string) => void;
  onSuccess: (message: string) => void;
  onOpenDeviceLinking?: () => void;
  onFontSizeChange?: (fontSize: FontSize) => void;
  onFontFamilyChange?: (fontFamily: FontFamily) => void;
}

export default function UserSettings({
  onError,
  onSuccess,
  onOpenDeviceLinking,
  onFontSizeChange,
  onFontFamilyChange,
}: UserSettingsProps) {
  const [loading, setLoading] = useState(false);
  const [userSession, setUserSession] = useState<UserSession | null>(null);
  const [copied, setCopied] = useState(false);
  const [wakeLockTimeout, setWakeLockTimeout] = useState<number>(5);
  const [fontSize, setFontSize] = useState<FontSize>("medium");
  const [fontFamily, setFontFamily] = useState<FontFamily>("inter");

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

    // Load font size from localStorage
    const savedFontSize = loadFontSize();
    setFontSize(savedFontSize);

    // Load font family from localStorage
    const savedFontFamily = loadFontFamily();
    setFontFamily(savedFontFamily);
  }, []);

  const handleWakeLockTimeoutChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const newTimeout = parseInt(e.target.value);
    setWakeLockTimeout(newTimeout);
    saveWakeLockTimeout(newTimeout);
    onSuccess(
      "Wake lock timeout updated. The new setting will apply to new reading sessions.",
    );
  };

  const handleFontSizeChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const newFontSize = e.target.value as FontSize;
    setFontSize(newFontSize);
    saveFontSize(newFontSize);
    onFontSizeChange?.(newFontSize);
  };

  const handleFontFamilyChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const newFontFamily = e.target.value as FontFamily;
    setFontFamily(newFontFamily);
    saveFontFamily(newFontFamily);
    onFontFamilyChange?.(newFontFamily);
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
    <SidebarTabWrapper title="Settings" icon={Settings}>
      <div className="flex-1 overflow-y-auto min-h-0 px-2">
        <div className="space-y-6">
          {/* Data Management Section */}
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
              <Info className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
              <div className="space-y-1 text-muted-foreground">
                <p>
                  Your data is stored anonymously and linked to your device via
                  a secure cookie.
                </p>
                <p>
                  Export your data to back it up or transfer to another device.
                </p>
              </div>
            </div>
          </div>

          {/* User ID Section */}
          {userSession && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium">User ID</h3>
              <p className="text-xs text-muted-foreground">
                Your anonymous user ID for pro subscription management.
              </p>
              <div className="flex gap-2">
                <div className="flex-1 bg-muted rounded-md px-3 py-2 text-xs font-mono truncate text-ellipsis">
                  {userSession.anonymous_id}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyUserId}
                  className="shrink-0"
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

          {/* Reading Settings */}
          <SettingsSection
            title="Font Size"
            description="Adjust the text size for comfortable reading."
            icon={Type}
          >
            <SettingsSelect
              id="font-size"
              label="Size:"
              value={fontSize}
              onChange={handleFontSizeChange}
              options={[
                { value: "small", label: "Small" },
                { value: "medium", label: "Medium" },
                { value: "large", label: "Large" },
                { value: "extra-large", label: "Extra Large" },
              ]}
            />
          </SettingsSection>

          <SettingsSection
            title="Font Family"
            description="Choose a typeface for the Bible text."
            icon={Type}
          >
            <SettingsSelect
              id="font-family"
              label="Font:"
              value={fontFamily}
              onChange={handleFontFamilyChange}
              options={[
                { value: "inter", label: "Inter (Default)" },
                { value: "serif", label: "Serif" },
                { value: "atkinson", label: "Atkinson Hyperlegible" },
                { value: "open-dyslexic", label: "OpenDyslexic" },
              ]}
            />
          </SettingsSection>

          {/* Wake Lock Settings */}
          <SettingsSection
            title="Wake Lock"
            description="Keep your device awake while reading. The wake lock will automatically release after the specified timeout period of inactivity."
            icon={Moon}
          >
            <SettingsSelect
              id="wake-lock-timeout"
              label="Timeout:"
              value={wakeLockTimeout}
              onChange={handleWakeLockTimeoutChange}
              options={[
                { value: 1, label: "1 minute" },
                { value: 2, label: "2 minutes" },
                { value: 5, label: "5 minutes" },
                { value: 10, label: "10 minutes" },
                { value: 15, label: "15 minutes" },
                { value: 30, label: "30 minutes" },
                { value: 0, label: "Disabled" },
              ]}
            />
          </SettingsSection>

          <div className="mb-4" />
        </div>
      </div>
    </SidebarTabWrapper>
  );
}
