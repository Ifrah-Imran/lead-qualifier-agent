import { CheckCircle2, Clock, Star, Users } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Lead } from "@/lib/api";

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Users;
  label: string;
  value: string;
}) {
  return (
    <Card className="flex flex-col gap-3 p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{label}</span>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <span className="text-3xl font-semibold tracking-tight text-foreground">{value}</span>
    </Card>
  );
}

export default function StatsRow({ leads }: { leads: Lead[] }) {
  const total = leads.length;
  const approved = leads.filter((l) => l.status === "Approved").length;
  const pending = leads.filter((l) => l.status === "New").length;
  const scored = leads.filter((l): l is Lead & { score: number } => l.score !== null);
  const avgScore =
    scored.length === 0
      ? "—"
      : (scored.reduce((sum, l) => sum + l.score, 0) / scored.length).toFixed(1);

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard icon={Users} label="Total leads" value={String(total)} />
      <StatCard icon={CheckCircle2} label="Approved" value={String(approved)} />
      <StatCard icon={Star} label="Avg score" value={avgScore} />
      <StatCard icon={Clock} label="Pending review" value={String(pending)} />
    </div>
  );
}
