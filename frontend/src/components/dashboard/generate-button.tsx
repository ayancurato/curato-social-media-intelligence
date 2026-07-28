/**
 * Curato AI — Generate Button Component
 *
 * The primary CTA for triggering content generation.
 */

"use client";

import { cn } from "@/lib/utils";

interface GenerateButtonProps {
  onClick: () => void;
  isLoading: boolean;
  disabled: boolean;
}

export function GenerateButton({
  onClick,
  isLoading,
  disabled,
}: GenerateButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || isLoading}
      className={cn(
        "relative group w-full max-w-md mx-auto",
        "px-8 py-4 rounded-2xl font-semibold text-lg",
        "transition-all duration-300 ease-out",
        "focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:ring-offset-2 focus:ring-offset-zinc-900",
        disabled || isLoading
          ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
          : "bg-gradient-to-r from-blue-600 via-violet-600 to-blue-600 bg-[length:200%_100%] text-white shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-[1.02] active:scale-[0.98] animate-gradient"
      )}
      id="generate-content-btn"
    >
      {/* Glow effect */}
      {!disabled && !isLoading && (
        <span className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-600/20 via-violet-600/20 to-blue-600/20 blur-xl group-hover:blur-2xl transition-all duration-300 -z-10" />
      )}

      <span className="flex items-center justify-center gap-3">
        {isLoading ? (
          <>
            <svg
              className="animate-spin h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Generating…
          </>
        ) : (
          <>
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            Generate Today&apos;s Content
          </>
        )}
      </span>
    </button>
  );
}
