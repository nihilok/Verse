import type { ChangeEvent } from "react";

interface SettingsSelectProps {
  id: string;
  label: string;
  value: string | number;
  onChange: (e: ChangeEvent<HTMLSelectElement>) => void;
  options: Array<{ value: string | number; label: string }>;
}

export function SettingsSelect({
  id,
  label,
  value,
  onChange,
  options,
}: SettingsSelectProps) {
  return (
    <div className="flex items-center gap-2">
      <label htmlFor={id} className="text-xs text-muted-foreground">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={onChange}
        className="flex h-8 rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
