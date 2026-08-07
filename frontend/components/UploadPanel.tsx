"use client";

import { useRef, useState } from "react";
import { FileUp, UploadCloud } from "lucide-react";

import { parseLeadsCsv } from "@/lib/csv";
import type { RawLeadInput } from "@/lib/pipeline";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type Mode = "csv" | "quick";

function toRawLeadInputsFromCsv(text: string): { inputs: RawLeadInput[]; errors: string[] } {
  const { rows, errors } = parseLeadsCsv(text);
  const inputs: RawLeadInput[] = rows.map((row) => ({
    company_name: row.company_name,
    website_url: row.website_url,
    name: row.founder_name ?? "Unknown",
    title: row.founder_title,
    location: row.location,
    recent_signal: row.notes,
  }));
  return { inputs, errors };
}

export default function UploadPanel({
  disabled,
  onRun,
}: {
  disabled: boolean;
  onRun: (inputs: RawLeadInput[]) => void;
}) {
  const [mode, setMode] = useState<Mode>("csv");
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [pendingInputs, setPendingInputs] = useState<RawLeadInput[]>([]);
  const [parseErrors, setParseErrors] = useState<string[]>([]);
  const [contactName, setContactName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setFileName(file.name);
    const text = await file.text();
    const { inputs, errors } = toRawLeadInputsFromCsv(text);
    setPendingInputs(inputs);
    setParseErrors(errors);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  function resetCsv() {
    setFileName(null);
    setPendingInputs([]);
    setParseErrors([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function handleQuickTestSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!companyName.trim() || !websiteUrl.trim()) return;
    onRun([
      {
        company_name: companyName.trim(),
        website_url: websiteUrl.trim(),
        name: contactName.trim() || "Unknown",
        title: null,
        location: null,
        recent_signal: null,
      },
    ]);
    setContactName("");
    setCompanyName("");
    setWebsiteUrl("");
  }

  return (
    <div className="flex flex-col gap-5 p-6">
      <p className="text-sm text-muted-foreground">
        Upload a batch of leads or test one company — we&apos;ll enrich, score, and draft outreach
        automatically.
      </p>

      <div className="flex w-fit gap-1 rounded-lg bg-secondary p-1">
        <button
          onClick={() => setMode("csv")}
          className={`rounded-md border px-3 py-1.5 text-sm font-medium transition-colors ${
            mode === "csv" ? "border-border bg-card text-foreground" : "border-transparent text-muted-foreground"
          }`}
        >
          Upload CSV
        </button>
        <button
          onClick={() => setMode("quick")}
          className={`rounded-md border px-3 py-1.5 text-sm font-medium transition-colors ${
            mode === "quick" ? "border-border bg-card text-foreground" : "border-transparent text-muted-foreground"
          }`}
        >
          Quick test
        </button>
      </div>

      {mode === "csv" ? (
        <div className="space-y-3">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
              dragActive ? "border-primary bg-accent/60" : "border-border bg-secondary/40 hover:border-primary/40"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFile(file);
              }}
            />
            {fileName ? (
              <>
                <FileUp className="h-8 w-8 text-foreground" />
                <p className="text-sm font-medium text-foreground">{fileName}</p>
                <p className="text-xs text-muted-foreground">
                  {pendingInputs.length} lead{pendingInputs.length === 1 ? "" : "s"} ready to run
                </p>
              </>
            ) : (
              <>
                <UploadCloud className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm font-medium text-foreground">
                  Drag and drop a CSV, or click to browse
                </p>
                <p className="text-xs text-muted-foreground">
                  Required columns: company_name, website_url. Optional: founder_name,
                  founder_title, location, notes.
                </p>
              </>
            )}
          </div>

          {parseErrors.length > 0 && (
            <div className="space-y-1 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
              {parseErrors.map((err, i) => (
                <p key={i}>{err}</p>
              ))}
            </div>
          )}

          {fileName && (
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={resetCsv} disabled={disabled}>
                Clear
              </Button>
              <Button
                size="sm"
                disabled={disabled || pendingInputs.length === 0}
                onClick={() => onRun(pendingInputs)}
              >
                Run pipeline ({pendingInputs.length})
              </Button>
            </div>
          )}
        </div>
      ) : (
        <form onSubmit={handleQuickTestSubmit} className="flex flex-col gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Contact name <span className="font-normal">(optional)</span>
            </label>
            <Input
              value={contactName}
              onChange={(e) => setContactName(e.target.value)}
              placeholder="Jane Doe"
              disabled={disabled}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Company name</label>
            <Input
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Acme Inc"
              disabled={disabled}
              required
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Website URL</label>
            <Input
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              placeholder="https://acme.com"
              disabled={disabled}
              required
            />
          </div>
          <Button type="submit" disabled={disabled} className="self-end">
            Run test
          </Button>
        </form>
      )}
    </div>
  );
}
