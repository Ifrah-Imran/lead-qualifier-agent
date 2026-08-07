"use client";

import { AlertCircle, CheckCircle2, Circle, Loader2 } from "lucide-react";

import { Progress } from "@/components/ui/progress";
import type { PipelineStage } from "@/lib/pipeline";

export type RowStatus = PipelineStage | "queued" | "error";

export type RowRunState = {
  key: string;
  companyName: string;
  status: RowStatus;
  error?: string;
};

const STAGE_LABEL: Record<RowStatus, string> = {
  queued: "Queued",
  enrich: "Enriching company data…",
  score: "Scoring fit…",
  draft: "Drafting outreach…",
  log: "Saving…",
  done: "Done",
  error: "Failed",
};

function RowIcon({ status }: { status: RowStatus }) {
  if (status === "done") return <CheckCircle2 className="h-4 w-4 text-success" />;
  if (status === "error") return <AlertCircle className="h-4 w-4 text-destructive" />;
  if (status === "queued") return <Circle className="h-4 w-4 text-muted-foreground" />;
  return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
}

export default function ProcessingPanel({ rows }: { rows: RowRunState[] }) {
  const settled = rows.filter((r) => r.status === "done" || r.status === "error").length;

  return (
    <div className="flex flex-col gap-4 p-6">
      <div className="space-y-3">
        <p className="text-sm font-medium text-foreground">
          Processing {rows.length} lead{rows.length === 1 ? "" : "s"}…
        </p>
        <Progress value={settled} max={rows.length} />
        <p className="text-xs text-muted-foreground">
          {settled} of {rows.length} complete
        </p>
      </div>
      <div className="max-h-80 space-y-2 overflow-y-auto">
        {rows.map((row) => (
          <div
            key={row.key}
            className="flex items-center justify-between gap-3 rounded-lg border border-border bg-secondary/40 px-3 py-2"
          >
            <div className="flex min-w-0 items-center gap-2.5">
              <RowIcon status={row.status} />
              <span className="truncate text-sm font-medium text-foreground">{row.companyName}</span>
            </div>
            <span
              className={`shrink-0 text-xs ${row.status === "error" ? "text-destructive" : "text-muted-foreground"}`}
              title={row.error}
            >
              {row.status === "error" && row.error ? row.error : STAGE_LABEL[row.status]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
