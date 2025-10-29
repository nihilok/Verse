import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingOverlayProps {
  message: string;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ message }) => {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card p-6 rounded-lg shadow-lg flex flex-col items-center gap-4">
        <Loader2 size={48} className="animate-spin text-primary" />
        <p className="text-lg">{message}</p>
      </div>
    </div>
  );
};

export default LoadingOverlay;
