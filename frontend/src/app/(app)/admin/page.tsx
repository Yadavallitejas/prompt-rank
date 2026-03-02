"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

interface Stats {
    total_contests: number;
    total_problems: number;
    total_users: number;
    total_submissions: number;
}

export default function AdminOverviewPage() {
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get("/admin/stats")
            .then((r) => setStats(r.data))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, []);

    const cards = stats
        ? [
            { label: "Contests", value: stats.total_contests, color: "text-accent" },
            { label: "Problems", value: stats.total_problems, color: "text-warning" },
            { label: "Users", value: stats.total_users, color: "text-success" },
            { label: "Submissions", value: stats.total_submissions, color: "text-error" },
        ]
        : [];

    return (
        <div className="p-8 animate-fade-in">
            <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
            ) : (
                <div className="grid grid-cols-4 gap-4">
                    {cards.map((card) => (
                        <div
                            key={card.label}
                            className="card text-center py-6"
                        >
                            <p className={`text-3xl font-bold tabular-nums ${card.color}`}>
                                {card.value}
                            </p>
                            <p className="mt-1 text-sm text-text-secondary">
                                {card.label}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
