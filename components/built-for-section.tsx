import { px } from "./utils";

const personas = [
  {
    label: "PRODUCT MANAGERS",
    description: "Benchmark your roadmap against the market. Know which features competitors have that you don&apos;t, and how hard they&apos;d be to ship.",
    icon: "PM",
  },
  {
    label: "ENTREPRENEURS",
    description: "Validate before you build. Estimate time, cost, and talent needed to replicate any product in your space.",
    icon: "EN",
  },
];

export function BuiltForSection() {
  const polyRoundness = 12;
  const hypotenuse = polyRoundness * 2;
  const hypotenuseHalf = polyRoundness / 2 - 1.5;

  return (
    <section className="py-24 md:py-32">
      <div className="container">
        <p className="font-mono text-xs text-white/40 uppercase tracking-widest text-center mb-12">
          // BUILT FOR
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {personas.map((persona) => (
            <div
              key={persona.label}
              className="relative border border-[#E8E3D8] p-8 hover:border-[#D4A017] transition-colors duration-300"
              style={{
                backgroundColor: "#FAF7F2",
                "--poly-roundness": px(polyRoundness),
                clipPath: "polygon(var(--poly-roundness) 0, calc(100% - var(--poly-roundness)) 0, 100% var(--poly-roundness), 100% calc(100% - var(--poly-roundness)), calc(100% - var(--poly-roundness)) 100%, var(--poly-roundness) 100%, 0 calc(100% - var(--poly-roundness)), 0 var(--poly-roundness))",
              } as React.CSSProperties}
            >
              {/* Corner accents */}
              <span style={{ "--h": px(hypotenuse), "--hh": px(hypotenuseHalf) } as React.CSSProperties} className="absolute inline-block w-[var(--h)] top-[var(--hh)] left-[var(--hh)] h-[1px] -rotate-45 origin-top -translate-x-1/2 bg-[#E8E3D8]" />
              <span style={{ "--h": px(hypotenuse), "--hh": px(hypotenuseHalf) } as React.CSSProperties} className="absolute w-[var(--h)] bottom-[var(--hh)] right-[var(--hh)] h-[1px] -rotate-45 translate-x-1/2 bg-[#E8E3D8]" />

              <div className="flex items-start gap-4 mb-4">
                <div 
                  className="w-10 h-10 flex items-center justify-center shrink-0"
                  style={{
                    backgroundColor: "#D4A017",
                    clipPath: "polygon(4px 0, calc(100% - 4px) 0, 100% 4px, 100% calc(100% - 4px), calc(100% - 4px) 100%, 4px 100%, 0 calc(100% - 4px), 0 4px)",
                  }}
                >
                  <span className="font-mono text-xs text-[#0F0F0F] font-bold">{persona.icon}</span>
                </div>
                <span className="font-mono text-sm text-[#0F0F0F] uppercase tracking-wider pt-2.5 font-medium">
                  {persona.label}
                </span>
              </div>
              <p className="font-sans text-[#6B6B68] leading-relaxed">
                {persona.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
