import { getAllSummaries } from "@/lib/summaries";
import { qualityLabel } from "@/lib/types";
import { NextResponse } from "next/server";

export const dynamic = "force-static";

const CANONICAL = "https://snemovna.datatimes.cz/digest";

export function GET() {
  const summaries = getAllSummaries();
  const events = summaries.map((s) => ({
    id: s.event.id,
    name: s.event.name,
    date: s.event.start_date,
    category: s.event.classification,
    quality: qualityLabel(s.transcription.parts_transcribed, s.transcription.parts_total),
    topic: s.summary.topic.split("\n")[0].slice(0, 200),
    speakers: s.entities.speakers.map((sp) => sp.name),
    highlights: s.highlights?.length ?? 0,
    controversies: s.controversial?.length ?? 0,
    url: `${CANONICAL}/events/${s.event.id}`,
  }));
  return NextResponse.json(events);
}
