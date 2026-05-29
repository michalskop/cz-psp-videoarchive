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

function normalizeSummary(raw: unknown): Summary | null {
  if (!raw || typeof raw !== "object") return null;
  const d = raw as Record<string, unknown>;
  if (!d.event || typeof d.event !== "object") return null;

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
        return normalizeSummary(JSON.parse(raw));
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
    return normalizeSummary(JSON.parse(raw));
  } catch {
    return null;
  }
}

export function getAllIds(): string[] {
  return getAllSummaries()
    .filter((s) => s.event.id != null)
    .map((s) => String(s.event.id));
}
