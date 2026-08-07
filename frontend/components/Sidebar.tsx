"use client";

import { IconLayoutDashboard, IconSettings, IconSparkles, IconUsers } from "@tabler/icons-react";

const NAV_ITEMS = [
  { icon: IconLayoutDashboard, label: "Dashboard", active: false },
  { icon: IconUsers, label: "Leads", active: true },
  { icon: IconSettings, label: "Settings", active: false },
];

export default function Sidebar() {
  return (
    <aside className="sticky top-0 flex h-screen w-14 shrink-0 flex-col items-center gap-6 bg-sidebar py-4">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
        <IconSparkles className="h-5 w-5" stroke={1.75} />
      </div>
      <nav className="flex flex-col gap-2">
        {NAV_ITEMS.map(({ icon: Icon, label, active }) => (
          <button
            key={label}
            aria-label={label}
            title={label}
            className={`flex h-9 w-9 items-center justify-center rounded-lg transition-colors ${
              active
                ? "bg-primary text-primary-foreground"
                : "text-sidebar-foreground/50 hover:bg-secondary hover:text-sidebar-foreground"
            }`}
          >
            <Icon className="h-5 w-5" stroke={1.75} />
          </button>
        ))}
      </nav>
    </aside>
  );
}
