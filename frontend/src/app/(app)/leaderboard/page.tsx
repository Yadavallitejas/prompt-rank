"use client";

import { useState, useMemo } from "react";
import { useAuthStore } from "@/stores/authStore";
import {
    useLeaderboardStream,
    LeaderboardEntry,
} from "@/hooks/useLeaderboardStream";

type SortKey = "rank" | "username" | "rating" | "created_at";
type SortDir = "asc" | "desc";

export default function LeaderboardPage() {
    const { user } = useAuthStore();
    const { entries, isLive, isLoading } = useLeaderboardStream({
        streamPath: "/leaderboard/stream",
        restPath: "/leaderboard",
    });

    const [sortKey, setSortKey] = useState<SortKey>("rank");
    const [sortDir, setSortDir] = useState<SortDir>("asc");

    function toggleSort(key: SortKey) {
        if (sortKey === key) {
            setSortDir((d) => (d === "asc" ? "desc" : "asc"));
        } else {
            setSortKey(key);
            setSortDir(key === "rating" ? "desc" : "asc");
        }
    }

    const sorted = useMemo(() => {
        const copy = [...entries];
        copy.sort((a, b) => {
            let cmp = 0;
            switch (sortKey) {
                case "rank":
                    cmp = a.rank - b.rank;
                    break;
                case "username":
                    cmp = a.username.localeCompare(b.username);
                    break;
                case "rating":
                    cmp = a.rating - b.rating;
                    break;
                case "created_at":
                    cmp =
                        new Date(a.created_at || "").getTime() -
                        new Date(b.created_at || "").getTime();
                    break;
            }
            return sortDir === "asc" ? cmp : -cmp;
        });
        return copy;
    }, [entries, sortKey, sortDir]);

    const top3 = entries.slice(0, 3);

    const ratingColor = (rating: number) => {
        if (rating >= 2000) return "text-error";
        if (rating >= 1600) return "text-warning";
        if (rating >= 1400) return "text-accent";
        if (rating >= 1200) return "text-success";
        return "text-text-secondary";
    };

    const SortArrow = ({ col }: { col: SortKey }) => {
        if (sortKey !== col) return null;
        return (
            <span className="ml-1 text-accent">
                {sortDir === "asc" ? "↑" : "↓"}
            </span>
        );
    };

    const podiumColors = [
        "from-yellow-500/20 to-yellow-600/5 border-yellow-500/30",
        "from-gray-400/20 to-gray-500/5 border-gray-400/30",
        "from-orange-600/20 to-orange-700/5 border-orange-600/30",
    ];
    const podiumLabels = ["🥇", "🥈", "🥉"];

    return (
        <div className="mx-auto max-w-4xl px-6 py-8 animate-fade-in">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">Global Leaderboard</h1>
                    <p className="mt-1 text-sm text-text-secondary">
                        All players ranked by ELO rating. Compete in contests to climb the
                        ranks.
                    </p>
                </div>
                {/* Live Badge */}
                <div
                    className={`flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium border ${isLive
                            ? "bg-success/10 border-success/30 text-success"
                            : "bg-text-muted/10 border-text-muted/30 text-text-muted"
                        }`}
                >
                    {isLive && (
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
                        </span>
                    )}
                    {isLive ? "LIVE" : "Polling"}
                </div>
            </div>

            {/* Rating Legend */}
            <div className="card mb-6">
                <div className="flex flex-wrap items-center gap-4 text-xs">
                    <span className="text-text-muted font-medium">Tiers:</span>
                    <span className="text-text-secondary">Beginner &lt;1200</span>
                    <span className="text-success">Intermediate 1200+</span>
                    <span className="text-accent">Advanced 1400+</span>
                    <span className="text-warning">Expert 1600+</span>
                    <span className="text-error">Grandmaster 2000+</span>
                </div>
            </div>

            {isLoading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
            ) : entries.length === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-text-secondary">
                        No players yet. Be the first to register!
                    </p>
                </div>
            ) : (
                <>
                    {/* Top 3 Podium */}
                    {top3.length >= 3 && (
                        <div className="grid grid-cols-3 gap-3 mb-6">
                            {[1, 0, 2].map((idx) => {
                                const e = top3[idx];
                                return (
                                    <div
                                        key={e.user_id}
                                        className={`relative rounded-lg border bg-gradient-to-b p-4 text-center transition-all ${podiumColors[idx]} ${idx === 0 ? "scale-105 -mt-1" : ""
                                            }`}
                                    >
                                        <div className="text-2xl mb-1">{podiumLabels[idx]}</div>
                                        <p className="text-sm font-bold truncate">
                                            {e.username}
                                            {e.user_id === user?.id && (
                                                <span className="text-accent text-xs ml-1">(you)</span>
                                            )}
                                        </p>
                                        <p
                                            className={`text-lg font-bold tabular-nums ${ratingColor(
                                                e.rating
                                            )}`}
                                        >
                                            {e.rating}
                                        </p>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Sortable Table */}
                    <div className="card overflow-hidden p-0">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-border text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                                    <th
                                        className="px-4 py-3 cursor-pointer select-none hover:text-foreground transition-colors"
                                        onClick={() => toggleSort("rank")}
                                    >
                                        #<SortArrow col="rank" />
                                    </th>
                                    <th
                                        className="px-4 py-3 cursor-pointer select-none hover:text-foreground transition-colors"
                                        onClick={() => toggleSort("username")}
                                    >
                                        Player
                                        <SortArrow col="username" />
                                    </th>
                                    <th
                                        className="px-4 py-3 text-right cursor-pointer select-none hover:text-foreground transition-colors"
                                        onClick={() => toggleSort("rating")}
                                    >
                                        Rating
                                        <SortArrow col="rating" />
                                    </th>
                                    <th
                                        className="px-4 py-3 text-right cursor-pointer select-none hover:text-foreground transition-colors"
                                        onClick={() => toggleSort("created_at")}
                                    >
                                        Joined
                                        <SortArrow col="created_at" />
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border/50">
                                {sorted.map((entry) => (
                                    <tr
                                        key={entry.user_id}
                                        className={`transition-all duration-500 hover:bg-elevated/50 ${entry.user_id === user?.id
                                                ? "bg-accent/5 border-l-2 border-l-accent"
                                                : ""
                                            }`}
                                        style={{
                                            viewTransitionName: `lb-row-${entry.user_id}`,
                                        }}
                                    >
                                        <td
                                            className={`px-4 py-3 font-bold tabular-nums ${entry.rank === 1
                                                    ? "text-gold text-lg"
                                                    : entry.rank === 2
                                                        ? "text-silver"
                                                        : entry.rank === 3
                                                            ? "text-bronze"
                                                            : "text-text-secondary"
                                                }`}
                                        >
                                            {entry.rank === 1
                                                ? "1st"
                                                : entry.rank === 2
                                                    ? "2nd"
                                                    : entry.rank === 3
                                                        ? "3rd"
                                                        : entry.rank}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className="text-sm font-medium">
                                                {entry.username}
                                            </span>
                                            {entry.user_id === user?.id && (
                                                <span className="ml-2 text-xs text-accent">(you)</span>
                                            )}
                                        </td>
                                        <td
                                            className={`px-4 py-3 text-right text-sm font-bold tabular-nums ${ratingColor(
                                                entry.rating
                                            )}`}
                                        >
                                            {entry.rating}
                                        </td>
                                        <td className="px-4 py-3 text-right text-xs text-text-muted">
                                            {entry.created_at
                                                ? new Date(entry.created_at).toLocaleDateString(
                                                    "en-US",
                                                    {
                                                        month: "short",
                                                        day: "numeric",
                                                        year: "numeric",
                                                    }
                                                )
                                                : "-"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
}
