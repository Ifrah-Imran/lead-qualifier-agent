import Header from "@/components/Header";
import LeadsTable from "@/components/LeadsTable";
import { getLeads } from "@/lib/api";

export default async function Home() {
  let leads;
  let loadError: string | null = null;
  try {
    leads = await getLeads();
  } catch (err) {
    loadError = err instanceof Error ? err.message : "Failed to load leads";
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold tracking-tight">Leads</h2>
          <p className="text-sm text-muted-foreground">
            Review enriched leads, check their fit score, and approve or reject outreach.
          </p>
        </div>
        {loadError ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {loadError}
          </div>
        ) : (
          <LeadsTable leads={leads!} />
        )}
      </main>
    </div>
  );
}
