import React from "react";
import { Skeleton } from "@/components/ui/skeleton";

interface HistorySkeletonProps {
  count?: number;
}

export const HistorySkeleton: React.FC<HistorySkeletonProps> = ({
  count = 3,
}) => {
  return (
    <div className="space-y-2 flex-1 overflow-y-auto min-h-0">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="w-full p-3 rounded-lg border bg-card">
          <Skeleton className="h-4 w-3/4 mb-2" />
          <Skeleton className="h-3 w-full mb-1" />
          <Skeleton className="h-3 w-5/6 mb-2" />
          <Skeleton className="h-3 w-1/3" />
        </div>
      ))}
    </div>
  );
};
