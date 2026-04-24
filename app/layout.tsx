import type { Metadata } from "next";
import { Geist_Mono, Instrument_Serif } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/header";

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument-serif",
  subsets: ["latin"],
  weight: "400",
  style: "italic",
});

export const metadata: Metadata = {
  title: "GutCheck | Agent-Based Replicability Analysis",
  description: "Paste a URL, get a feature breakdown, replication score, and build estimate. Agent-based replicability analysis for any web product.",
  generator: "v0.app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistMono.variable} ${instrumentSerif.variable} antialiased bg-background`}
        suppressHydrationWarning
      >
        <Header />
        {children}
      </body>
    </html>
  );
}
