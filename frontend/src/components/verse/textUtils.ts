import type { TextPart, TextPartText } from "@/types";

export function isTextPart(part: TextPart): part is TextPartText {
  return typeof part === "object" && "text" in part;
}

export function isLineBreak(part: TextPart): part is { lineBreak: true } {
  return typeof part === "object" && "lineBreak" in part;
}

export function containsPilcrow(text: string): boolean {
  return text.includes("¶");
}

export function getPoemIndentClass(poem?: number): string {
  if (!poem) return "";
  switch (poem) {
    case 1:
      return "ml-4";
    case 2:
      return "ml-8";
    case 3:
      return "ml-12";
    default:
      return `ml-${Math.min(poem * 4, 16)}`;
  }
}

export function removePilcrow(text: string): string {
  return text.replace(/¶\s*/g, "");
}
