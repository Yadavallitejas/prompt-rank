"use client";

import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* ── Header ──────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-8 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <svg
            width="28"
            height="28"
            viewBox="0 0 28 28"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="text-accent"
          >
            <path
              d="M4 20L14 4L24 20H4Z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinejoin="round"
            />
            <path
              d="M14 14V18"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
          <span className="text-lg font-semibold tracking-tight">
            Prompt<span className="text-accent">Rank</span>
          </span>
        </div>
        <nav className="flex items-center gap-4">
          <Link href="/login" className="btn-secondary text-sm">
            Log In
          </Link>
          <Link href="/register" className="btn-primary text-sm">
            Sign Up
          </Link>
        </nav>
      </header>

      {/* ── Hero ────────────────────────────────────────────── */}
      <main className="flex flex-1 flex-col items-center justify-center px-8 text-center animate-fade-in">
        <div className="max-w-2xl">
          <div className="mb-6 inline-flex items-center rounded-full border border-border px-4 py-1.5 text-xs font-medium text-text-secondary">
            <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
            Competitive Prompt Engineering Platform
          </div>

          <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight">
            Prove your{" "}
            <span className="text-accent">LLM-control</span>{" "}
            skill.
          </h1>

          <p className="mx-auto mb-10 max-w-lg text-lg leading-relaxed text-text-secondary">
            Write system prompts. Compete in timed contests with hidden
            testcases. Earn ELO-style ratings based on accuracy, consistency,
            and efficiency — not vibes.
          </p>

          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link href="/register" className="btn-primary px-8 py-3 text-base">
              Start Competing
            </Link>
            <Link
              href="/contests"
              className="btn-secondary px-8 py-3 text-base"
            >
              Browse Contests
            </Link>
          </div>
        </div>

        {/* ── Stats ───────────────────────────────────────── */}
        <div className="mt-20 grid w-full max-w-3xl grid-cols-3 gap-6 animate-slide-up">
          {[
            { label: "Metric Dimensions", value: "6" },
            { label: "Runs per Testcase", value: "N=5" },
            { label: "Rating System", value: "ELO" },
          ].map((stat) => (
            <div key={stat.label} className="card text-center">
              <p className="mb-1 text-2xl font-bold tabular-nums text-accent">
                {stat.value}
              </p>
              <p className="text-sm text-text-secondary">{stat.label}</p>
            </div>
          ))}
        </div>
      </main>

      {/* ── Scoring breakdown ──────────────────────────────── */}
      <section className="px-8 pb-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="mb-8 text-center text-2xl font-semibold">
            Multi-Metric Scoring
          </h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {[
              { name: "Accuracy", weight: "40%", icon: "◎" },
              { name: "Consistency", weight: "20%", icon: "≡" },
              { name: "Format", weight: "15%", icon: "{ }" },
              { name: "Efficiency", weight: "10%", icon: "⚡" },
              { name: "Robustness", weight: "10%", icon: "🛡" },
              { name: "Latency", weight: "5%", icon: "⏱" },
            ].map((metric) => (
              <div
                key={metric.name}
                className="card flex items-center gap-3 transition-colors hover:border-accent/40"
              >
                <span className="text-xl">{metric.icon}</span>
                <div>
                  <p className="text-sm font-medium">{metric.name}</p>
                  <p className="text-xs tabular-nums text-text-muted">
                    {metric.weight}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────── */}
      <footer className="border-t border-border px-8 py-6 text-center text-sm text-text-muted">
        PromptRank © {new Date().getFullYear()} — Engineering competition, not
        movie cosplay.
      </footer>
    </div>
  );
}
