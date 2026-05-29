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

export function getAllSummaries(): Summary[] {
  return readSummariesDir()
    .map((f) => {
      try {
        const raw = fs.readFileSync(path.join(SUMMARIES_DIR, f), "utf-8");
        return JSON.parse(raw) as Summary;
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
    return JSON.parse(raw) as Summary;
  } catch {
    return null;
  }
}

export function getAllIds(): string[] {
  return getAllSummaries().map((s) => s.event.id);
}
