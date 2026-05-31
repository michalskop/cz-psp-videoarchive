import Link from "next/link";

export default function NotFound() {
  return (
    <main className="max-w-3xl mx-auto px-4 py-20 text-center">
      <h1 className="font-slab font-bold text-4xl text-navy-9 mb-4">404</h1>
      <p className="font-sans text-lg text-foreground mb-2">Stránka nebyla nalezena.</p>
      <p className="font-sans text-sm text-muted-foreground mb-8">
        Odkaz, který jste použili, pravděpodobně neexistuje nebo byl přesunut.
      </p>
      <Link
        href="/"
        className="font-sans text-sm font-medium text-teal-7 hover:underline"
      >
        ← Zpět na přehled akcí
      </Link>
    </main>
  );
}
