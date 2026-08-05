import { Sparkles } from "lucide-react";

export default function Header() {
  return (
    <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-3 px-6 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <h1 className="text-sm font-semibold leading-none">Lead Qualifier Agent</h1>
          <p className="text-xs text-muted-foreground">Enrichment &amp; outreach dashboard</p>
        </div>
      </div>
    </header>
  );
}
