import Link from "next/link";

const footerLinks = {
  Product: [
    { name: "How It Works", href: "#how-it-works" },
    { name: "Portfolios", href: "#portfolios" },
    { name: "Compare", href: "#compare" },
    { name: "Pricing", href: "#pricing" },
  ],
  Company: [
    { name: "About", href: "#about" },
    { name: "Insights", href: "#insights" },
    { name: "Contact", href: "#contact" },
  ],
  Legal: [
    { name: "Privacy", href: "#privacy" },
    { name: "Terms", href: "#terms" },
  ],
};

export function Footer() {
  return (
    <footer className="py-16 border-t border-border/30">
      <div className="container">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-16">
          {/* Brand */}
          <div>
            <div className="font-mono text-foreground mb-2">GutCheck</div>
            <p className="font-mono text-sm text-foreground/40">
              {"// Agent-based replicability analysis"}
            </p>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <div className="font-mono text-sm text-foreground/40 uppercase tracking-wider mb-4">
                {category}
              </div>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.name}>
                    <Link
                      href={link.href}
                      className="font-mono text-sm text-foreground/60 hover:text-foreground transition-colors duration-150"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t border-border/20">
          <p className="font-mono text-sm text-foreground/30">
            © 2026 Feltsense. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
