import { cn } from "@/lib/utils";

export const Logo = ({ className }: { className?: string }) => {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* Geometric icon */}
      <svg
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-5 h-5 md:w-6 md:h-6"
      >
        <path
          d="M8.5 14.5V22H4V17.5H0V14.5H4V14.499L8.5 14.5ZM14.5 8.5H14.501V13H14.5V17H10V13H6V8.5H10V8.499L14.5 8.5ZM20.5 2.5V10H16V6H12V2.5H20.5Z"
          fill="currentColor"
        />
      </svg>
      {/* Wordmark */}
      <span className="font-mono text-foreground text-base md:text-lg tracking-tight">
        GutCheck
      </span>
    </div>
  );
};
