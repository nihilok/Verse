import React from "react";
import type { LucideIcon } from "lucide-react";

interface SidebarTabWrapperProps {
  title: string;
  icon: LucideIcon;
  children: React.ReactNode;
}

export const SidebarTabWrapper: React.FC<SidebarTabWrapperProps> = ({
  title,
  icon: Icon,
  children,
}) => {
  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="flex items-center justify-between flex-shrink-0">
        <h3 className="font-semibold flex items-center gap-2">
          <Icon size={20} />
          {title}
        </h3>
      </div>
      <div className="flex-1 h-full overflow-y-auto scrollbar-overlay px-1">
        {children}
      </div>
    </div>
  );
};
