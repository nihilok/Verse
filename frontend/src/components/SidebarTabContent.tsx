import React from "react";
import { TabsContent } from "./ui/tabs";

interface SidebarTabContentProps {
  value: string;
  children: React.ReactNode;
}

export const SidebarTabContent: React.FC<SidebarTabContentProps> = ({
  value,
  children,
}) => {
  return (
    <TabsContent value={value} className="mt-4 flex-1">
      {children}
    </TabsContent>
  );
};
