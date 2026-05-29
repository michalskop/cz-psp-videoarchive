import Link from "next/link";
import { PspLogotype } from "./PspLogotype";

export function SiteHeader() {
  return (
    <header className="w-full border-b border-border bg-surface-0 sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        <Link href="/" className="hover:opacity-80 transition-opacity flex-shrink-0">
          <PspLogotype size="md" />
        </Link>
        <nav className="flex items-center gap-1 text-sm font-sans font-medium">
          <Link
            href="/events"
            className="px-3 py-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-surface-2 transition-colors"
          >
            Akce
          </Link>
        </nav>
      </div>
    </header>
  );
}
