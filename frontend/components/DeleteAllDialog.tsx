"use client";

import { useState } from "react";
import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

const CONFIRM_TEXT = "DELETE";

export default function DeleteAllDialog({
  open,
  onOpenChange,
  leadCount,
  pending,
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  leadCount: number;
  pending: boolean;
  onConfirm: () => void;
}) {
  const [confirmText, setConfirmText] = useState("");

  function handleOpenChange(next: boolean) {
    if (!next) setConfirmText("");
    onOpenChange(next);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange} title="Delete all leads">
      <div className="flex flex-col gap-4 p-6">
        <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            This permanently deletes all {leadCount} lead{leadCount === 1 ? "" : "s"} currently in
            the database. This action cannot be undone.
          </p>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground">
            Type <span className="font-semibold text-foreground">{CONFIRM_TEXT}</span> to confirm
          </label>
          <Input
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder={CONFIRM_TEXT}
            disabled={pending}
            autoFocus
          />
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={() => handleOpenChange(false)} disabled={pending}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            size="sm"
            disabled={pending || confirmText !== CONFIRM_TEXT}
            onClick={onConfirm}
          >
            Delete all leads
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
