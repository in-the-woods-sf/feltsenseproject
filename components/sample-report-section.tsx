"use client";

const scores = [
  { label: "Product", value: 55 },
  { label: "GTM", value: 66 },
  { label: "Physical Infra", value: 10 },
  { label: "Talent & Domain", value: 45 },
];

const features = [
  { name: "AI-Powered Conversational Practice", category: "Core Features", difficulty: 7, cost: "$$", description: "Real-time AI tutor for spoken language practice with adaptive responses" },
  { name: "Instant Spoken Feedback and Correction", category: "Core Features", difficulty: 8, cost: "$$", description: "Immediate pronunciation and grammar feedback using speech recognition" },
  { name: "Personalized Language Curriculum", category: "Content Management", difficulty: 6, cost: "$", description: "Adaptive learning paths based on user progress and goals" },
  { name: "Multi-Language Support", category: "Integrations", difficulty: 6, cost: "$", description: "Support for multiple major world languages with localized content" },
  { name: "Mobile and Web App Availability", category: "Core Features", difficulty: 3, cost: "$", description: "Cross-platform availability on iOS, Android, and web browsers" },
  { name: "Progress Tracking and Motivation Tools", category: "Analytics", difficulty: 3, cost: "$", description: "Streaks, achievements, and learning analytics dashboard" },
  { name: "Realistic Conversational Scenarios", category: "Content Management", difficulty: 4, cost: "$", description: "Role-play situations for practical language application" },
  { name: "User Account Management", category: "User Management", difficulty: 1, cost: "$", description: "Profile settings, preferences, and subscription management" },
  { name: "Freemium Trial and Subscription Management", category: "Core Features", difficulty: 2, cost: "$", description: "Free tier with premium subscription upsell flows" },
  { name: "Customer Support Access", category: "Collaboration", difficulty: 1, cost: "$", description: "Help center, chat support, and FAQ integration" },
  { name: "App Store Distribution and Reviews", category: "Core Features", difficulty: 4, cost: "$", description: "App store presence with ratings and review management" },
  { name: "Language Roadmap Waitlist/Feedback Loop", category: "Collaboration", difficulty: 2, cost: "$", description: "Community feedback collection for new language requests" },
];

const categoryStats = [
  { category: "Core Features", count: 5, avgDifficulty: 4.8, type: "Digital", time: "1–3 days" },
  { category: "Content Management", count: 2, avgDifficulty: 5.0, type: "Digital", time: "1–3 days" },
  { category: "Integrations", count: 1, avgDifficulty: 6.0, type: "Digital", time: "3–7 days" },
  { category: "Analytics", count: 1, avgDifficulty: 3.0, type: "Digital", time: "Hours–1 day" },
  { category: "User Management", count: 1, avgDifficulty: 1.0, type: "Digital", time: "Minutes–Hours" },
  { category: "Collaboration", count: 2, avgDifficulty: 1.5, type: "Digital", time: "Minutes–Hours" },
];

export function SampleReportSection() {
  return (
    <section id="sample-report" className="relative z-10">
      {/* Section Label - On dark background above the cream section */}
      <div className="py-16 text-center">
        <span className="font-mono text-xs text-[#6B6B68] uppercase tracking-widest">// SAMPLE ANALYSIS</span>
      </div>

      {/* Full-width warm off-white/cream section - using inline style to ensure it renders */}
      <div style={{ backgroundColor: "#FAF7F2", width: "100%" }}>
        <div className="max-w-6xl mx-auto px-6 md:px-12 py-16 md:py-20">
          
          {/* REPORT HEADER ROW */}
          <div className="pb-10 border-b" style={{ borderColor: "#E8E3D8" }}>
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-8">
              {/* Left - Product info */}
              <div>
                <h3 className="font-serif italic text-5xl md:text-6xl" style={{ color: "#0F0F0F" }}>Speak</h3>
                <p className="font-mono text-sm mt-3 mb-1" style={{ color: "#6B6B68" }}>speak.com</p>
                <p className="font-mono text-xs uppercase tracking-wider" style={{ color: "#6B6B68" }}>// ANALYZED 04.22.2026</p>
              </div>

              {/* Right - Score */}
              <div className="text-left lg:text-right">
                <p className="font-mono text-xs uppercase tracking-wider mb-2" style={{ color: "#6B6B68" }}>REPLICABILITY SCORE</p>
                <div className="flex items-baseline gap-1 lg:justify-end">
                  <span className="font-mono text-7xl md:text-8xl leading-none" style={{ color: "#D4A017" }}>56</span>
                  <span className="font-mono text-2xl" style={{ color: "#0F0F0F" }}>/100</span>
                </div>
                <div className="mt-4">
                  <span className="inline-block font-mono text-xs uppercase tracking-wider px-4 py-2" style={{ backgroundColor: "#D4A017", color: "#0F0F0F" }}>
                    STRONG BARRIERS
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* SCORE BREAKDOWN */}
          <div className="py-10 border-b" style={{ borderColor: "#E8E3D8" }}>
            <p className="font-mono text-xs uppercase tracking-wider mb-8" style={{ color: "#6B6B68" }}>// SCORE BREAKDOWN</p>
            <div className="space-y-0">
              {scores.map((score, index) => (
                <div key={score.label}>
                  <div className="flex items-center gap-6 py-4">
                    <span className="w-36 shrink-0" style={{ color: "#0F0F0F" }}>{score.label}</span>
                    <div className="flex-1 h-1 overflow-hidden" style={{ backgroundColor: "#E8E3D8" }}>
                      <div 
                        className="h-full"
                        style={{ width: `${score.value}%`, backgroundColor: "#D4A017" }}
                      />
                    </div>
                    <span className="font-mono text-lg w-10 text-right" style={{ color: "#0F0F0F" }}>{score.value}</span>
                  </div>
                  {index < scores.length - 1 && <div className="h-px" style={{ backgroundColor: "#E8E3D8" }} />}
                </div>
              ))}
            </div>
          </div>

          {/* TOTAL COST TO REPLICATE */}
          <div className="py-10 border-b" style={{ borderColor: "#E8E3D8" }}>
            <p className="font-mono text-xs uppercase tracking-wider mb-8" style={{ color: "#6B6B68" }}>// TOTAL COST TO REPLICATE</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {/* Card 1: Compute */}
              <div 
                className="p-6"
                style={{ 
                  backgroundColor: "#0F0F0F",
                  clipPath: "polygon(12px 0, calc(100% - 12px) 0, 100% 12px, 100% calc(100% - 12px), calc(100% - 12px) 100%, 12px 100%, 0 calc(100% - 12px), 0 12px)" 
                }}
              >
                <p className="font-mono text-xs uppercase tracking-wider mb-1" style={{ color: "#D4A017" }}>// 01 / COMPUTE</p>
                <p className="text-sm mb-4" style={{ color: "rgba(255,255,255,0.6)" }}>Agentic build portion</p>
                <p className="font-mono text-2xl md:text-3xl mb-4" style={{ color: "#D4A017" }}>$8K — $24K</p>
                <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.8)" }}>
                  Cost of AI-assisted engineering to build the replicable digital surface area. Covers inference, tooling, and agent orchestration for the 12 identified features.
                </p>
              </div>

              {/* Card 2: Human */}
              <div 
                className="p-6"
                style={{ 
                  backgroundColor: "#0F0F0F",
                  clipPath: "polygon(12px 0, calc(100% - 12px) 0, 100% 12px, 100% calc(100% - 12px), calc(100% - 12px) 100%, 12px 100%, 0 calc(100% - 12px), 0 12px)" 
                }}
              >
                <p className="font-mono text-xs uppercase tracking-wider mb-1" style={{ color: "#D4A017" }}>// 02 / HUMAN</p>
                <p className="text-sm mb-4" style={{ color: "rgba(255,255,255,0.6)" }}>Where agents stop, humans start</p>
                <p className="font-mono text-2xl md:text-3xl mb-4" style={{ color: "#D4A017" }}>$45K — $120K</p>
                <p className="text-sm leading-relaxed mb-3" style={{ color: "rgba(255,255,255,0.8)" }}>
                  Specialist hires to finish what agents can&apos;t — applied NLP engineering, curriculum design, and multi-language feedback tuning.
                </p>
                <p className="font-mono text-xs" style={{ color: "rgba(255,255,255,0.5)" }}>~4–8 weeks of specialist time</p>
              </div>

              {/* Card 3: Go-to-Market */}
              <div 
                className="p-6"
                style={{ 
                  backgroundColor: "#0F0F0F",
                  clipPath: "polygon(12px 0, calc(100% - 12px) 0, 100% 12px, 100% calc(100% - 12px), calc(100% - 12px) 100%, 12px 100%, 0 calc(100% - 12px), 0 12px)" 
                }}
              >
                <p className="font-mono text-xs uppercase tracking-wider mb-1" style={{ color: "#D4A017" }}>// 03 / GO-TO-MARKET</p>
                <p className="text-sm mb-4" style={{ color: "rgba(255,255,255,0.6)" }}>Budget to penetrate the market</p>
                <p className="font-mono text-2xl md:text-3xl mb-4" style={{ color: "#D4A017" }}>$500K — $2M+</p>
                <p className="text-sm leading-relaxed mb-3" style={{ color: "rgba(255,255,255,0.8)" }}>
                  Marketing, CAC, and brand-building spend for market penetration. Benchmarked against Duolingo, Babbel, Busuu.
                </p>
                <p className="font-mono text-xs" style={{ color: "rgba(255,255,255,0.5)" }}>Largest barrier to replication</p>
              </div>
            </div>

            {/* Total Summary Row */}
            <div className="border p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4" style={{ backgroundColor: "white", borderColor: "#E8E3D8" }}>
              <p className="font-mono text-xs uppercase tracking-wider" style={{ color: "#0F0F0F" }}>// TOTAL ESTIMATED REPLICATION COST</p>
              <p className="font-mono text-3xl md:text-4xl" style={{ color: "#D4A017" }}>$553K — $2.14M</p>
            </div>
          </div>

          {/* TWO-COLUMN BLOCK */}
          <div className="py-10 border-b" style={{ borderColor: "#E8E3D8" }}>
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-10">
              {/* Left Column (60%) */}
              <div className="lg:col-span-3 space-y-10">
                {/* AI Summary */}
                <div>
                  <p className="font-mono text-xs uppercase tracking-wider mb-4" style={{ color: "#6B6B68" }}>// AI SUMMARY</p>
                  <p className="leading-relaxed mb-4" style={{ color: "#0F0F0F" }}>
                    Speak is an AI-driven language learning app specializing in spoken language practice with an interactive virtual tutor. Instead of human teachers, it offers real-time feedback, personalized curricula, and conversational experiences in major world languages.
                  </p>
                  <p className="leading-relaxed" style={{ color: "#0F0F0F" }}>
                    The product accelerates speaking fluency and motivation, differentiating through immersive tailored experiences on mobile and web.
                  </p>
                </div>

                {/* Key Differentiators */}
                <div>
                  <p className="font-mono text-xs uppercase tracking-wider mb-4" style={{ color: "#6B6B68" }}>// KEY DIFFERENTIATORS</p>
                  <ul className="space-y-3">
                    {[
                      "24/7 AI-powered conversational partner",
                      "Instant spoken feedback without human tutors",
                      "Personalized curriculum adapting to progress",
                      "Multi-language support with spoken dialogue",
                      "Trusted by millions with strong brand equity",
                    ].map((item, index) => (
                      <li key={index} className="flex items-start gap-3">
                        <span className="font-medium" style={{ color: "#D4A017" }}>—</span>
                        <span style={{ color: "#0F0F0F" }}>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Right Column (40%) - Stats Card */}
              <div className="lg:col-span-2">
                <div style={{ backgroundColor: "#0F0F0F" }}>
                  <div className="p-5" style={{ borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
                    <p className="font-mono text-xs uppercase tracking-wider mb-1" style={{ color: "rgba(255,255,255,0.5)" }}>TOTAL FEATURES</p>
                    <p className="font-mono text-3xl" style={{ color: "#D4A017" }}>12</p>
                  </div>
                  <div className="p-5" style={{ borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
                    <p className="font-mono text-xs uppercase tracking-wider mb-1" style={{ color: "rgba(255,255,255,0.5)" }}>BUILD TIME</p>
                    <p className="font-mono text-3xl" style={{ color: "#D4A017" }}>2–4 weeks</p>
                  </div>
                  <div className="p-5" style={{ borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
                    <p className="font-mono text-xs uppercase tracking-wider mb-1" style={{ color: "rgba(255,255,255,0.5)" }}>DIGITAL / PHYSICAL</p>
                    <p className="font-mono text-3xl" style={{ color: "#D4A017" }}>100% / 0%</p>
                    <div className="mt-2 h-2" style={{ backgroundColor: "rgba(255,255,255,0.2)" }}>
                      <div className="h-full" style={{ width: "100%", backgroundColor: "#D4A017" }} />
                    </div>
                  </div>
                  <div className="p-5">
                    <p className="font-mono text-xs uppercase tracking-wider mb-1" style={{ color: "rgba(255,255,255,0.5)" }}>ANALYSIS DEPTH</p>
                    <p className="font-mono text-xl" style={{ color: "white" }}>Agent-based</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* FEATURE CATEGORY TABLE */}
          <div className="py-10 border-b" style={{ borderColor: "#E8E3D8" }}>
            <p className="font-mono text-xs uppercase tracking-wider mb-8" style={{ color: "#6B6B68" }}>// REPLICATION DIFFICULTY BY CATEGORY</p>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr style={{ borderBottom: "1px solid #E8E3D8" }}>
                    <th className="font-mono text-xs uppercase tracking-wider text-left py-4 pr-4" style={{ color: "#6B6B68" }}>CATEGORY</th>
                    <th className="font-mono text-xs uppercase tracking-wider text-center py-4 px-4" style={{ color: "#6B6B68" }}># FEATURES</th>
                    <th className="font-mono text-xs uppercase tracking-wider text-center py-4 px-4" style={{ color: "#6B6B68" }}>AVG. DIFFICULTY</th>
                    <th className="font-mono text-xs uppercase tracking-wider text-center py-4 px-4" style={{ color: "#6B6B68" }}>TYPE</th>
                    <th className="font-mono text-xs uppercase tracking-wider text-right py-4 pl-4" style={{ color: "#6B6B68" }}>EST. BUILD TIME</th>
                  </tr>
                </thead>
                <tbody>
                  {categoryStats.map((cat, index) => (
                    <tr key={index} style={{ borderBottom: index < categoryStats.length - 1 ? "1px solid #E8E3D8" : "none" }}>
                      <td className="py-4 pr-4" style={{ color: "#0F0F0F" }}>{cat.category}</td>
                      <td className="font-mono text-center py-4 px-4" style={{ color: "#0F0F0F" }}>{cat.count}</td>
                      <td className="font-mono text-center py-4 px-4" style={{ color: "#D4A017" }}>{cat.avgDifficulty.toFixed(1)}</td>
                      <td className="text-center py-4 px-4" style={{ color: "#6B6B68" }}>{cat.type}</td>
                      <td className="text-right py-4 pl-4" style={{ color: "#6B6B68" }}>{cat.time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* EXTRACTED FEATURES LIST */}
          <div className="pt-10">
            <p className="font-mono text-xs uppercase tracking-wider mb-4" style={{ color: "#6B6B68" }}>// EXTRACTED FEATURES (12)</p>
            
            {/* Legend */}
            <p className="font-mono text-xs mb-2" style={{ color: "#6B6B68" }}>
              Cost to replicate (AI-assisted compute only): $ &lt;$5K | $$ $5K–$25K | $$$ $25K–$100K | $$$$ $100K+
            </p>
            <p className="font-mono text-xs mb-8" style={{ color: "#6B6B68" }}>
              // Feature-level costs reflect compute layer. See Total Cost to Replicate above for full human + GTM breakdown.
            </p>

            <div className="space-y-3">
              {features.map((feature, index) => (
                <div 
                  key={index} 
                  className="border p-5"
                  style={{ 
                    backgroundColor: "white", 
                    borderColor: "#E8E3D8",
                    clipPath: "polygon(6px 0, calc(100% - 6px) 0, 100% 6px, 100% calc(100% - 6px), calc(100% - 6px) 100%, 6px 100%, 0 calc(100% - 6px), 0 6px)" 
                  }}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                    <span className="font-medium" style={{ color: "#0F0F0F" }}>{feature.name}</span>
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="font-mono text-xs border px-2 py-1" style={{ color: "#6B6B68", borderColor: "#E8E3D8" }}>Digital</span>
                      <span className="font-mono text-xs border px-2 py-1" style={{ color: "#6B6B68", borderColor: "#E8E3D8" }}>{feature.category}</span>
                      <span className="font-mono text-sm" style={{ color: "#D4A017" }}>{feature.difficulty}/10</span>
                      <span className="font-mono text-sm" style={{ color: "#D4A017" }}>{feature.cost}</span>
                    </div>
                  </div>
                  <p className="text-sm" style={{ color: "#6B6B68" }}>{feature.description}</p>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
