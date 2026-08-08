export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type LeadStatus = "New" | "Approved" | "Rejected" | (string & {});

export type Lead = {
  id: number;
  name: string;
  company: string;
  title: string | null;
  company_size: string | null;
  industry: string | null;
  linkedin_active_recently: boolean | null;
  estimated_monthly_leads: number | null;
  has_dedicated_sales_role: boolean | null;
  recent_signal: string | null;
  location: string | null;
  phone: string | null;
  social_links: Record<string, string>;
  website_url: string | null;
  score: number | null;
  confidence: string | null;
  reason: string | null;
  drafted_message: string | null;
  status: LeadStatus;
  created_at: string;
};

export async function getLeads(): Promise<Lead[]> {
  const res = await fetch(`${API_URL}/leads`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch leads: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function updateLeadStatus(id: number, status: "Approved" | "Rejected"): Promise<Lead> {
  const res = await fetch(`${API_URL}/leads/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) {
    throw new Error(`Failed to update lead ${id}: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function deleteLead(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/leads/${id}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error(`Failed to delete lead ${id}: ${res.status} ${res.statusText}`);
  }
}

// --- Pipeline endpoints (enrich -> score -> draft -> log), for client-side batch runs ---

export type EnrichRequest = { company_name: string; website_url: string };
export type EnrichResult = {
  company_name: string;
  website_url: string;
  company_size: string | null;
  industry: string | null;
  pages_fetched: number;
  source_urls: string[];
  phone: string | null;
  social_links: Record<string, string>;
};

export type LeadInput = {
  name: string;
  company: string;
  title: string | null;
  company_size: string | number | null;
  industry: string | null;
  linkedin_active_recently: boolean | null;
  estimated_monthly_leads: number | null;
  has_dedicated_sales_role: boolean | null;
  recent_signal: string | null;
  location: string | null;
  phone: string | null;
  social_links: Record<string, string>;
  website_url: string | null;
};

export type LeadScoreResult = {
  score: number;
  confidence: "low" | "medium" | "high";
  reason: string;
};

export type DraftResult = { drafted: boolean; message: string };

export type LogResult = { logged: boolean; id: number; status: string; message: string };

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      // response wasn't JSON — fall back to the status text above
    }
    throw new Error(`${path} failed: ${detail}`);
  }
  return res.json();
}

export function postEnrich(payload: EnrichRequest): Promise<EnrichResult> {
  return postJson<EnrichResult>("/enrich", payload);
}

export function postScore(payload: LeadInput): Promise<LeadScoreResult> {
  return postJson<LeadScoreResult>("/score", payload);
}

export function postDraft(
  payload: LeadInput & { score: number; confidence: string; reason: string },
): Promise<DraftResult> {
  return postJson<DraftResult>("/draft", payload);
}

export function postLog(
  payload: LeadInput & {
    score: number;
    confidence: string;
    reason: string;
    drafted_message: string | null;
    status?: string;
  },
): Promise<LogResult> {
  return postJson<LogResult>("/log", payload);
}
