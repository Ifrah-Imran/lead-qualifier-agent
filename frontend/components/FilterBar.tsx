"use client";

import { useState } from "react";
import { ChevronDown, Search, SlidersHorizontal } from "lucide-react";

import { Input } from "@/components/ui/input";

export type StatusFilterValue = "All" | "New" | "Approved" | "Rejected";
export type ScoreFilterValue = "all" | "0-3" | "4-6" | "7-10";
export type SortValue = "date-desc" | "date-asc" | "score-desc" | "score-asc" | "name-asc";

export const STATUS_OPTIONS: StatusFilterValue[] = ["All", "New", "Approved", "Rejected"];

const SCORE_OPTIONS: { value: ScoreFilterValue; label: string }[] = [
  { value: "all", label: "All scores" },
  { value: "0-3", label: "Score 0–3" },
  { value: "4-6", label: "Score 4–6" },
  { value: "7-10", label: "Score 7–10" },
];

const SORT_OPTIONS: { value: SortValue; label: string }[] = [
  { value: "date-desc", label: "Newest first" },
  { value: "date-asc", label: "Oldest first" },
  { value: "score-desc", label: "Score: high to low" },
  { value: "score-asc", label: "Score: low to high" },
  { value: "name-asc", label: "Name A–Z" },
];

const SELECT_CLASS =
  "h-9 appearance-none rounded-md border border-input bg-card pl-3 pr-8 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2";

function Select({
  value,
  onChange,
  children,
}: {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  children: React.ReactNode;
}) {
  return (
    <div className="relative">
      <select value={value} onChange={onChange} className={SELECT_CLASS}>
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
    </div>
  );
}

export default function FilterBar({
  search,
  onSearchChange,
  status,
  onStatusChange,
  score,
  onScoreChange,
  sort,
  onSortChange,
  activeCount,
}: {
  search: string;
  onSearchChange: (v: string) => void;
  status: StatusFilterValue;
  onStatusChange: (v: StatusFilterValue) => void;
  score: ScoreFilterValue;
  onScoreChange: (v: ScoreFilterValue) => void;
  sort: SortValue;
  onSortChange: (v: SortValue) => void;
  activeCount: number;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="relative min-w-[220px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search name or company…"
            className="pl-9"
          />
        </div>
        <button
          onClick={() => setOpen((v) => !v)}
          className="flex shrink-0 items-center gap-2 rounded-lg border border-border bg-card px-3.5 py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {activeCount > 0 && (
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-accent px-1 text-xs font-semibold text-accent-foreground">
              {activeCount}
            </span>
          )}
          <ChevronDown className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
        </button>
      </div>

      {open && (
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-card p-3">
          <Select value={status} onChange={(e) => onStatusChange(e.target.value as StatusFilterValue)}>
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt === "All" ? "All statuses" : opt}
              </option>
            ))}
          </Select>
          <Select value={score} onChange={(e) => onScoreChange(e.target.value as ScoreFilterValue)}>
            {SCORE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
          <Select value={sort} onChange={(e) => onSortChange(e.target.value as SortValue)}>
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
        </div>
      )}
    </div>
  );
}
