import fs from "fs";
import path from "path";

// ── Types ──────────────────────────────────────────────────────────────────────

export interface Speaker {
  name: string;
  person_id: string | null;
  affiliation: string | null;
}

export interface HighlightItem {
  text: string;
  type: "citation" | "paraphrase";
  speaker: string;
  affiliation: string | null;
  timestamp: string;
  screenshot_path: string | null;
  context: string | null;
}

export interface ControversialItem {
  statement: string;
  speaker: string;
  affiliation: string | null;
  timestamp: string;
  screenshot_path: string | null;
  context: string | null;
}

export interface Summary {
  schema_version: string;
  model_hint: string;
  created_at: string;
  event: {
    id: string;
    name: string;
    classification: string;
    start_date: string;
    end_date: string | null;
    sources: string[];
  };
  transcription: {
    parts_transcribed: number;
    parts_total: number;
    source: string;
    model: string;
  };
  summary: {
    topic: string;
    main_points: string[];
    outcome: string;
    notes: string | null;
  };
  entities: {
    speakers: Speaker[];
  };
  highlights: HighlightItem[] | null;
  controversial: ControversialItem[] | null;
}

// ── Loader ────────────────────────────────────────────────────────────────────

const SUMMARIES_DIR = path.resolve(process.cwd(), "..", "summaries", "json");

function readSummariesDir(): string[] {
  try {
    return fs.readdirSync(SUMMARIES_DIR).filter((f) => f.endsWith(".json"));
  } catch {
    // Fallback for GitHub Actions where JSON files are copied into public/summaries
    return [];
  }
}

export function getAllSummaries(): Summary[] {
  const files = readSummariesDir();
  return files
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
  const files = readSummariesDir();
  const match = files.find((f) => f.includes(`_${id}_`) || f.startsWith(`summary_${id}_`));
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

// ── Helpers ───────────────────────────────────────────────────────────────────

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("cs-CZ", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export function qualityLabel(
  parts_transcribed: number,
  parts_total: number
): "good" | "partial" | "poor" {
  if (parts_total === 0) return "poor";
  const ratio = parts_transcribed / parts_total;
  if (ratio >= 0.9) return "good";
  if (ratio >= 0.5) return "partial";
  return "poor";
}
