import React, { useLayoutEffect, useRef, useState } from "react";
import { Sparkles, X, MessageCircle } from "lucide-react";

interface SelectionButtonsProps {
  position: { x: number; y: number };
  onGetInsights: (e: React.MouseEvent | React.TouchEvent) => void;
  onAskQuestion: (e: React.MouseEvent | React.TouchEvent) => void;
  onClear: () => void;
}

const SelectionButtons: React.FC<SelectionButtonsProps> = ({
  position,
  onGetInsights,
  onAskQuestion,
  onClear,
}) => {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [adjustedPosition, setAdjustedPosition] = useState(position);

  useLayoutEffect(() => {
    const adjustPosition = () => {
      if (!tooltipRef.current) return;

      const tooltip = tooltipRef.current;
      const rect = tooltip.getBoundingClientRect();
      const viewportWidth = window.innerWidth;

      // Calculate the tooltip's width
      const tooltipWidth = rect.width;
      const halfWidth = tooltipWidth / 2;

      let newX = position.x;
      const newY = position.y;

      // Check if tooltip would go off the right edge (considering the -50% transform)
      if (position.x + halfWidth > viewportWidth) {
        // Move it left to fit within viewport with padding
        newX = viewportWidth - halfWidth - 8;
      }

      // Check if tooltip would go off the left edge (considering the -50% transform)
      if (position.x - halfWidth < 0) {
        // Move it right to fit within viewport with padding
        newX = halfWidth + 8;
      }

      setAdjustedPosition({ x: newX, y: newY });
    };

    // Adjust position after initial render and whenever position changes
    adjustPosition();

    // Also adjust on window resize
    window.addEventListener("resize", adjustPosition);
    return () => window.removeEventListener("resize", adjustPosition);
  }, [position]);

  return (
    <div
      ref={tooltipRef}
      data-testid="selection-tooltip"
      className="absolute bg-popover border-2 border-primary/20 rounded-lg shadow-xl p-1.5 flex flex-col gap-1.5 z-50"
      style={{
        left: `${adjustedPosition.x}px`,
        top: `${adjustedPosition.y}px`,
        transform: "translate(-50%, -50%)",
      }}
    >
      <div className="flex gap-1.5">
        <button
          onClick={onGetInsights}
          className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-all text-sm font-semibold whitespace-nowrap shadow-sm"
        >
          <Sparkles size={16} />
          Get Insights
        </button>
        <button
          onClick={onClear}
          className="flex items-center justify-center p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
          aria-label="Close"
        >
          <X size={16} />
        </button>
      </div>
      <button
        onClick={onAskQuestion}
        className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-accent text-accent-foreground hover:bg-accent/80 transition-all text-sm font-semibold whitespace-nowrap shadow-sm"
      >
        <MessageCircle size={16} />
        Ask a Question
      </button>
    </div>
  );
};

export default SelectionButtons;
