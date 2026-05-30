import { ImageResponse } from "next/og";
import { getAllSummaries } from "@/lib/summaries";

export const dynamic = "force-static";
export const alt = "Archiv akcí — Sněmovna Digest";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const robotoSlabBold = fetch(
  "https://raw.githubusercontent.com/googlefonts/robotoslab/main/fonts/ttf/RobotoSlab-Bold.ttf"
).then((r) => r.arrayBuffer());

const robotoSlabRegular = fetch(
  "https://raw.githubusercontent.com/googlefonts/robotoslab/main/fonts/ttf/RobotoSlab-Regular.ttf"
).then((r) => r.arrayBuffer());

const NEWSPRINT = "#fdfbf7";
const CRIMSON   = "#de1743";
const NAVY9     = "#101432";
const NAVY6     = "#6267a3";
const YELLOW7   = "#efb704";
const SURFACE2  = "#f8f6f0";
const BORDER    = "#e8e8dc";

const CATEGORY_COLOR: Record<string, string> = {
  "Seminář":            CRIMSON,
  "Konference":         CRIMSON,
  "Kulatý stůl":        NAVY6,
  "Veřejné slyšení":    "#0e839e",
  "Tiskové konference": NAVY9,
  "Jednání výborů":     "#272a59",
};

export default async function OgImage() {
  const summaries = getAllSummaries();
  const total = summaries.length;

  const categoryCounts = summaries.reduce<Record<string, number>>((acc, s) => {
    acc[s.event.classification] = (acc[s.event.classification] ?? 0) + 1;
    return acc;
  }, {});

  const categories = Object.entries(categoryCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  const [boldFont, regularFont] = await Promise.all([robotoSlabBold, robotoSlabRegular]);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          background: NEWSPRINT,
          fontFamily: "Roboto Slab, Georgia, serif",
        }}
      >
        {/* Left crimson strip */}
        <div style={{ width: 16, background: CRIMSON, flexShrink: 0 }} />

        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            padding: "56px 72px 52px 64px",
          }}
        >
          {/* Top: logotype */}
          <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
            <span style={{ color: CRIMSON, fontWeight: 700, fontSize: 24 }}>Sněmovna</span>
            <span style={{ color: YELLOW7, fontWeight: 700, fontSize: 24 }}>.</span>
            <span style={{ color: NAVY9, fontWeight: 700, fontSize: 24 }}>DataTimes</span>
            <span style={{ color: YELLOW7, fontWeight: 700, fontSize: 24 }}>.</span>
            <span style={{ color: NAVY9, fontWeight: 700, fontSize: 24 }}>cz</span>
            <span style={{ color: NAVY6, fontWeight: 700, fontSize: 24 }}>/digest</span>
          </div>

          {/* Middle */}
          <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <span style={{ color: NAVY9, fontSize: 64, fontWeight: 700, lineHeight: 1.1, letterSpacing: "-0.5px" }}>
                Archiv akcí PSP
              </span>
              <span style={{ color: NAVY6, fontSize: 26, fontWeight: 400 }}>
                {total} shrnutých akcí Poslanecké sněmovny ČR
              </span>
            </div>

            {/* Category pills */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              {categories.map(([cat, count]) => (
                <div
                  key={cat}
                  style={{
                    background: CATEGORY_COLOR[cat] ?? NAVY9,
                    color: "#fff",
                    fontSize: 15,
                    fontWeight: 700,
                    letterSpacing: "0.05em",
                    padding: "6px 16px",
                    borderRadius: "6px 0 6px 6px",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  {cat}
                  <span style={{ opacity: 0.75, fontWeight: 400 }}>{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              borderTop: `2px solid ${BORDER}`,
              paddingTop: 20,
            }}
          >
            <span style={{ color: NAVY6, fontSize: 18, fontWeight: 400 }}>
              Přepisy AI · Souhrny AI · Fakta PSP ČR
            </span>
            <div
              style={{
                background: SURFACE2,
                border: `1px solid ${BORDER}`,
                borderRadius: 8,
                padding: "8px 20px",
                display: "flex",
                alignItems: "center",
              }}
            >
              <span style={{ color: NAVY9, fontSize: 16, fontWeight: 700 }}>datatimes.cz</span>
            </div>
          </div>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: "Roboto Slab", data: boldFont,    weight: 700, style: "normal" },
        { name: "Roboto Slab", data: regularFont, weight: 400, style: "normal" },
      ],
    }
  );
}
