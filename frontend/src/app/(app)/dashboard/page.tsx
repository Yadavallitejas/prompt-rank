"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuthStore } from "@/stores/authStore";
import api from "@/lib/api";

interface Contest {
    id: string;
    name: string;
    status: string;
    start_time: string;
    end_time: string;
}

interface Submission {
    id: string;
    problem_id: string;
    problem_title: string;
    contest_id: string | null;
    contest_name: string | null;
    version: number;
    status: string;
    final_score: number | null;
    created_at: string;
}

interface PracticeProblem {
    id: string;
    title: string;
    difficulty: string;
    statement: string;
    time_limit_sec: number;
}

export default function DashboardPage() {
    const { user } = useAuthStore();
    const [contests, setContests] = useState<Contest[]>([]);
    const [submissions, setSubmissions] = useState<Submission[]>([]);
    const [showAllSubs, setShowAllSubs] = useState(false);
    const [practiceProblems, setPracticeProblems] = useState<PracticeProblem[]>([]);
    const [loading, setLoading] = useState(true);

    const solvedProblems = useMemo<{ id: string, title: string }[]>(() => {
        const solved = submissions.filter(s => s.final_score !== null && s.final_score > 75 && !s.contest_id);
        const unique = new Map();
        for (const s of solved) {
            if (!unique.has(s.problem_id)) {
                unique.set(s.problem_id, { id: s.problem_id, title: s.problem_title });
            }
        }
        return Array.from(unique.values());
    }, [submissions]);

    const participatedContests = useMemo<{ id: string, name: string }[]>(() => {
        const participated = submissions.filter(s => s.contest_id);
        const unique = new Map();
        for (const s of participated) {
            if (!unique.has(s.contest_id)) {
                unique.set(s.contest_id, { id: s.contest_id, name: s.contest_name || "Contest" });
            }
        }
        return Array.from(unique.values());
    }, [submissions]);

    useEffect(() => {
        async function load() {
            try {
                const [contestsRes, subsRes, practiceRes] = await Promise.allSettled([
                    api.get("/contests"),
                    api.get("/submissions/my"),
                    api.get("/problems"),
                ]);
                if (contestsRes.status === "fulfilled")
                    setContests(contestsRes.value.data.slice(0, 5));
                if (subsRes.status === "fulfilled")
                    setSubmissions(subsRes.value.data);
                if (practiceRes.status === "fulfilled")
                    setPracticeProblems(practiceRes.value.data);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    const statusColor = (s: string) => {
        if (s === "active") return "text-success";
        if (s === "evaluated") return "text-success";
        if (s === "running" || s === "queued") return "text-warning";
        if (s === "failed") return "text-error";
        return "text-text-muted";
    };

    const diffBadge = (d: string) => {
        const styles: Record<string, string> = {
            easy: "bg-success/15 text-success border-success/30",
            medium: "bg-warning/15 text-warning border-warning/30",
            hard: "bg-error/15 text-error border-error/30",
        };
        return styles[d] || styles.medium;
    };

    return (
        <div className="mx-auto max-w-5xl px-6 py-8 animate-fade-in">
            {/* Welcome */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold">
                    Welcome back,{" "}
                    <span className="text-accent">{user?.username || "Engineer"}</span>
                </h1>
                <p className="mt-1 text-sm text-text-secondary">
                    Your current ELO rating:{" "}
                    <span className="tabular-nums font-semibold text-foreground">
                        {user?.rating ?? 1200}
                    </span>
                </p>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
                {/* Recent Contests */}
                <section className="card">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold">Recent Contests</h2>
                        <Link
                            href="/contests"
                            className="text-xs text-accent hover:underline"
                        >
                            View all
                        </Link>
                    </div>
                    {loading ? (
                        <p className="text-sm text-text-muted">Loading...</p>
                    ) : contests.length === 0 ? (
                        <p className="text-sm text-text-muted">No contests yet.</p>
                    ) : (
                        <div className="space-y-2">
                            {contests.map((c) => (
                                <Link
                                    key={c.id}
                                    href={`/contests/${c.id}`}
                                    className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-elevated transition-colors"
                                >
                                    <span className="text-sm font-medium">{c.name}</span>
                                    <span className={`text-xs font-medium ${statusColor(c.status)}`}>
                                        {c.status}
                                    </span>
                                </Link>
                            ))}
                        </div>
                    )}
                </section>

                {/* Recent Submissions */}
                <section className="card">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold">My Submissions</h2>
                        <Link
                            href="/submissions"
                            className="text-xs text-accent hover:underline"
                        >
                            View all
                        </Link>
                    </div>
                    {loading ? (
                        <p className="text-sm text-text-muted">Loading...</p>
                    ) : submissions.length === 0 ? (
                        <p className="text-sm text-text-muted">
                            No submissions yet. Join a contest to start competing!
                        </p>
                    ) : (
                        <div className="space-y-2">
                            {(showAllSubs ? submissions : submissions.slice(0, 5)).map((s) => (
                                <div
                                    key={s.id}
                                    className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-elevated transition-colors"
                                >
                                    <div>
                                        <p className="text-sm font-medium truncate max-w-[200px]">
                                            {s.problem_title} <span className="text-xs text-text-muted font-normal">(v{s.version})</span>
                                        </p>
                                        <p className="text-xs text-text-muted">
                                            {new Date(s.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <p className={`text-xs font-medium ${statusColor(s.status)}`}>
                                            {s.status}
                                        </p>
                                        {s.final_score !== null && (
                                            <div className="flex flex-col items-end">
                                                <p className="text-sm tabular-nums font-semibold text-accent">
                                                    {s.final_score.toFixed(1)}
                                                </p>
                                                <p className={`text-[10px] uppercase font-bold tracking-wider ${s.final_score > 75 ? 'text-success' : s.final_score >= 50 ? 'text-warning' : 'text-error'}`}>
                                                    {s.final_score > 75 ? "Fully verified" : s.final_score >= 50 ? "Partially verified" : "Failed"}
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {submissions.length > 5 && !showAllSubs && (
                                <button
                                    onClick={() => setShowAllSubs(true)}
                                    className="w-full text-center text-xs text-accent hover:underline py-2"
                                >
                                    View more
                                </button>
                            )}
                            {showAllSubs && submissions.length > 5 && (
                                <button
                                    onClick={() => setShowAllSubs(false)}
                                    className="w-full text-center text-xs text-accent hover:underline py-2"
                                >
                                    View less
                                </button>
                            )}
                        </div>
                    )}
                </section>
            </div>

            {/* Practice Problems */}
            <section className="mt-8">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold">Practice Problems</h2>
                    <Link
                        href="/practice"
                        className="text-xs text-accent hover:underline"
                    >
                        View all
                    </Link>
                </div>
                {loading ? (
                    <p className="text-sm text-text-muted">Loading...</p>
                ) : practiceProblems.length === 0 ? (
                    <p className="text-sm text-text-muted">
                        No practice problems available yet.
                    </p>
                ) : (
                    <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin">
                        {practiceProblems.map((p) => (
                            <Link
                                key={p.id}
                                href={`/practice/${p.id}`}
                                className="card flex-shrink-0 w-64 block transition-all hover:border-accent/30 hover:shadow-lg hover:shadow-accent/5"
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <h3 className="text-sm font-semibold truncate flex-1 mr-2">
                                        {p.title}
                                    </h3>
                                    <span
                                        className={`inline-flex shrink-0 text-[10px] font-medium px-2 py-0.5 rounded-full border capitalize ${diffBadge(
                                            p.difficulty
                                        )}`}
                                    >
                                        {p.difficulty}
                                    </span>
                                </div>
                                <p className="text-xs text-text-muted line-clamp-2">
                                    {p.statement.slice(0, 100)}
                                    {p.statement.length > 100 ? "…" : ""}
                                </p>
                                <p className="mt-2 text-[10px] text-text-muted">
                                    Time limit: {p.time_limit_sec}s
                                </p>
                            </Link>
                        ))}
                    </div>
                )}
            </section>

            {/* User History */}
            <div className="grid gap-6 lg:grid-cols-2 mt-8">
                {/* Solved Problems */}
                <section className="card flex flex-col">
                    <h2 className="text-lg font-semibold mb-4">Solved Problems</h2>
                    {loading ? (
                        <p className="text-sm text-text-muted">Loading...</p>
                    ) : solvedProblems.length === 0 ? (
                        <div className="flex-1 flex items-center justify-center py-6 text-center">
                            <p className="text-sm text-text-muted">No solved problems yet. Practice more to show up here!</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {solvedProblems.map(p => (
                                <Link
                                    key={p.id}
                                    href={`/practice/${p.id}`}
                                    className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-elevated transition-colors border border-transparent hover:border-success/30"
                                >
                                    <span className="text-sm font-medium">{p.title}</span>
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-success">
                                        Fully verified
                                    </span>
                                </Link>
                            ))}
                        </div>
                    )}
                </section>

                {/* Participated Contests */}
                <section className="card flex flex-col">
                    <h2 className="text-lg font-semibold mb-4">Participated Contests</h2>
                    {loading ? (
                        <p className="text-sm text-text-muted">Loading...</p>
                    ) : participatedContests.length === 0 ? (
                        <div className="flex-1 flex items-center justify-center py-6 text-center">
                            <p className="text-sm text-text-muted">No contests participated yet. Join one now!</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {participatedContests.map(c => (
                                <Link
                                    key={c.id}
                                    href={`/contests/${c.id}`}
                                    className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-elevated transition-colors border border-transparent hover:border-accent/30"
                                >
                                    <span className="text-sm font-medium">{c.name}</span>
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-accent">
                                        View
                                    </span>
                                </Link>
                            ))}
                        </div>
                    )}
                </section>
            </div>

            {/* Quick Actions */}
            <div className="mt-8 flex gap-4">
                <Link href="/contests" className="btn-primary">
                    Browse Contests
                </Link>
                <Link href="/practice" className="btn-secondary">
                    Practice Problems
                </Link>
                <Link href="/leaderboard" className="btn-secondary">
                    View Leaderboard
                </Link>
            </div>
        </div>
    );
}
