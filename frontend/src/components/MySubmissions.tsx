"use client";

import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";

/* ─── Types ─────────────────────────────────────────────────────────────── */

interface SubmissionItem {
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

interface MySubmissionsProps {
    problemId: string;
    contestId?: string;
    refreshTrigger?: string | null;
}

/* ─── Component ─────────────────────────────────────────────────────────── */

export default function MySubmissions({
    problemId,
    contestId,
    refreshTrigger,
}: MySubmissionsProps) {
    const [submissions, setSubmissions] = useState<SubmissionItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(true);
    const [selectedPrompt, setSelectedPrompt] = useState<SubmissionItem | null>(
        null
    );

    const load = useCallback(async () => {
        try {
            const params = contestId ? `?contest_id=${contestId}` : "";
            const { data } = await api.get(
                `/submissions/my/problem/${problemId}${params}`
            );
            setSubmissions(data);
        } catch {
            /* not logged in or error */
        } finally {
            setLoading(false);
        }
    }, [problemId, contestId]);

    useEffect(() => {
        load();
    }, [load]);

    // Re-fetch when a new submission is tracked
    useEffect(() => {
        if (!refreshTrigger) return;
        const interval = setInterval(load, 4000);
        return () => clearInterval(interval);
    }, [refreshTrigger, load]);

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
        <>
            <div className="rounded-md border border-border overflow-hidden">
                {/* Accordion Header */}
                <button
                    onClick={() => setExpanded((v) => !v)}
                    className="w-full flex items-center justify-between px-3 py-2.5 bg-surface/30 hover:bg-elevated/40 transition-colors text-left"
                >
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-text-muted uppercase tracking-wider">
                            My Submissions
                        </span>
                        {!loading && (
                            <span className="text-[10px] tabular-nums font-medium text-accent bg-accent/10 px-1.5 py-0.5 rounded-full">
                                {submissions.length}
                            </span>
                        )}
                    </div>
                    <svg
                        className={`w-3.5 h-3.5 text-text-muted transition-transform duration-200 ${expanded ? "rotate-180" : ""
                            }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M19 9l-7 7-7-7"
                        />
                    </svg>
                </button>

                {/* Accordion Body */}
                {expanded && (
                    <div className="border-t border-border">
                        {loading ? (
                            <div className="flex items-center justify-center py-6">
                                <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                            </div>
                        ) : submissions.length === 0 ? (
                            <div className="py-6 text-center">
                                <p className="text-xs text-text-muted">
                                    No submissions yet for this problem.
                                </p>
                            </div>
                        ) : (
                            <div className="max-h-52 overflow-y-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-border/50 text-left text-[10px] font-medium text-text-muted uppercase tracking-wider">
                                            <th className="px-3 py-1.5">
                                                Ver
                                            </th>
                                            <th className="px-3 py-1.5 text-center">
                                                Status
                                            </th>
                                            <th className="px-3 py-1.5 text-right">
                                                Score
                                            </th>
                                            <th className="px-3 py-1.5 text-center">
                                                Tests
                                            </th>
                                            <th className="px-3 py-1.5 text-right">
                                                Date
                                            </th>
                                            <th className="px-3 py-1.5 text-right">
                                                {" "}
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/30">
                                        {submissions.map((s) => (
                                            <tr
                                                key={s.id}
                                                className="transition-colors hover:bg-elevated/30 group"
                                            >
                                                <td className="px-3 py-2 text-xs text-text-secondary tabular-nums">
                                                    v{s.version}
                                                </td>
                                                <td className="px-3 py-2 text-center">
                                                    <span
                                                        className={`inline-flex items-center gap-1 text-[10px] font-medium ${statusColor(
                                                            s.status
                                                        )}`}
                                                    >
                                                        <span>
                                                            {statusIcon(
                                                                s.status
                                                            )}
                                                        </span>
                                                        {s.status}
                                                    </span>
                                                </td>
                                                <td className="px-3 py-2 text-right">
                                                    {s.final_score !== null ? (
                                                        <div className="flex flex-col items-end">
                                                            <span className="text-xs tabular-nums font-semibold text-accent">
                                                                {s.final_score.toFixed(1)}
                                                            </span>
                                                            <span className={`text-[8px] mt-0.5 uppercase font-bold tracking-wider ${s.final_score > 75 ? 'text-success' : s.final_score >= 50 ? 'text-warning' : 'text-error'}`}>
                                                                {s.final_score > 75 ? "Fully verified" : s.final_score >= 50 ? "Partially verified" : "Failed"}
                                                            </span>
                                                        </div>
                                                    ) : (
                                                        <span className="text-[10px] text-text-muted">
                                                            —
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-3 py-2 text-center">
                                                    {s.total_runs > 0 ? (
                                                        <span className="text-[10px] tabular-nums">
                                                            <span className="text-success font-medium">
                                                                {s.passed_runs}
                                                            </span>
                                                            <span className="text-text-muted">
                                                                /{s.total_runs}
                                                            </span>
                                                        </span>
                                                    ) : (
                                                        <span className="text-[10px] text-text-muted">
                                                            —
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-3 py-2 text-right">
                                                    <span className="text-[10px] text-text-muted">
                                                        {formatDate(
                                                            s.created_at
                                                        )}{" "}
                                                        {formatTime(
                                                            s.created_at
                                                        )}
                                                    </span>
                                                </td>
                                                <td className="px-3 py-2 text-right">
                                                    <button
                                                        onClick={() =>
                                                            setSelectedPrompt(s)
                                                        }
                                                        className="text-[10px] font-medium text-accent hover:text-accent/80 opacity-0 group-hover:opacity-100 transition-opacity px-2 py-0.5 rounded border border-accent/30 hover:bg-accent/10"
                                                    >
                                                        Open
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* ─── Prompt Viewer Modal ─────────────────────────────────────────── */}
            {selectedPrompt && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
                    onClick={() => setSelectedPrompt(null)}
                >
                    <div
                        className="card w-full max-w-2xl mx-4 animate-fade-in max-h-[80vh] flex flex-col"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between mb-3">
                            <div>
                                <h3 className="text-base font-semibold">
                                    Submission v{selectedPrompt.version}
                                </h3>
                                <p className="text-xs text-text-muted mt-0.5">
                                    {formatDate(selectedPrompt.created_at)}{" "}
                                    {formatTime(selectedPrompt.created_at)}
                                    {selectedPrompt.final_score !== null && (
                                        <>
                                            {" · Score: "}
                                            <span className="text-accent font-medium">
                                                {selectedPrompt.final_score.toFixed(
                                                    1
                                                )}
                                            </span>
                                        </>
                                    )}
                                </p>
                            </div>
                            <button
                                onClick={() => setSelectedPrompt(null)}
                                className="text-text-muted hover:text-foreground transition-colors p-1"
                            >
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
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        {/* Prompt Text */}
                        <div className="flex-1 overflow-y-auto rounded-md bg-background border border-border p-4">
                            <pre className="text-sm font-mono text-text-secondary whitespace-pre-wrap leading-relaxed">
                                {selectedPrompt.prompt_text}
                            </pre>
                        </div>

                        {/* Footer */}
                        <div className="mt-3 flex justify-end">
                            <button
                                onClick={() => setSelectedPrompt(null)}
                                className="btn-secondary text-sm px-4"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
