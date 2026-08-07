import Dashboard from "@/components/Dashboard";
import Sidebar from "@/components/Sidebar";
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
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="min-w-0 flex-1">
        <div className="mx-auto max-w-[1160px] px-6 py-8">
          {loadError ? (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {loadError}
            </div>
          ) : (
            <Dashboard initialLeads={leads!} />
          )}
        </div>
      </main>
    </div>
  );
}
