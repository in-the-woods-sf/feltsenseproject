"use client";

import { useState } from "react";
import { Button } from "./ui/button";

export function UrlInputSection() {
  const [url, setUrl] = useState("");

  return (
    <section id="analyze" className="py-24 md:py-32 relative">
      <div className="container max-w-4xl mx-auto">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://speak.com"
              className="w-full h-16 px-6 bg-transparent border border-border font-mono text-foreground placeholder:text-foreground/30 focus:outline-none focus:border-primary/50 transition-colors duration-150"
              style={{
                clipPath: "polygon(12px 0, calc(100% - 12px) 0, 100% 12px, 100% calc(100% - 12px), calc(100% - 12px) 100%, 12px 100%, 0 calc(100% - 12px), 0 12px)",
              }}
            />
          </div>
          <Button className="shrink-0">
            [ANALYZE]
          </Button>
        </div>
        <p className="font-mono text-sm text-foreground/40 mt-6 text-center sm:text-left">
          {"// 5 minutes. No signup required for your first analysis."}
        </p>
      </div>
    </section>
  );
}
