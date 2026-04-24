import Link from "next/link";
import { Button } from "./ui/button";

export function FinalCtaSection() {
  return (
    <section className="py-24 md:py-32">
      <div className="container text-center">
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-light mb-6">
          Start with a <span className="font-serif italic">gut check</span>.
        </h2>
        <p className="font-mono text-foreground/50 mb-12">
          Your first analysis is free.
        </p>
        <Link href="#analyze">
          <Button>
            [ANALYZE A URL]
          </Button>
        </Link>
      </div>
    </section>
  );
}
