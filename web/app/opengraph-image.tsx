import { ImageResponse } from "next/og";

export const dynamic = "force-static";
export const alt = "Sněmovna PSP Video Archive — DataTimes.cz";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const robotoSlabBold = fetch(
  "https://raw.githubusercontent.com/googlefonts/robotoslab/main/fonts/ttf/RobotoSlab-Bold.ttf"
).then((r) => r.arrayBuffer());

const robotoSlabRegular = fetch(
  "https://raw.githubusercontent.com/googlefonts/robotoslab/main/fonts/ttf/RobotoSlab-Regular.ttf"
).then((r) => r.arrayBuffer());

// Palette
const NEWSPRINT = "#fdfbf7";
const CRIMSON   = "#de1743";
const NAVY9     = "#101432";
const NAVY6     = "#6267a3";
const YELLOW7   = "#efb704";
const SURFACE2  = "#f8f6f0";
const BORDER    = "#e8e8dc";

export default async function OgImage() {
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

        {/* Content */}
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
            <span style={{ color: NAVY6, fontWeight: 700, fontSize: 24 }}>/videoarchiv</span>
          </div>

          {/* Middle: main content */}
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            {/* Badge icon inline */}
            <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
              <div
                style={{
                  width: 80,
                  height: 80,
                  borderRadius: "16px 0 16px 16px",
                  background: `linear-gradient(90deg, ${CRIMSON} 0%, ${NAVY9} 100%)`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <span style={{ color: YELLOW7, fontSize: 44, fontWeight: 700, lineHeight: 1 }}>S</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <span
                  style={{
                    background: CRIMSON,
                    color: "#fff",
                    fontSize: 13,
                    fontWeight: 700,
                    letterSpacing: "0.15em",
                    padding: "4px 12px",
                    borderRadius: 4,
                    textTransform: "uppercase",
                  }}
                >
                  PSP Video Archive
                </span>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <span
                style={{
                  color: NAVY9,
                  fontSize: 58,
                  fontWeight: 700,
                  lineHeight: 1.15,
                  letterSpacing: "-0.5px",
                }}
              >
                Přepisy a souhrny akcí Poslanecké sněmovny
              </span>
              <span style={{ color: NAVY6, fontSize: 26, fontWeight: 400, lineHeight: 1.5 }}>
                Semináře · Konference · Kulatý stůl · Jednání výborů
              </span>
            </div>
          </div>

          {/* Bottom: meta strip */}
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
