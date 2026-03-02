"use client";

import { useEffect, useState } from "react";
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
    status: string;
    final_score: number | null;
    created_at: string;
}

export default function DashboardPage() {
    const { user } = useAuthStore();
    const [contests, setContests] = useState<Contest[]>([]);
    const [submissions, setSubmissions] = useState<Submission[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            try {
                const [contestsRes, subsRes] = await Promise.allSettled([
                    api.get("/contests"),
                    api.get("/submissions/my"),
                ]);
                if (contestsRes.status === "fulfilled")
                    setContests(contestsRes.value.data.slice(0, 5));
                if (subsRes.status === "fulfilled")
                    setSubmissions(subsRes.value.data.slice(0, 10));
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
                    </div>
                    {loading ? (
                        <p className="text-sm text-text-muted">Loading...</p>
                    ) : submissions.length === 0 ? (
                        <p className="text-sm text-text-muted">
                            No submissions yet. Join a contest to start competing!
                        </p>
                    ) : (
                        <div className="space-y-2">
                            {submissions.map((s) => (
                                <div
                                    key={s.id}
                                    className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-elevated transition-colors"
                                >
                                    <div>
                                        <p className="text-sm font-medium truncate max-w-[200px]">
                                            {s.id.slice(0, 8)}...
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
                                            <p className="text-sm tabular-nums font-semibold text-accent">
                                                {s.final_score.toFixed(1)}
                                            </p>
                                        )}
                                    </div>
                                </div>
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
                <Link href="/leaderboard" className="btn-secondary">
                    View Leaderboard
                </Link>
            </div>
        </div>
    );
}
