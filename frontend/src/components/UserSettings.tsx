import { useState } from "react";
import { Download, Upload, Trash2, Info } from "lucide-react";
import { Button } from "./ui/button";
import { bibleService } from "../services/api";

interface UserSettingsProps {
  onError: (message: string) => void;
  onSuccess: (message: string) => void;
}

export default function UserSettings({ onError, onSuccess }: UserSettingsProps) {
  const [loading, setLoading] = useState(false);

  const handleClearData = async () => {
    if (!confirm("Are you sure you want to clear all your data? This action cannot be undone.")) {
      return;
    }

    setLoading(true);
    try {
      const result = await bibleService.clearUserData();
      if (result.deleted) {
        onSuccess(`Cleared ${result.deleted.insights} insights, ${result.deleted.chat_messages} chat messages, and ${result.deleted.standalone_chats} chats.`);
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
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `verse-data-${new Date().toISOString().split('T')[0]}.json`;
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
          onError("Invalid JSON file. Please select a valid Verse export file.");
          setLoading(false);
          return;
        }
        
        const result = await bibleService.importUserData(data);
        if (result.imported) {
          onSuccess(`Imported ${result.imported.insights} insights, ${result.imported.chat_messages} chat messages, and ${result.imported.standalone_chats} chats.`);
        } else {
          onSuccess("Data imported successfully!");
        }
        
        // Reload the page to show imported data after user has time to read message
        setTimeout(() => window.location.reload(), 2500);
      } catch (err) {
        console.error("Failed to import data:", err);
        onError("Failed to import data. Please check the file format and try again.");
      } finally {
        setLoading(false);
      }
    };
    input.click();
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Data Management</h3>
        <p className="text-xs text-muted-foreground">
          Export, import, or clear your personal data. Your data is stored locally on your device via cookies.
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
              Your data is stored anonymously and linked to your device via a secure cookie.
            </p>
            <p>
              Export your data to back it up or transfer to another device.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
