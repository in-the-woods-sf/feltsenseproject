const steps = [
  {
    number: "01",
    title: "Fetch",
    description: "We scan the target product and retrieve content, assets, and surface area.",
  },
  {
    number: "02",
    title: "Extract",
    description: "Agents identify features, integrations, and technical dependencies.",
  },
  {
    number: "03",
    title: "Score",
    description: "A replicability score from 1 to 100 with feature-level build estimates.",
  },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24 md:py-32">
      <div className="container">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {steps.map((step) => (
            <div
              key={step.number}
              className="bg-[#0F0F0F] p-8 md:p-10"
              style={{
                clipPath: "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
              }}
            >
              <div className="mb-4 flex items-baseline gap-3">
                <span className="font-mono text-3xl text-primary font-medium">{step.number}</span>
                <span className="text-white/30">/</span>
                <span className="font-serif italic text-xl text-white">{step.title}</span>
              </div>
              <p className="font-mono text-sm text-white/70 leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
