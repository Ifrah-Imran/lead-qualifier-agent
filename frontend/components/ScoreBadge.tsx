import { Minus, TrendingDown, TrendingUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";

// Mirrors OUTREACH_SCORE_THRESHOLD (6) and the qualified/strong-fit split in app/main.py.
const SCORE_MAX = 10;

function iconFor(score: number): { icon: typeof TrendingUp; label: string } {
  if (score < 6) return { icon: TrendingDown, label: "Below fit" };
  if (score < 8) return { icon: Minus, label: "Moderate fit" };
  return { icon: TrendingUp, label: "Strong fit" };
}

export default function ScoreBadge({
  score,
  pillBg,
  pillText,
}: {
  score: number | null;
  /** Card-family pill colors — when provided, these win over the semantic tier color. */
  pillBg?: string;
  pillText?: string;
}) {
  if (score === null) {
    return (
      <span
        className="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium"
        style={pillBg ? { backgroundColor: pillBg, color: pillText, borderColor: "transparent" } : undefined}
      >
        <Minus className="h-3 w-3" />
        No score
      </span>
    );
  }

  const { icon: Icon, label } = iconFor(score);

  if (pillBg) {
    return (
      <span
        className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium tabular-nums"
        style={{ backgroundColor: pillBg, color: pillText }}
        title={label}
      >
        <Icon className="h-3 w-3" />
        {score}/{SCORE_MAX}
      </span>
    );
  }

  return (
    <Badge variant="outline" className="gap-1" title={label}>
      <Icon className="h-3 w-3" />
      <span className="tabular-nums">
        {score}/{SCORE_MAX}
      </span>
    </Badge>
  );
}
