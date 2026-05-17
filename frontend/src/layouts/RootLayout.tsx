import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu } from "lucide-react";
import { Toaster } from "sonner";
import { Button } from "../components/ui/button";
import { useUI } from "../context/UIContext";
import { Outlet } from "react-router-dom";

interface RootLayoutProps {
  sidebar?: React.ReactNode;
  children?: React.ReactNode;
}

export default function RootLayout({ sidebar, children }: RootLayoutProps) {
  const { sidebarOpen, setSidebarOpen, isDesktop } = useUI();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Toaster richColors closeButton position="top-center" />
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {!isDesktop && sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          x: sidebarOpen ? 0 : -320,
          width: sidebarOpen ? (isDesktop ? "20rem" : "100%") : "0rem",
        }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className={`fixed lg:relative z-50 h-full border-r bg-card shadow-lg lg:shadow-none overflow-hidden ${!isDesktop && sidebarOpen ? "w-full max-w-[20rem]" : ""}`}
      >
        <div className="h-full w-80 lg:w-80">{sidebar}</div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {!sidebarOpen && (
          <div className="absolute top-4 left-4 z-30">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(true)}
              className="rounded-full shadow-none bg-transparent hover:bg-muted text-foreground/60"
            >
              <Menu className="h-6 w-6" />
            </Button>
          </div>
        )}
        <div className="flex-1 flex flex-col overflow-hidden min-h-0">
          {children || <Outlet />}
        </div>
      </main>
    </div>
  );
}
