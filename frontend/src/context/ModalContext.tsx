/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, ReactNode } from "react";

export type ModalType =
  | "insights"
  | "definition"
  | "chat"
  | "insightChat"
  | "deviceLink"
  | "landing";

interface ModalContextType {
  openModals: Record<ModalType, boolean>;
  openModal: (modal: ModalType) => void;
  closeModal: (modal: ModalType) => void;
  closeAllModals: () => void;
  isModalOpen: (modal: ModalType) => boolean;
}

const ModalContext = createContext<ModalContextType | undefined>(undefined);

export function ModalProvider({ children }: { children: ReactNode }) {
  const [openModals, setOpenModals] = useState<Record<ModalType, boolean>>({
    insights: false,
    definition: false,
    chat: false,
    insightChat: false,
    deviceLink: false,
    landing: false,
  });

  const openModal = (modal: ModalType) => {
    setOpenModals((prev) => ({ ...prev, [modal]: true }));
  };

  const closeModal = (modal: ModalType) => {
    setOpenModals((prev) => ({ ...prev, [modal]: false }));
  };

  const closeAllModals = () => {
    setOpenModals((prev) => {
      const closed = { ...prev };
      (Object.keys(closed) as ModalType[]).forEach((key) => {
        closed[key] = false;
      });
      return closed;
    });
  };

  const isModalOpen = (modal: ModalType) => openModals[modal];

  return (
    <ModalContext.Provider
      value={{ openModals, openModal, closeModal, closeAllModals, isModalOpen }}
    >
      {children}
    </ModalContext.Provider>
  );
}

export function useModal() {
  const context = useContext(ModalContext);
  if (context === undefined) {
    throw new Error("useModal must be used within a ModalProvider");
  }
  return context;
}
