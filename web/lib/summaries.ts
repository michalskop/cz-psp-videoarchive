// Server-only: reads summaries from the filesystem at build time
import fs from "fs";
import path from "path";
import type { Summary } from "./types";

export type { Summary, Speaker, HighlightItem, ControversialItem } from "./types";
export { formatDate, qualityLabel, firstThumbnail, pluralCitace, pluralKontroverze } from "./types";

const SUMMARIES_DIR = path.resolve(process.cwd(), "..", "summaries", "json");

function readSummariesDir(): string[] {
  try {
    return fs.readdirSync(SUMMARIES_DIR).filter((f) => f.endsWith(".json"));
  } catch {
    return [];
  }
}

// Extract the event ID from the filename (authoritative — LLM sometimes writes a subevent ID)
function idFromFilename(filename: string): string | null {
  const m = filename.match(/^summary_(\d+)_/);
  return m ? m[1] : null;
}

function normalizeSummary(raw: unknown, filename?: string): Summary | null {
  if (!raw || typeof raw !== "object") return null;
  const d = raw as Record<string, unknown>;
  if (!d.event || typeof d.event !== "object") return null;

  // Override event.id with the filename-derived ID — the LLM sometimes writes
  // the subevent ID (5 digits) instead of the real event ID (4 digits).
  const filenameId = filename ? idFromFilename(filename) : null;
  if (filenameId) {
    (d.event as Record<string, unknown>).id = filenameId;
  }

  // main_points: LLM sometimes returns [{speaker: text}, ...] instead of [string]
  const summary = d.summary as Record<string, unknown> | undefined;
  if (summary && Array.isArray(summary.main_points)) {
    summary.main_points = summary.main_points.map((p: unknown) => {
      if (typeof p === "string") return p;
      if (p && typeof p === "object") {
        return Object.entries(p as Record<string, string>)
          .map(([k, v]) => `**${k}** — ${v}`)
          .join("\n");
      }
      return String(p);
    });
  }

  return d as unknown as Summary;
}

export function getAllSummaries(): Summary[] {
  return readSummariesDir()
    .map((f) => {
      try {
        const raw = fs.readFileSync(path.join(SUMMARIES_DIR, f), "utf-8");
        return normalizeSummary(JSON.parse(raw), f);
      } catch {
        return null;
      }
    })
    .filter(Boolean)
    .sort(
      (a, b) =>
        new Date(b!.event.start_date).getTime() -
        new Date(a!.event.start_date).getTime()
    ) as Summary[];
}

export function getSummaryById(id: string): Summary | null {
  const match = readSummariesDir().find(
    (f) => f.includes(`_${id}_`) || f.startsWith(`summary_${id}_`)
  );
  if (!match) return null;
  try {
    const raw = fs.readFileSync(path.join(SUMMARIES_DIR, match), "utf-8");
    return normalizeSummary(JSON.parse(raw), match);
  } catch {
    return null;
  }
}

export function getAllIds(): string[] {
  return getAllSummaries()
    .filter((s) => s.event.id != null)
    .map((s) => String(s.event.id));
}
