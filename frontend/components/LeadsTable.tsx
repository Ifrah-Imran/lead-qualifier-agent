"use client";

import { useState } from "react";
import { Lead, updateLeadStatus } from "@/lib/api";

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
    return <p>No leads yet.</p>;
  }

  return (
    <>
      {error && <p className="error">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Company</th>
            <th>Score</th>
            <th>Status</th>
            <th>Drafted Message</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id}>
              <td>{lead.name}</td>
              <td>{lead.company}</td>
              <td>{lead.score ?? "—"}</td>
              <td>
                <span className={`status status-${lead.status.toLowerCase()}`}>{lead.status}</span>
              </td>
              <td>{lead.drafted_message ?? "—"}</td>
              <td>
                <button
                  disabled={pendingId === lead.id}
                  onClick={() => handleUpdate(lead.id, "Approved")}
                >
                  Approve
                </button>
                <button
                  disabled={pendingId === lead.id}
                  onClick={() => handleUpdate(lead.id, "Rejected")}
                >
                  Reject
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
