"use client";

import { useState } from "react";
import { AlertTriangle, Check, ChevronDown, Link as LinkIcon, Phone, Trash2, X } from "lucide-react";

import ScoreBadge from "@/components/ScoreBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getCardColors } from "@/lib/cardColors";
import { Lead, LeadStatus } from "@/lib/api";

function StatusPill({
  status,
  pillBg,
  pillText,
}: {
  status: LeadStatus;
  pillBg: string;
  pillText: string;
}) {
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ backgroundColor: pillBg, color: pillText }}
    >
      {status}
    </span>
  );
}

const OPTIONAL_FIELDS: { key: keyof Lead; label: string }[] = [
  { key: "title", label: "Title" },
  { key: "industry", label: "Industry" },
  { key: "company_size", label: "Company size" },
  { key: "location", label: "Location" },
  { key: "recent_signal", label: "Recent signal" },
  { key: "linkedin_active_recently", label: "LinkedIn activity" },
  { key: "estimated_monthly_leads", label: "Monthly leads" },
  { key: "has_dedicated_sales_role", label: "Dedicated sales role" },
];

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function formatValue(value: string | number | boolean | null): string {
  if (value === null) return "Not provided";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function MetaField({ label, value }: { label: string; value: string | number | boolean | null }) {
  const missing = value === null;
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={`text-sm font-medium ${missing ? "italic text-muted-foreground" : "text-foreground"}`}>
        {formatValue(value)}
      </dd>
    </div>
  );
}

export default function LeadCard({
  lead,
  pending,
  onApprove,
  onReject,
  onDelete,
  highlighted,
}: {
  lead: Lead;
  pending: boolean;
  onApprove: () => void;
  onReject: () => void;
  onDelete: () => void;
  highlighted?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const missingFields = OPTIONAL_FIELDS.filter((f) => lead[f.key] === null);
  const colors = getCardColors(lead.id);

  function handleDeleteClick(e: React.SyntheticEvent) {
    e.stopPropagation();
    if (window.confirm(`Delete the lead for ${lead.company}? This can't be undone.`)) {
      onDelete();
    }
  }

  return (
    <Card
      className={`flex flex-col gap-0 overflow-hidden border-0 transition-shadow ${
        highlighted ? "ring-2 ring-primary ring-offset-2 ring-offset-background" : ""
      }`}
    >
      <div
        role="button"
        tabIndex={0}
        onClick={() => setExpanded((v) => !v)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setExpanded((v) => !v);
          }
        }}
        className="flex w-full cursor-pointer flex-col gap-3 p-6 text-left"
        style={{ backgroundColor: colors.card }}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="truncate text-sm font-semibold" style={{ color: colors.cardText }}>
              {lead.company}
            </h3>
            {lead.name && lead.name !== "Unknown" && (
              <p className="truncate text-sm" style={{ color: colors.cardTextMuted }}>
                {lead.name}
                {lead.title ? `, ${lead.title}` : ""}
              </p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <button
              onClick={handleDeleteClick}
              aria-label="Delete lead"
              title="Delete lead"
              className="rounded-md p-1.5 transition-colors hover:bg-destructive/15 hover:text-destructive"
              style={{ color: colors.cardTextMuted }}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
            <ChevronDown
              className={`h-4 w-4 transition-transform ${expanded ? "rotate-180" : ""}`}
              style={{ color: colors.cardTextMuted }}
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <ScoreBadge score={lead.score} pillBg={colors.pillBg} pillText={colors.pillText} />
          <StatusPill status={lead.status} pillBg={colors.pillBg} pillText={colors.pillText} />
          {missingFields.length > 0 && (
            <span
              className="flex items-center gap-1 text-xs"
              style={{ color: colors.cardTextMuted }}
            >
              <AlertTriangle className="h-3 w-3" />
              {missingFields.length} field{missingFields.length === 1 ? "" : "s"} missing
            </span>
          )}
        </div>
      </div>

      {expanded && (
        <div className="flex flex-col gap-4 border-t border-border bg-background p-6">
          <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {OPTIONAL_FIELDS.slice(0, 4).map((f) => (
              <MetaField key={f.key} label={f.label} value={lead[f.key] as string | number | boolean | null} />
            ))}
          </dl>

          {(lead.phone || Object.keys(lead.social_links).length > 0) && (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">Contact info found</p>
              <div className="flex flex-wrap items-center gap-2">
                {lead.phone && (
                  <a
                    href={`tel:${lead.phone}`}
                    className="flex items-center gap-1.5 rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-foreground transition-colors hover:bg-secondary"
                  >
                    <Phone className="h-3.5 w-3.5" />
                    {lead.phone}
                  </a>
                )}
                {Object.entries(lead.social_links).map(([platform, url]) => (
                  <a
                    key={platform}
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1.5 rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-foreground transition-colors hover:bg-secondary"
                  >
                    <LinkIcon className="h-3.5 w-3.5" />
                    {capitalize(platform)}
                  </a>
                ))}
              </div>
            </div>
          )}

          {missingFields.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-xs text-muted-foreground">Missing:</span>
              {missingFields.map((f) => (
                <Badge key={f.key} variant="outline" className="text-muted-foreground">
                  {f.label}
                </Badge>
              ))}
            </div>
          )}

          {lead.reason && <p className="text-sm text-muted-foreground">{lead.reason}</p>}

          {lead.drafted_message ? (
            <blockquote className="whitespace-pre-wrap break-words rounded-lg border border-border bg-card px-3 py-2.5 text-sm text-foreground">
              {lead.drafted_message}
            </blockquote>
          ) : (
            <p className="rounded-lg border border-dashed border-border px-3 py-2.5 text-sm text-muted-foreground">
              No outreach message drafted.
            </p>
          )}

          <div className="flex justify-end gap-2">
            <Button variant="outlineSuccess" size="sm" disabled={pending} onClick={onApprove}>
              <Check className="h-3.5 w-3.5" />
              Approve
            </Button>
            <Button variant="outlineDestructive" size="sm" disabled={pending} onClick={onReject}>
              <X className="h-3.5 w-3.5" />
              Reject
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}
