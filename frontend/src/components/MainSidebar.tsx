import {
  BookOpen,
  X,
  History as HistoryIcon,
  MessageSquare,
  Settings as SettingsIcon,
  Search as SearchIcon,
} from "lucide-react";
import { Sidebar, SidebarHeader, SidebarContent } from "./ui/sidebar";
import { Button } from "./ui/button";
import { Tabs, TabsList, TabsTrigger } from "./ui/tabs";
import { SidebarTabContent } from "./SidebarTabContent";
import PassageSearch from "./PassageSearch";
import InsightsHistoryComponent from "./InsightsHistory";
import ChatHistory from "./ChatHistory";
import UserSettings from "./UserSettings";
import { ModeToggle } from "./mode-toggle";
import { useUI } from "../context/UIContext";
import { InsightHistory, StandaloneChat } from "../types";
import { FontSize, FontFamily } from "../lib/storage";

interface MainSidebarProps {
  onSearch: (
    book: string,
    chapter: number,
    verseStart?: number,
    verseEnd?: number,
    translation?: string,
  ) => void;
  onHistorySelect: (item: InsightHistory) => void;
  onChatHistorySelect: (chat: StandaloneChat) => void;
  onError: (msg: string) => void;
  onSuccess: (msg: string) => void;
  onOpenDeviceLinking: () => void;
  onFontSizeChange: (size: FontSize) => void;
  onFontFamilyChange: (font: FontFamily) => void;
}

export default function MainSidebar({
  onSearch,
  onHistorySelect,
  onChatHistorySelect,
  onError,
  onSuccess,
  onOpenDeviceLinking,
  onFontSizeChange,
  onFontFamilyChange,
}: MainSidebarProps) {
  const { setSidebarOpen, isDesktop } = useUI();

  return (
    <Sidebar className="h-full w-full bg-card flex flex-col border-none shadow-none">
      <SidebarHeader className="flex flex-col gap-2 flex-shrink-0 pb-4 border-b relative">
        {!isDesktop && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(false)}
            className="absolute top-0 right-0"
            aria-label="Close sidebar"
          >
            <X size={20} />
          </Button>
        )}
        <div className="flex gap-2 w-full items-center justify-between">
          <div className="flex gap-2 items-center">
            <BookOpen size={28} className="text-primary" strokeWidth={1.5} />
            <h2 className="font-semibold text-xl tracking-tight text-primary">
              Verse
            </h2>
          </div>
        </div>
        <p className="w-full text-xs text-muted-foreground italic">
          Discover wisdom through AI-powered insights
        </p>
      </SidebarHeader>
      <SidebarContent className="flex-1 min-h-0 bg-transparent">
        <Tabs defaultValue="search" className="w-full h-full flex flex-col">
          <TabsList className="grid w-full grid-cols-4 flex-shrink-0 mb-4">
            <TabsTrigger value="search" className="flex items-center gap-1">
              <SearchIcon size={16} className="sm:hidden" />
              <span className="hidden sm:inline">Search</span>
            </TabsTrigger>
            <TabsTrigger value="insights" className="flex items-center gap-1">
              <HistoryIcon size={16} className="sm:hidden" />
              <span className="hidden sm:inline">Insights</span>
            </TabsTrigger>
            <TabsTrigger value="chats" className="flex items-center gap-1">
              <MessageSquare size={16} className="sm:hidden" />
              <span className="hidden sm:inline">Chats</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-1">
              <SettingsIcon size={16} className="sm:hidden" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto min-h-0">
            <SidebarTabContent value="search">
              <PassageSearch onSearch={onSearch} />
            </SidebarTabContent>
            <SidebarTabContent value="insights">
              <InsightsHistoryComponent onSelect={onHistorySelect} />
            </SidebarTabContent>
            <SidebarTabContent value="chats">
              <ChatHistory onSelect={onChatHistorySelect} onError={onError} />
            </SidebarTabContent>
            <SidebarTabContent value="settings">
              <UserSettings
                onError={onError}
                onSuccess={onSuccess}
                onOpenDeviceLinking={onOpenDeviceLinking}
                onFontSizeChange={onFontSizeChange}
                onFontFamilyChange={onFontFamilyChange}
              />
            </SidebarTabContent>
          </div>
        </Tabs>
      </SidebarContent>
      {/* ModeToggle at the bottom of the sidebar */}
      <div className="w-full flex justify-center py-4 border-t mt-auto">
        <ModeToggle />
      </div>
    </Sidebar>
  );
}
