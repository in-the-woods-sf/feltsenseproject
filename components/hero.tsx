"use client";

import Link from "next/link";
import { GL } from "./gl";
import { Pill } from "./pill";
import { Button } from "./ui/button";
import { useState } from "react";

export function Hero() {
  const [hovering, setHovering] = useState(false);
  return (
    <div className="flex flex-col h-svh justify-between">
      <GL hovering={hovering} />

      <div className="pb-16 mt-auto text-center relative">
        <Pill className="mb-6">LIVE ANALYSIS</Pill>
        <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-light tracking-tight">
          Analyze any product in{" "}
          <span className="font-serif italic">minutes</span>
        </h1>
        <p className="font-mono text-sm sm:text-base text-foreground/50 text-balance mt-8 max-w-[520px] mx-auto leading-relaxed">
          Agent-based replicability analysis for any startup.
          <br />
          Paste a URL, get a feature breakdown, replication score, and build estimate.
        </p>

        <Link className="contents max-sm:hidden" href="#analyze">
          <Button
            className="mt-14"
            onMouseEnter={() => setHovering(true)}
            onMouseLeave={() => setHovering(false)}
          >
            [ANALYZE A URL]
          </Button>
        </Link>
        <Link className="contents sm:hidden" href="#analyze">
          <Button
            size="sm"
            className="mt-14"
            onMouseEnter={() => setHovering(true)}
            onMouseLeave={() => setHovering(false)}
          >
            [ANALYZE A URL]
          </Button>
        </Link>
        
        <div className="mt-6">
          <Link 
            href="#sample-report" 
            className="font-mono text-sm text-foreground/50 hover:text-foreground/80 transition-colors duration-150"
          >
            See a sample report →
          </Link>
        </div>
      </div>
    </div>
  );
}
