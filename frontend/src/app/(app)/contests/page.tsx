"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

interface Contest {
    id: string;
    name: string;
    status: string;
    start_time: string;
    end_time: string;
    submission_limit: number;
    allowed_model: string;
}

export default function ContestsPage() {
    const [contests, setContests] = useState<Contest[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api
            .get("/contests")
            .then((r) => setContests(r.data))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, []);

    const statusBadge = (s: string) => {
        const styles: Record<string, string> = {
            active: "bg-success/15 text-success border-success/30",
            scheduled: "bg-warning/15 text-warning border-warning/30",
            ended: "bg-text-muted/15 text-text-muted border-text-muted/30",
        };
        return styles[s] || styles.ended;
    };

    const formatDate = (iso: string) =>
        new Date(iso).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });

    return (
        <div className="mx-auto max-w-4xl px-6 py-8 animate-fade-in">
            <div className="mb-8">
                <h1 className="text-2xl font-bold">Contests</h1>
                <p className="mt-1 text-sm text-text-secondary">
                    Join active contests or browse past competitions.
                </p>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
            ) : contests.length === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-text-secondary">No contests available yet.</p>
                    <p className="mt-1 text-sm text-text-muted">
                        Check back soon for upcoming competitions.
                    </p>
                </div>
            ) : (
                <div className="space-y-3">
                    {contests.map((c) => (
                        <Link
                            key={c.id}
                            href={`/contests/${c.id}`}
                            className="card block transition-all hover:border-accent/30 hover:shadow-lg hover:shadow-accent/5"
                        >
                            <div className="flex items-start justify-between">
                                <div>
                                    <h3 className="text-base font-semibold">{c.name}</h3>
                                    <div className="mt-2 flex items-center gap-4 text-xs text-text-muted">
                                        <span>
                                            Start: {formatDate(c.start_time)}
                                        </span>
                                        <span>
                                            End: {formatDate(c.end_time)}
                                        </span>
                                        <span>Limit: {c.submission_limit} submissions</span>
                                        <span className="tabular-nums">{c.allowed_model}</span>
                                    </div>
                                </div>
                                <span
                                    className={`inline-flex text-xs font-medium px-2.5 py-0.5 rounded-full border ${statusBadge(
                                        c.status
                                    )}`}
                                >
                                    {c.status}
                                </span>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
