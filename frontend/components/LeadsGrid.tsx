"use client";

import { useMemo, useState } from "react";

import FilterBar, { ScoreFilterValue, SortValue, StatusFilterValue } from "@/components/FilterBar";
import LeadCard from "@/components/LeadCard";
import { Card } from "@/components/ui/card";
import { deleteLead, Lead, updateLeadStatus } from "@/lib/api";

function inScoreRange(score: number | null, range: ScoreFilterValue): boolean {
  if (range === "all") return true;
  if (score === null) return false;
  if (range === "0-3") return score <= 3;
  if (range === "4-6") return score >= 4 && score <= 6;
  return score >= 7;
}

function sortLeads(leads: Lead[], sort: SortValue): Lead[] {
  const arr = [...leads];
  switch (sort) {
    case "date-desc":
      return arr.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    case "date-asc":
      return arr.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    case "score-desc":
      return arr.sort((a, b) => (b.score ?? -1) - (a.score ?? -1));
    case "score-asc":
      return arr.sort((a, b) => (a.score ?? -1) - (b.score ?? -1));
    case "name-asc":
      return arr.sort((a, b) => a.name.localeCompare(b.name));
  }
}

export default function LeadsGrid({
  leads,
  onLeadUpdated,
  onLeadDeleted,
  highlightedIds,
}: {
  leads: Lead[];
  onLeadUpdated: (lead: Lead) => void;
  onLeadDeleted: (id: number) => void;
  highlightedIds?: Set<number>;
}) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilterValue>("All");
  const [score, setScore] = useState<ScoreFilterValue>("all");
  const [sort, setSort] = useState<SortValue>("date-desc");
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const filteredSorted = useMemo(() => {
    const q = search.trim().toLowerCase();
    const filtered = leads.filter((lead) => {
      if (status !== "All" && lead.status !== status) return false;
      if (!inScoreRange(lead.score, score)) return false;
      if (q && !lead.name.toLowerCase().includes(q) && !lead.company.toLowerCase().includes(q)) return false;
      return true;
    });
    return sortLeads(filtered, sort);
  }, [leads, search, status, score, sort]);

  const activeCount = [search.trim() !== "", status !== "All", score !== "all"].filter(Boolean).length;

  async function handleUpdate(id: number, next: "Approved" | "Rejected") {
    setPendingId(id);
    setError(null);
    try {
      const updated = await updateLeadStatus(id, next);
      onLeadUpdated(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update lead");
    } finally {
      setPendingId(null);
    }
  }

  async function handleDelete(id: number) {
    setPendingId(id);
    setError(null);
    try {
      await deleteLead(id);
      onLeadDeleted(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete lead");
    } finally {
      setPendingId(null);
    }
  }

  return (
    <div id="leads-grid" className="space-y-4 scroll-mt-6">
      <h2 className="text-base font-semibold text-foreground">Leads</h2>
      <FilterBar
        search={search}
        onSearchChange={setSearch}
        status={status}
        onStatusChange={setStatus}
        score={score}
        onScoreChange={setScore}
        sort={sort}
        onSortChange={setSort}
        activeCount={activeCount}
      />

      {error && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {leads.length === 0 ? (
        <Card className="py-10 text-center text-sm text-muted-foreground">
          No leads yet — click &ldquo;Add leads&rdquo; above to get started.
        </Card>
      ) : filteredSorted.length === 0 ? (
        <Card className="py-10 text-center text-sm text-muted-foreground">
          No leads match your search or filters.
        </Card>
      ) : (
        <div className="grid grid-cols-1 items-start gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredSorted.map((lead) => (
            <LeadCard
              key={lead.id}
              lead={lead}
              pending={pendingId === lead.id}
              onApprove={() => handleUpdate(lead.id, "Approved")}
              onReject={() => handleUpdate(lead.id, "Rejected")}
              onDelete={() => handleDelete(lead.id)}
              highlighted={highlightedIds?.has(lead.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
