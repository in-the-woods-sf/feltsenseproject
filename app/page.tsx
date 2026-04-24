'use client'

import { Hero } from "@/components/hero";
import { UrlInputSection } from "@/components/url-input-section";
import { HowItWorksSection } from "@/components/how-it-works-section";
import { SampleReportSection } from "@/components/sample-report-section";
import { BuiltForSection } from "@/components/built-for-section";
import { StatsSection } from "@/components/stats-section";
import { FinalCtaSection } from "@/components/final-cta-section";
import { Footer } from "@/components/footer";
import { Leva } from "leva";

export default function Home() {
  return (
    <>
      <Hero />
      <UrlInputSection />
      <HowItWorksSection />
      <SampleReportSection />
      <BuiltForSection />
      <StatsSection />
      <FinalCtaSection />
      <Footer />
      <Leva hidden />
    </>
  );
}
