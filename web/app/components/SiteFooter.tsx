import { PspLogotype } from "./PspLogotype";

function FooterSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs font-sans font-semibold uppercase tracking-wider text-muted-foreground">
        {title}
      </span>
      {children}
    </div>
  );
}

function FooterLink({ href, children }: { href: string; children: React.ReactNode }) {
  const external = href.startsWith("http");
  return (
    <a
      href={href}
      {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      className="text-sm font-sans text-muted-foreground hover:text-foreground transition-colors"
    >
      {children}
    </a>
  );
}

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function SiteFooter() {
  return (
    <footer className="w-full border-t border-border bg-surface-0 mt-auto">
      <div className="max-w-5xl mx-auto px-4 py-10 grid grid-cols-2 sm:grid-cols-4 gap-8">
        <div className="col-span-2 sm:col-span-1 flex flex-col gap-3">
          <PspLogotype size="sm" />
          <p className="text-xs font-sans text-muted-foreground leading-relaxed">
            Strukturované souhrny akcí Poslanecké sněmovny ČR. Data: PSP ČR. Přepisy a souhrny: AI.
          </p>
          <p className="text-xs font-sans text-muted-foreground">
            © {new Date().getFullYear()} DataTimes.cz
          </p>
        </div>

        <FooterSection title="Data">
          <FooterLink href={`${BASE}/llms.txt`}>llms.txt</FooterLink>
          <FooterLink href={`${BASE}/summary.schema.json`}>JSON schéma</FooterLink>
          <FooterLink href={`${BASE}/SKILL.md`}>SKILL.md</FooterLink>
        </FooterSection>

        <FooterSection title="Projekty">
          <FooterLink href="https://datatimes.cz">DataTimes.cz</FooterLink>
          <FooterLink href="https://snemovna.datatimes.cz">Sněmovna.DataTimes.cz</FooterLink>
          <FooterLink href="https://volebnikalkulacka.cz">Volební kalkulačka</FooterLink>
        </FooterSection>

        <FooterSection title="Kontakt">
          <FooterLink href="https://kohovolit.eu">KohoVolit.eu</FooterLink>
          <FooterLink href="https://www.psp.cz">PSP ČR</FooterLink>
        </FooterSection>
      </div>
    </footer>
  );
}
