import Link from "next/link";

const LINKS = [
  { href: "/", label: "Check" },
  { href: "/how-it-works", label: "How it works" },
  { href: "/evaluation", label: "Evaluation" },
];

export default function Nav() {
  return (
    <header className="bg-primary text-primary-foreground">
      <nav className="mx-auto flex max-w-2xl flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3">
        <Link href="/" className="mr-auto text-lg font-bold tracking-tight">
          FwdMD
        </Link>
        {LINKS.map((l) => (
          <Link key={l.href} href={l.href} className="text-sm underline-offset-4 hover:underline">
            {l.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
