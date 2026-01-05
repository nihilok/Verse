import React from "react";

interface VerseNumberProps {
  verse: number;
  variant?: "inline" | "superscript" | "block";
  className?: string;
}

export const VerseNumber: React.FC<VerseNumberProps> = ({
  verse,
  variant = "inline",
  className = "",
}) => {
  const baseClasses = "verse-number text-primary/70 font-semibold select-none";

  const variantClasses = {
    inline: "text-xs",
    superscript: "text-xs mr-0.5",
    block: "min-w-[28px] text-right",
  };

  const Component = variant === "superscript" ? "sup" : "span";

  return (
    <Component
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
    >
      {verse}
    </Component>
  );
};
