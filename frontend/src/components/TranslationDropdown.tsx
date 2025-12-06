import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Translation list - same as in PassageSearch
const TRANSLATIONS = [
  { code: "KJV", name: "King James Version" },
  { code: "ASV", name: "American Standard Version" },
  { code: "LSV", name: "Literal Standard Version" },
  { code: "WEB", name: "World English Bible" },
  { code: "BSB", name: "Berean Standard Bible" },
  { code: "BST", name: "Brenton English Septuagint" },
  { code: "LXXSB", name: "British English Septuagint 2012" },
  { code: "TOJBT", name: "The Orthodox Jewish Bible" },
  { code: "PEV", name: "Plain English Version" },
  { code: "RV", name: "Revised Version" },
  { code: "MSB", name: "Majority Standard Bible" },
  { code: "YLT", name: "Young's Literal Translation" },
  { code: "BBE", name: "Bible in Basic English" },
  { code: "EMTV", name: "English Majority Text Version" },
  { code: "BES", name: "La Biblia en Español Sencillo" },
  { code: "SRV", name: "Santa Biblia - Reina-Valera 1909" },
];

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
