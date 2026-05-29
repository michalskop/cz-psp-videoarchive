import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "PSP Video Archive",
    template: "%s | PSP Video Archive",
  },
  description:
    "Strukturované souhrny akcí Poslanecké sněmovny ČR — semináře, konference, výbory.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="cs" className="h-full">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@400;500;600;700&family=Work+Sans:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col bg-newsprint text-ink font-slab antialiased">
        <nav className="border-b border-border-cream bg-white/70 backdrop-blur-sm sticky top-0 z-10">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-6">
            <a href="/" className="font-slab font-bold text-crimson text-lg leading-none">
              PSP Video Archive
            </a>
            <div className="flex gap-4 text-sm font-sans">
              <a href="/events" className="text-ink hover:text-crimson transition-colors">
                Akce
              </a>
            </div>
          </div>
        </nav>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-border-cream mt-12 py-6 text-center text-sm font-sans text-neutral-500">
          Data: <a href="https://www.psp.cz" className="hover:text-crimson">PSP ČR</a> •{" "}
          Souhrny: AI (Gemini / Groq) •{" "}
          <a href="/llms.txt" className="hover:text-crimson">llms.txt</a>
        </footer>
      </body>
    </html>
  );
}
