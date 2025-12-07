import React, { useEffect, useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TranslationInfo } from "@/types";
import { bibleService } from "@/services/api";
import { Crown } from "lucide-react";

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
  const [translations, setTranslations] = useState<TranslationInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTranslations = async () => {
      try {
        const response = await bibleService.getTranslations();
        setTranslations(response.translations);
      } catch (error) {
        console.error("Failed to fetch translations:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchTranslations();
  }, []);

  const selectedTranslation = translations.find((t) => t.code === value);

  if (loading) {
    return (
      <div className="h-auto bg-accent/80 text-accent-foreground px-3 py-1.5 rounded-full text-xs font-semibold tracking-wide w-auto min-w-[80px] flex items-center justify-center">
        {value}
      </div>
    );
  }

  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger className="h-auto bg-accent/80 text-accent-foreground px-3 py-1.5 rounded-full text-xs font-semibold tracking-wide border-0 focus:ring-0 focus:ring-offset-0 w-auto min-w-[80px]">
        <SelectValue placeholder="Select translation">
          {selectedTranslation?.code}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {translations.map((trans) => (
          <SelectItem key={trans.code} value={trans.code}>
            <div className="flex items-center gap-2">
              <span>
                {trans.code} - {trans.name}
              </span>
              {trans.requires_pro && (
                <Crown className="h-3 w-3 text-yellow-500" />
              )}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export default TranslationDropdown;
