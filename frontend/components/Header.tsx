"use client";

import { Plus, Sparkles, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function Header({
  onAddLeads,
  onDeleteAll,
}: {
  onAddLeads: () => void;
  onDeleteAll: () => void;
}) {
  return (
    <header className="flex items-center justify-between gap-4 py-2">
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Sparkles className="h-4 w-4" />
        </div>
        <h1 className="text-lg font-semibold tracking-tight text-foreground">Lead Qualifier</h1>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outlineDestructive" size="sm" onClick={onDeleteAll}>
          <Trash2 className="h-3.5 w-3.5" />
          Delete all
        </Button>
        <Button onClick={onAddLeads} className="rounded-xl px-5 py-2.5 shadow-sm">
          <Plus className="h-4 w-4" />
          Add leads
        </Button>
      </div>
    </header>
  );
}
