"use client";

import { useState } from "react";
import { Check, X } from "lucide-react";

import { Lead, LeadStatus, updateLeadStatus } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const STATUS_BADGE_VARIANT: Record<string, "secondary" | "success" | "destructive"> = {
  New: "secondary",
  Approved: "success",
  Rejected: "destructive",
};

function StatusBadge({ status }: { status: LeadStatus }) {
  return <Badge variant={STATUS_BADGE_VARIANT[status] ?? "secondary"}>{status}</Badge>;
}

export default function LeadsTable({ leads: initialLeads }: { leads: Lead[] }) {
  const [leads, setLeads] = useState(initialLeads);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleUpdate(id: number, status: "Approved" | "Rejected") {
    setPendingId(id);
    setError(null);
    try {
      const updated = await updateLeadStatus(id, status);
      setLeads((prev) => prev.map((lead) => (lead.id === id ? updated : lead)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update lead");
    } finally {
      setPendingId(null);
    }
  }

  if (leads.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          No leads yet.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}
      <Card className="overflow-hidden py-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Score</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Drafted Message</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {leads.map((lead) => (
              <TableRow key={lead.id}>
                <TableCell className="font-medium">{lead.name}</TableCell>
                <TableCell>{lead.company}</TableCell>
                <TableCell className="tabular-nums">
                  {lead.score ?? <span className="text-muted-foreground">—</span>}
                </TableCell>
                <TableCell>
                  <StatusBadge status={lead.status} />
                </TableCell>
                <TableCell
                  className="max-w-xs truncate text-muted-foreground"
                  title={lead.drafted_message ?? undefined}
                >
                  {lead.drafted_message ?? "—"}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-emerald-200 text-emerald-700 hover:bg-emerald-50 hover:text-emerald-800 dark:border-emerald-900 dark:text-emerald-400 dark:hover:bg-emerald-500/10"
                      disabled={pendingId === lead.id}
                      onClick={() => handleUpdate(lead.id, "Approved")}
                    >
                      <Check className="h-3.5 w-3.5" />
                      Approve
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-red-200 text-red-700 hover:bg-red-50 hover:text-red-800 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-500/10"
                      disabled={pendingId === lead.id}
                      onClick={() => handleUpdate(lead.id, "Rejected")}
                    >
                      <X className="h-3.5 w-3.5" />
                      Reject
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
