"use client";

import { useState } from "react";

import { Dialog } from "@/components/ui/dialog";
import { Toast, ToastState } from "@/components/ui/toast";
import DeleteAllDialog from "@/components/DeleteAllDialog";
import Header from "@/components/Header";
import LeadsGrid from "@/components/LeadsGrid";
import ProcessingPanel, { RowRunState } from "@/components/ProcessingPanel";
import StatsRow from "@/components/StatsRow";
import UploadPanel from "@/components/UploadPanel";
import { deleteAllLeads, Lead } from "@/lib/api";
import { RawLeadInput, runLeadPipeline } from "@/lib/pipeline";

const HIGHLIGHT_DURATION_MS = 6000;

export default function Dashboard({ initialLeads }: { initialLeads: Lead[] }) {
  const [leads, setLeads] = useState(initialLeads);
  const [addLeadsOpen, setAddLeadsOpen] = useState(false);
  const [running, setRunning] = useState(false);
  const [rows, setRows] = useState<RowRunState[]>([]);
  const [toast, setToast] = useState<ToastState>(null);
  const [highlightedIds, setHighlightedIds] = useState<Set<number>>(new Set());
  const [deleteAllOpen, setDeleteAllOpen] = useState(false);
  const [deletingAll, setDeletingAll] = useState(false);

  async function handleDeleteAll() {
    setDeletingAll(true);
    try {
      const { deleted } = await deleteAllLeads();
      setLeads([]);
      setDeleteAllOpen(false);
      setToast({ message: `Deleted ${deleted} lead${deleted === 1 ? "" : "s"}.`, tone: "success" });
    } catch (err) {
      setToast({
        message: err instanceof Error ? err.message : "Failed to delete all leads",
        tone: "error",
      });
    } finally {
      setDeletingAll(false);
    }
  }

  async function handleRun(inputs: RawLeadInput[]) {
    if (inputs.length === 0) return;

    setRunning(true);
    setRows(inputs.map((input, i) => ({ key: String(i), companyName: input.company_name, status: "queued" })));

    const newLeads: Lead[] = [];
    let failedCount = 0;

    for (let i = 0; i < inputs.length; i++) {
      try {
        const lead = await runLeadPipeline(inputs[i], (stage) => {
          setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, status: stage } : r)));
        });
        newLeads.push(lead);
      } catch (err) {
        failedCount += 1;
        setRows((prev) =>
          prev.map((r, idx) =>
            idx === i
              ? { ...r, status: "error", error: err instanceof Error ? err.message : "Failed" }
              : r,
          ),
        );
      }
    }

    setLeads((prev) => [...newLeads].reverse().concat(prev));
    setRunning(false);

    if (newLeads.length > 0) {
      // Success (possibly partial) — close the dialog and surface a clear completion
      // signal instead of silently dropping back to a blank upload form.
      setAddLeadsOpen(false);
      setToast({
        message:
          failedCount > 0
            ? `Scoring complete — ${newLeads.length} of ${inputs.length} leads processed, ${failedCount} failed.`
            : `Scoring complete — ${newLeads.length} lead${newLeads.length === 1 ? "" : "s"} processed.`,
        tone: "success",
      });
      setHighlightedIds(new Set(newLeads.map((l) => l.id)));
      document.getElementById("leads-grid")?.scrollIntoView({ behavior: "smooth", block: "start" });
      setTimeout(() => setHighlightedIds(new Set()), HIGHLIGHT_DURATION_MS);
    } else {
      // Every row failed — keep the dialog open so the per-row error detail in
      // ProcessingPanel stays visible instead of hiding the only diagnostic info.
      setToast({ message: `All ${inputs.length} lead${inputs.length === 1 ? "" : "s"} failed to process.`, tone: "error" });
    }
  }

  return (
    <div className="space-y-6">
      <Toast toast={toast} onDismiss={() => setToast(null)} />

      <Header onAddLeads={() => setAddLeadsOpen(true)} onDeleteAll={() => setDeleteAllOpen(true)} />
      <StatsRow leads={leads} />
      <div className="pt-4">
        <LeadsGrid
          leads={leads}
          onLeadUpdated={(updated) =>
            setLeads((prev) => prev.map((l) => (l.id === updated.id ? updated : l)))
          }
          onLeadDeleted={(id) => setLeads((prev) => prev.filter((l) => l.id !== id))}
          highlightedIds={highlightedIds}
        />
      </div>

      <Dialog
        open={addLeadsOpen}
        onOpenChange={(open) => {
          if (!running) setAddLeadsOpen(open);
        }}
        title="Add leads"
      >
        {running ? <ProcessingPanel rows={rows} /> : <UploadPanel disabled={running} onRun={handleRun} />}
      </Dialog>

      <DeleteAllDialog
        open={deleteAllOpen}
        onOpenChange={setDeleteAllOpen}
        leadCount={leads.length}
        pending={deletingAll}
        onConfirm={handleDeleteAll}
      />
    </div>
  );
}
