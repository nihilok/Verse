import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TRANSLATIONS } from "@/lib/translations";

interface TranslationDropdownProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

const TranslationDropdown: React.FC<TranslationDropdownProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger className="h-auto bg-accent/80 text-accent-foreground px-3 py-1.5 rounded-full text-xs font-semibold tracking-wide border-0 focus:ring-0 focus:ring-offset-0 w-auto min-w-[80px]">
        <SelectValue placeholder="Select translation" />
      </SelectTrigger>
      <SelectContent>
        {TRANSLATIONS.map((trans) => (
          <SelectItem key={trans.code} value={trans.code}>
            {trans.code} - {trans.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export default TranslationDropdown;
