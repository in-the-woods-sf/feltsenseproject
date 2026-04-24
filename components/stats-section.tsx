const stats = [
  { value: "2,400+", label: "analyses run" },
  { value: "12 min", label: "average report time" },
  { value: "1–100", label: "replication score range" },
];

export function StatsSection() {
  return (
    <section className="py-24 md:py-32">
      <div className="container">
        <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-0">
          {stats.map((stat, index) => (
            <div
              key={stat.label}
              className="relative flex flex-col items-center text-center px-8 md:px-16 py-8 md:py-0"
            >
              {/* Vertical divider for desktop */}
              {index < stats.length - 1 && (
                <div className="hidden md:block absolute right-0 top-1/2 -translate-y-1/2 h-16 w-px bg-primary/20" />
              )}
              {/* Horizontal divider for mobile */}
              {index < stats.length - 1 && (
                <div className="md:hidden absolute bottom-0 left-1/2 -translate-x-1/2 w-32 h-px bg-primary/20" />
              )}

              <span className="text-4xl md:text-5xl font-mono text-primary mb-2">
                {stat.value}
              </span>
              <span className="font-mono text-sm text-foreground/50">
                {stat.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
