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
    <main>
      <h1>Leads</h1>
      {loadError ? <p className="error">{loadError}</p> : <LeadsTable leads={leads!} />}
    </main>
  );
}
