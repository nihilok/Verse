import { useState, useEffect } from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  Link2,
  Smartphone,
  Monitor,
  Tablet,
  Copy,
  Clock,
  CheckCircle,
  AlertCircle,
  Trash2,
  X,
} from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Card } from "./ui/card";
import { bibleService } from "../services/api";
import { UserDevice } from "../types";

interface DeviceLinkModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  devices: UserDevice[];
  onDevicesChange: (devices: UserDevice[]) => void;
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
}

export default function DeviceLinkModal({
  open,
  onOpenChange,
  devices,
  onDevicesChange,
  onSuccess,
  onError,
}: DeviceLinkModalProps) {
  const [loading, setLoading] = useState(false);
  const [linkCode, setLinkCode] = useState<string | null>(null);
  const [qrData, setQrData] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [inputCode, setInputCode] = useState("");
  const [copied, setCopied] = useState(false);

  // Countdown timer for link code expiration
  useEffect(() => {
    if (!expiresAt) {
      setTimeRemaining(null);
      return;
    }

    const updateTimer = () => {
      const now = new Date().getTime();
      const expiry = new Date(expiresAt).getTime();
      const remaining = Math.max(0, Math.floor((expiry - now) / 1000));
      setTimeRemaining(remaining);

      if (remaining === 0) {
        setLinkCode(null);
        setQrData(null);
        setExpiresAt(null);
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [expiresAt]);

  const loadDevices = async () => {
    try {
      const fetchedDevices = await bibleService.getUserDevices();
      onDevicesChange(fetchedDevices);
    } catch (err) {
      console.error("Failed to load devices:", err);
    }
  };

  // Load devices when modal opens
  useEffect(() => {
    if (open) {
      loadDevices();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const handleGenerateCode = async () => {
    setLoading(true);
    try {
      const result = await bibleService.generateLinkCode();
      setLinkCode(result.display_code);
      setQrData(result.qr_data);
      setExpiresAt(result.expires_at);
      onSuccess("Link code generated successfully!");
    } catch (err) {
      console.error("Failed to generate link code:", err);
      onError("Failed to generate link code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    if (linkCode) {
      navigator.clipboard.writeText(linkCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleLinkDevice = async () => {
    if (!inputCode.trim()) {
      onError("Please enter a link code");
      return;
    }

    setLoading(true);
    try {
      const result = await bibleService.acceptLinkCode(inputCode.trim());
      if (result.success) {
        onSuccess(result.message);
        setInputCode("");
        onOpenChange(false);
        // Reload page to refresh with merged data
        setTimeout(() => window.location.reload(), 1500);
      }
    } catch (err) {
      console.error("Failed to link device:", err);
      onError("Failed to link device. Please check the code and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleUnlinkDevice = async (deviceId: number) => {
    if (
      !confirm(
        "Are you sure you want to unlink this device? If this is the last device, all data will be deleted.",
      )
    ) {
      return;
    }

    setLoading(true);
    try {
      const result = await bibleService.unlinkDevice(deviceId);
      onSuccess(result.message);

      if (result.should_clear_cookie) {
        // Last device was unlinked, reload to clear session
        setTimeout(() => window.location.reload(), 1500);
      } else {
        // Reload devices list
        await loadDevices();
      }
    } catch (err) {
      console.error("Failed to unlink device:", err);
      onError("Failed to unlink device. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const formatTimeRemaining = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getDeviceIcon = (type: string | null) => {
    switch (type) {
      case "mobile":
        return <Smartphone className="h-5 w-5" />;
      case "desktop":
        return <Monitor className="h-5 w-5" />;
      case "tablet":
        return <Tablet className="h-5 w-5" />;
      default:
        return <Smartphone className="h-5 w-5" />;
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            <Link2 size={28} className="text-primary" />
            Link Devices
          </DialogTitle>
        </DialogHeader>

        <Tabs
          defaultValue="link"
          className="flex-1 overflow-hidden flex flex-col"
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="link">Link Device</TabsTrigger>
            <TabsTrigger value="manage">
              Manage Devices ({devices.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent
            value="link"
            className="flex-1 overflow-y-auto space-y-6 mt-4"
          >
            {/* Generate Code Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Generate Link Code</h3>
              <p className="text-sm text-muted-foreground">
                Generate a code to link another device. The code expires in 5
                minutes.
              </p>

              {!linkCode ? (
                <Button
                  onClick={handleGenerateCode}
                  disabled={loading}
                  className="w-full"
                >
                  <Link2 className="mr-2 h-4 w-4" />
                  Generate Link Code
                </Button>
              ) : (
                <Card className="p-6 space-y-4">
                  {/* QR Code */}
                  <div className="flex justify-center">
                    <div className="bg-white p-4 rounded-lg">
                      <QRCodeSVG value={qrData || linkCode} size={200} />
                    </div>
                  </div>

                  {/* Display Code */}
                  <div className="space-y-2">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground mb-2">
                        Or enter this code manually:
                      </p>
                      <div className="flex items-center justify-center gap-2">
                        <code className="text-2xl font-mono font-bold bg-muted px-4 py-2 rounded">
                          {linkCode}
                        </code>
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={handleCopyCode}
                        >
                          {copied ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Timer */}
                  {timeRemaining !== null && (
                    <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      <span>
                        Expires in {formatTimeRemaining(timeRemaining)}
                      </span>
                    </div>
                  )}

                  {/* Cancel Button */}
                  <Button
                    variant="outline"
                    onClick={() => {
                      setLinkCode(null);
                      setQrData(null);
                      setExpiresAt(null);
                    }}
                    className="w-full"
                  >
                    <X className="mr-2 h-4 w-4" />
                    Cancel
                  </Button>
                </Card>
              )}
            </div>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  Or
                </span>
              </div>
            </div>

            {/* Enter Code Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Enter Link Code</h3>
              <p className="text-sm text-muted-foreground">
                Enter a code from another device to link it to this account.
              </p>

              <div className="flex gap-2">
                <Input
                  type="text"
                  placeholder="XXXX-XXXX-XXXX"
                  value={inputCode}
                  onChange={(e) => setInputCode(e.target.value.toUpperCase())}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleLinkDevice();
                    }
                  }}
                  className="flex-1 font-mono"
                  maxLength={14}
                />
                <Button
                  onClick={handleLinkDevice}
                  disabled={loading || !inputCode.trim()}
                >
                  Link
                </Button>
              </div>
            </div>
          </TabsContent>

          <TabsContent
            value="manage"
            className="flex-1 overflow-y-auto space-y-4 mt-4"
          >
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Manage devices linked to your account. Unlinking the last device
                will delete all your data.
              </p>

              {devices.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No devices found</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {devices.map((device) => (
                    <Card key={device.id} className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="text-muted-foreground mt-0.5">
                            {getDeviceIcon(device.device_type)}
                          </div>
                          <div className="space-y-1">
                            <div className="font-medium">
                              {device.device_name || "Unnamed Device"}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {device.device_type || "Unknown type"}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Last active: {formatDate(device.last_active)}
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleUnlinkDevice(device.id)}
                          disabled={loading}
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
