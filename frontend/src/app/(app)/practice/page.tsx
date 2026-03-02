"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

interface PracticeProblem {
    id: string;
    title: string;
    difficulty: string;
    statement: string;
    time_limit_sec: number;
    created_at: string;
}

const DIFFICULTIES = ["all", "easy", "medium", "hard"] as const;

export default function PracticePage() {
    const [problems, setProblems] = useState<PracticeProblem[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>("all");

    useEffect(() => {
        const params = filter !== "all" ? `?difficulty=${filter}` : "";
        setLoading(true);
        api
            .get(`/problems${params}`)
            .then((r) => setProblems(r.data))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [filter]);

    const diffBadge = (d: string) => {
        const styles: Record<string, string> = {
            easy: "bg-success/15 text-success border-success/30",
            medium: "bg-warning/15 text-warning border-warning/30",
            hard: "bg-error/15 text-error border-error/30",
        };
        return styles[d] || styles.medium;
    };

    return (
        <div className="mx-auto max-w-4xl px-6 py-8 animate-fade-in">
            {/* ── Header ────────────────────────────────────── */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold">Practice Problems</h1>
                <p className="mt-1 text-sm text-text-secondary">
                    Sharpen your prompt engineering skills. No contest timer, no
                    pressure.
                </p>
            </div>

            {/* ── Difficulty Filter ──────────────────────────── */}
            <div className="mb-6 flex items-center gap-2">
                {DIFFICULTIES.map((d) => (
                    <button
                        key={d}
                        onClick={() => setFilter(d)}
                        className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-colors capitalize ${filter === d
                                ? "bg-accent/15 text-accent border-accent/40"
                                : "text-text-muted border-border hover:border-text-secondary"
                            }`}
                    >
                        {d}
                    </button>
                ))}
            </div>

            {/* ── Problems List ──────────────────────────────── */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
            ) : problems.length === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-text-secondary">
                        No practice problems available yet.
                    </p>
                    <p className="mt-1 text-sm text-text-muted">
                        Check back soon for new challenges.
                    </p>
                </div>
            ) : (
                <div className="space-y-3">
                    {problems.map((p) => (
                        <Link
                            key={p.id}
                            href={`/practice/${p.id}`}
                            className="card block transition-all hover:border-accent/30 hover:shadow-lg hover:shadow-accent/5"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1 min-w-0">
                                    <h3 className="text-base font-semibold">
                                        {p.title}
                                    </h3>
                                    <p className="mt-1 text-sm text-text-muted line-clamp-2">
                                        {p.statement.slice(0, 160)}
                                        {p.statement.length > 160 ? "…" : ""}
                                    </p>
                                    <div className="mt-3 flex items-center gap-4 text-xs text-text-muted">
                                        <span>
                                            Time limit: {p.time_limit_sec}s
                                        </span>
                                    </div>
                                </div>
                                <span
                                    className={`ml-4 inline-flex shrink-0 text-xs font-medium px-2.5 py-0.5 rounded-full border capitalize ${diffBadge(
                                        p.difficulty
                                    )}`}
                                >
                                    {p.difficulty}
                                </span>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
