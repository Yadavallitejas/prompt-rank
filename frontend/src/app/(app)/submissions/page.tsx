"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

/* ─── Types ─────────────────────────────────────────────────────────────── */

interface SubmissionHistory {
    id: string;
    problem_id: string;
    contest_id: string | null;
    prompt_text: string;
    version: number;
    status: string;
    final_score: number | null;
    created_at: string;
    problem_title: string;
    contest_name: string | null;
    is_practice: boolean;
    total_runs: number;
    passed_runs: number;
}

type FilterType = "all" | "contest" | "practice";
type StatusFilter = "all" | "evaluated" | "queued" | "running" | "failed";

/* ─── Page ──────────────────────────────────────────────────────────────── */

export default function SubmissionsPage() {
    const [submissions, setSubmissions] = useState<SubmissionHistory[]>([]);
    const [loading, setLoading] = useState(true);
    const [typeFilter, setTypeFilter] = useState<FilterType>("all");
    const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

    useEffect(() => {
        async function load() {
            try {
                const { data } = await api.get("/submissions/my");
                setSubmissions(data);
            } catch {
                /* not logged in or error */
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    /* ─── Filtering ────────────────────────────────────────────────────── */

    const filtered = submissions.filter((s) => {
        if (typeFilter === "contest" && !s.contest_id) return false;
        if (typeFilter === "practice" && s.contest_id) return false;
        if (statusFilter !== "all" && s.status !== statusFilter) return false;
        return true;
    });

    /* ─── Helpers ──────────────────────────────────────────────────────── */

    const statusColor = (s: string) => {
        if (s === "evaluated") return "text-success";
        if (s === "running" || s === "queued") return "text-warning";
        if (s === "failed") return "text-error";
        return "text-text-muted";
    };

    const statusIcon = (s: string) => {
        if (s === "evaluated") return "✓";
        if (s === "running") return "⟳";
        if (s === "queued") return "◷";
        if (s === "failed") return "✗";
        return "?";
    };

    const formatDate = (iso: string) => {
        const d = new Date(iso);
        return d.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    };

    const formatTime = (iso: string) => {
        const d = new Date(iso);
        return d.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    /* ─── Render ───────────────────────────────────────────────────────── */

    return (
        <div className="mx-auto max-w-5xl px-6 py-8 animate-fade-in">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">My Submissions</h1>
                    <p className="mt-1 text-sm text-text-secondary">
                        Track all your past prompts across contests and practice
                    </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-text-muted">
                    <span className="tabular-nums font-medium text-foreground">
                        {submissions.length}
                    </span>{" "}
                    total submissions
                </div>
            </div>

            {/* Filters */}
            <div className="mb-5 flex flex-wrap items-center gap-3">
                {/* Type filter */}
                <div className="flex rounded-md border border-border overflow-hidden">
                    {(
                        [
                            ["all", "All"],
                            ["contest", "Contest"],
                            ["practice", "Practice"],
                        ] as [FilterType, string][]
                    ).map(([key, label]) => (
                        <button
                            key={key}
                            onClick={() => setTypeFilter(key)}
                            className={`px-3 py-1.5 text-xs font-medium transition-colors ${typeFilter === key
                                    ? "bg-accent/15 text-accent"
                                    : "text-text-secondary hover:bg-elevated hover:text-foreground"
                                }`}
                        >
                            {label}
                        </button>
                    ))}
                </div>

                {/* Status filter */}
                <div className="flex rounded-md border border-border overflow-hidden">
                    {(
                        [
                            ["all", "Any Status"],
                            ["evaluated", "Evaluated"],
                            ["queued", "Queued"],
                            ["running", "Running"],
                            ["failed", "Failed"],
                        ] as [StatusFilter, string][]
                    ).map(([key, label]) => (
                        <button
                            key={key}
                            onClick={() => setStatusFilter(key)}
                            className={`px-3 py-1.5 text-xs font-medium transition-colors ${statusFilter === key
                                    ? "bg-accent/15 text-accent"
                                    : "text-text-secondary hover:bg-elevated hover:text-foreground"
                                }`}
                        >
                            {label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Table / Content */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
            ) : filtered.length === 0 ? (
                <div className="card text-center py-16">
                    <p className="text-3xl mb-3">📝</p>
                    <p className="text-text-secondary font-medium">
                        {submissions.length === 0
                            ? "No submissions yet"
                            : "No submissions match your filters"}
                    </p>
                    <p className="text-sm text-text-muted mt-1 mb-5">
                        {submissions.length === 0
                            ? "Start by joining a contest or trying a practice problem!"
                            : "Try adjusting your filters above."}
                    </p>
                    {submissions.length === 0 && (
                        <div className="flex justify-center gap-3">
                            <Link href="/contests" className="btn-primary text-sm">
                                Browse Contests
                            </Link>
                            <Link href="/practice" className="btn-secondary text-sm">
                                Practice Problems
                            </Link>
                        </div>
                    )}
                </div>
            ) : (
                <div className="card overflow-hidden p-0">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-border text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                                <th className="px-4 py-3">Problem</th>
                                <th className="px-4 py-3">Type</th>
                                <th className="px-4 py-3 text-center">Version</th>
                                <th className="px-4 py-3 text-center">Status</th>
                                <th className="px-4 py-3 text-right">Score</th>
                                <th className="px-4 py-3 text-center">Tests</th>
                                <th className="px-4 py-3 text-right">Date</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border/50">
                            {filtered.map((s) => (
                                <tr
                                    key={s.id}
                                    className="transition-colors hover:bg-elevated/50 group"
                                >
                                    {/* Problem */}
                                    <td className="px-4 py-3">
                                        <Link
                                            href={
                                                s.contest_id
                                                    ? `/contests/${s.contest_id}`
                                                    : `/practice/${s.problem_id}`
                                            }
                                            className="text-sm font-medium hover:text-accent transition-colors"
                                        >
                                            {s.problem_title}
                                        </Link>
                                    </td>

                                    {/* Type Badge */}
                                    <td className="px-4 py-3">
                                        {s.contest_id ? (
                                            <span className="inline-flex text-[10px] font-medium px-2 py-0.5 rounded-full border bg-accent/10 text-accent border-accent/30">
                                                {s.contest_name || "Contest"}
                                            </span>
                                        ) : (
                                            <span className="inline-flex text-[10px] font-medium px-2 py-0.5 rounded-full border bg-warning/10 text-warning border-warning/30">
                                                Practice
                                            </span>
                                        )}
                                    </td>

                                    {/* Version */}
                                    <td className="px-4 py-3 text-center text-xs text-text-secondary tabular-nums">
                                        v{s.version}
                                    </td>

                                    {/* Status */}
                                    <td className="px-4 py-3 text-center">
                                        <span
                                            className={`inline-flex items-center gap-1 text-xs font-medium ${statusColor(s.status)}`}
                                        >
                                            <span className="text-[10px]">
                                                {statusIcon(s.status)}
                                            </span>
                                            {s.status}
                                        </span>
                                    </td>

                                    {/* Score */}
                                    <td className="px-4 py-3 text-right">
                                        {s.final_score !== null ? (
                                            <div className="flex flex-col items-end">
                                                <span className="text-sm tabular-nums font-semibold text-accent">
                                                    {s.final_score.toFixed(1)}
                                                </span>
                                                <span className={`text-[8px] mt-0.5 uppercase font-bold tracking-wider ${s.final_score > 75 ? 'text-success' : s.final_score >= 50 ? 'text-warning' : 'text-error'}`}>
                                                    {s.final_score > 75 ? "Fully verified" : s.final_score >= 50 ? "Partially verified" : "Failed"}
                                                </span>
                                            </div>
                                        ) : (
                                            <span className="text-xs text-text-muted">
                                                —
                                            </span>
                                        )}
                                    </td>

                                    {/* Test Cases */}
                                    <td className="px-4 py-3 text-center">
                                        {s.total_runs > 0 ? (
                                            <span className="text-xs tabular-nums">
                                                <span className="text-success font-medium">
                                                    {s.passed_runs}
                                                </span>
                                                <span className="text-text-muted">
                                                    /{s.total_runs}
                                                </span>
                                            </span>
                                        ) : (
                                            <span className="text-xs text-text-muted">
                                                —
                                            </span>
                                        )}
                                    </td>

                                    {/* Date */}
                                    <td className="px-4 py-3 text-right">
                                        <p className="text-xs text-text-secondary">
                                            {formatDate(s.created_at)}
                                        </p>
                                        <p className="text-[10px] text-text-muted">
                                            {formatTime(s.created_at)}
                                        </p>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
