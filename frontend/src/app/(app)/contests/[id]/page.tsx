"use client";

import { useEffect, useState, FormEvent } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import { useAuthStore } from "@/stores/authStore";
import api from "@/lib/api";
import CountdownTimer from "@/components/CountdownTimer";
import SubmissionTracker from "@/components/SubmissionTracker";
import { useLeaderboardStream } from "@/hooks/useLeaderboardStream";

// Lazy-load Monaco to avoid SSR issues
const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

/* ─── Types ─────────────────────────────────────────────────────────────── */

interface Contest {
    id: string;
    name: string;
    status: string;
    start_time: string;
    end_time: string;
    submission_limit: number;
    allowed_model: string;
    temperature: number;
}

interface Problem {
    id: string;
    title: string;
    statement: string;
    schema_json: Record<string, unknown> | null;
    time_limit_sec: number;
}

interface LeaderboardEntry {
    rank: number;
    user_id: string;
    username: string;
    rating: number;
    contest_score: number | null;
    delta: number | null;
}

/* ─── Helpers ───────────────────────────────────────────────────────────── */

function estimateTokens(text: string): number {
    // GPT-style estimate: ~4 chars per token
    return Math.ceil(text.length / 4);
}

function wordCount(text: string): number {
    return text.trim() ? text.trim().split(/\s+/).length : 0;
}

/* ─── Page ──────────────────────────────────────────────────────────────── */

export default function ContestDetailPage() {
    const params = useParams();
    const contestId = params.id as string;
    const { user } = useAuthStore();

    const [contest, setContest] = useState<Contest | null>(null);
    const [problems, setProblems] = useState<Problem[]>([]);
    const [selectedProblem, setSelectedProblem] = useState<Problem | null>(null);
    const [promptText, setPromptText] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState("");
    const [activeTab, setActiveTab] = useState<"problem" | "leaderboard">(
        "problem"
    );
    const [loading, setLoading] = useState(true);

    // Real-time leaderboard via SSE
    const { entries: leaderboard, isLive: lbIsLive } = useLeaderboardStream({
        streamPath: `/contests/${contestId}/leaderboard/stream`,
        restPath: `/contests/${contestId}/leaderboard`,
    });

    // Submission tracking
    const [trackedSubmissionId, setTrackedSubmissionId] = useState<string | null>(
        null
    );
    // Confirmation modal
    const [showConfirm, setShowConfirm] = useState(false);

    useEffect(() => {
        async function load() {
            try {
                const contestRes = await api.get(`/contests/${contestId}`);
                setContest(contestRes.data);

                try {
                    const problemsRes = await api.get(
                        `/contests/${contestId}/problems`
                    );
                    const probs = problemsRes.data;
                    setProblems(probs);
                    if (probs.length > 0) setSelectedProblem(probs[0]);
                } catch {
                    // Problems endpoint might not exist yet
                }
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [contestId]);

    function handleSubmitClick(e: FormEvent) {
        e.preventDefault();
        if (!selectedProblem || !promptText.trim()) return;
        setShowConfirm(true);
    }

    async function confirmSubmit() {
        if (!selectedProblem) return;
        setShowConfirm(false);
        setSubmitting(true);
        setSubmitError("");
        setTrackedSubmissionId(null);

        try {
            const { data } = await api.post("/submissions", {
                problem_id: selectedProblem.id,
                contest_id: contestId,
                prompt_text: promptText,
            });
            setTrackedSubmissionId(data.id);
        } catch (err: any) {
            setSubmitError(
                err.response?.data?.detail || "Submission failed. Try again."
            );
        } finally {
            setSubmitting(false);
        }
    }

    const rankColor = (rank: number) => {
        if (rank === 1) return "text-gold";
        if (rank === 2) return "text-silver";
        if (rank === 3) return "text-bronze";
        return "text-text-secondary";
    };

    /* ─── Loading / Error states ──────────────────────────────────────────── */

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </div>
        );
    }

    if (!contest) {
        return (
            <div className="mx-auto max-w-4xl px-6 py-20 text-center">
                <p className="text-text-secondary">Contest not found.</p>
            </div>
        );
    }

    /* ─── Render ──────────────────────────────────────────────────────────── */

    return (
        <div className="flex flex-col h-[calc(100vh-49px)] animate-fade-in">
            {/* ─── Contest Header ─────────────────────────────────────────────── */}
            <div className="shrink-0 border-b border-border px-6 py-3 flex items-center justify-between bg-surface/30">
                <div className="flex items-center gap-4">
                    <h1 className="text-lg font-bold truncate">{contest.name}</h1>
                    <span
                        className={`inline-flex text-xs font-medium px-2 py-0.5 rounded-full border ${contest.status === "active"
                            ? "bg-success/15 text-success border-success/30"
                            : contest.status === "scheduled"
                                ? "bg-warning/15 text-warning border-warning/30"
                                : "bg-text-muted/15 text-text-muted border-text-muted/30"
                            }`}
                    >
                        {contest.status}
                    </span>
                </div>

                <div className="flex items-center gap-6 text-xs text-text-muted">
                    <span>{contest.allowed_model}</span>
                    <span className="tabular-nums">Temp: {contest.temperature}</span>
                    <span>Limit: {contest.submission_limit}</span>
                    <CountdownTimer endTime={contest.end_time} />
                </div>
            </div>

            {/* ─── Tabs ───────────────────────────────────────────────────────── */}
            <div className="shrink-0 flex border-b border-border bg-surface/20 px-6">
                {(["problem", "leaderboard"] as const).map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === tab
                            ? "border-accent text-accent"
                            : "border-transparent text-text-secondary hover:text-foreground"
                            }`}
                    >
                        {tab === "problem" ? "Problem & Editor" : (
                            <>
                                Leaderboard
                                {lbIsLive && (
                                    <span className="relative flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
                                    </span>
                                )}
                            </>
                        )}
                    </button>
                ))}
            </div>

            {/* ─── Problem & Editor Tab ───────────────────────────────────────── */}
            {activeTab === "problem" && (
                <div className="flex-1 grid grid-cols-12 gap-0 min-h-0">
                    {/* Left Panel — Problem Statement (5 cols) */}
                    <div className="col-span-5 border-r border-border overflow-y-auto p-5">
                        {/* Problem Selector (if multiple) */}
                        {problems.length > 1 && (
                            <div className="mb-4">
                                <select
                                    value={selectedProblem?.id || ""}
                                    onChange={(e) =>
                                        setSelectedProblem(
                                            problems.find((p) => p.id === e.target.value) || null
                                        )
                                    }
                                    className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground focus:border-accent focus:outline-none"
                                >
                                    {problems.map((p) => (
                                        <option key={p.id} value={p.id}>
                                            {p.title}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {selectedProblem ? (
                            <div className="space-y-5">
                                <div>
                                    <h2 className="text-lg font-semibold mb-2">
                                        {selectedProblem.title}
                                    </h2>
                                    <div className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
                                        {selectedProblem.statement}
                                    </div>
                                </div>

                                {/* Constraints */}
                                <div className="rounded-md border border-border p-3 space-y-2">
                                    <h4 className="text-xs font-medium text-text-muted uppercase tracking-wider">
                                        Constraints
                                    </h4>
                                    <div className="flex items-center gap-4 text-xs text-text-secondary">
                                        <span>
                                            Time Limit:{" "}
                                            <span className="text-foreground font-medium">
                                                {selectedProblem.time_limit_sec}s
                                            </span>
                                        </span>
                                        <span>
                                            Model:{" "}
                                            <span className="text-foreground font-medium">
                                                {contest.allowed_model}
                                            </span>
                                        </span>
                                        <span>
                                            Temp:{" "}
                                            <span className="text-foreground font-medium tabular-nums">
                                                {contest.temperature}
                                            </span>
                                        </span>
                                    </div>
                                </div>

                                {/* Expected Schema */}
                                {selectedProblem.schema_json && (
                                    <div>
                                        <h4 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2">
                                            Expected Output Schema
                                        </h4>
                                        <pre className="rounded-md bg-background border border-border p-3 text-xs overflow-x-auto font-mono text-text-secondary">
                                            {JSON.stringify(selectedProblem.schema_json, null, 2)}
                                        </pre>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-full">
                                <p className="text-sm text-text-muted">
                                    No problems available for this contest yet.
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Right Panel — Editor & Submit (7 cols) */}
                    <div className="col-span-7 flex flex-col min-h-0">
                        {/* Monaco Editor */}
                        <div className="flex-1 min-h-0">
                            <Editor
                                height="100%"
                                language="plaintext"
                                theme="vs-dark"
                                value={promptText}
                                onChange={(v) => setPromptText(v || "")}
                                options={{
                                    minimap: { enabled: false },
                                    wordWrap: "on",
                                    fontSize: 13,
                                    lineNumbers: "on",
                                    scrollBeyondLastLine: false,
                                    padding: { top: 12 },
                                    renderLineHighlight: "gutter",
                                    suggestOnTriggerCharacters: false,
                                    quickSuggestions: false,
                                    parameterHints: { enabled: false },
                                    tabSize: 2,
                                    fontFamily: "var(--font-jetbrains-mono), monospace",
                                }}
                            />
                        </div>

                        {/* Bottom Bar — Stats, Submit, Results */}
                        <div className="shrink-0 border-t border-border p-4 space-y-3 bg-surface/20">
                            {/* Word/Token Stats */}
                            <div className="flex items-center justify-between text-xs text-text-muted">
                                <div className="flex items-center gap-4">
                                    <span>
                                        Words:{" "}
                                        <span className="text-foreground tabular-nums font-medium">
                                            {wordCount(promptText)}
                                        </span>
                                    </span>
                                    <span>
                                        Est. Tokens:{" "}
                                        <span className="text-foreground tabular-nums font-medium">
                                            {estimateTokens(promptText)}
                                        </span>
                                    </span>
                                    <span>
                                        Chars:{" "}
                                        <span className="text-foreground tabular-nums font-medium">
                                            {promptText.length}
                                        </span>
                                    </span>
                                </div>

                                <form onSubmit={handleSubmitClick}>
                                    <button
                                        type="submit"
                                        disabled={
                                            submitting ||
                                            !promptText.trim() ||
                                            !selectedProblem ||
                                            contest.status !== "active"
                                        }
                                        className="btn-primary px-6 py-1.5 text-sm disabled:opacity-50"
                                    >
                                        {submitting
                                            ? "Submitting..."
                                            : contest.status !== "active"
                                                ? "Contest Not Active"
                                                : "Submit Prompt"}
                                    </button>
                                </form>
                            </div>

                            {/* Error */}
                            {submitError && (
                                <div className="rounded-md bg-error/10 border border-error/30 px-3 py-2 text-sm text-error">
                                    {submitError}
                                </div>
                            )}

                            {/* Submission Tracker */}
                            {trackedSubmissionId && (
                                <SubmissionTracker submissionId={trackedSubmissionId} />
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* ─── Leaderboard Tab (Real-time via SSE) ──────────────────────── */}
            {activeTab === "leaderboard" && (
                <div className="flex-1 overflow-y-auto p-6">
                    <div className="max-w-4xl mx-auto">
                        {/* Live indicator */}
                        <div className="flex justify-end mb-3">
                            <div className={`flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium border ${lbIsLive
                                    ? "bg-success/10 border-success/30 text-success"
                                    : "bg-text-muted/10 border-text-muted/30 text-text-muted"
                                }`}>
                                {lbIsLive && (
                                    <span className="relative flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
                                    </span>
                                )}
                                {lbIsLive ? "LIVE" : "Polling"}
                            </div>
                        </div>

                        {leaderboard.length === 0 ? (
                            <div className="card text-center py-12">
                                <p className="text-text-muted">
                                    No entries yet. Be the first to submit!
                                </p>
                            </div>
                        ) : (
                            <div className="card overflow-hidden p-0">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-border text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                                            <th className="px-4 py-3">#</th>
                                            <th className="px-4 py-3">Player</th>
                                            <th className="px-4 py-3 text-right">Score</th>
                                            <th className="px-4 py-3 text-right">Rating</th>
                                            <th className="px-4 py-3 text-right">Delta</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/50">
                                        {leaderboard.map((entry) => (
                                            <tr
                                                key={entry.user_id}
                                                className={`transition-all duration-500 hover:bg-elevated/50 ${entry.user_id === user?.id ? "bg-accent/5" : ""}`}
                                            >
                                                <td className={`px-4 py-3 text-sm font-bold tabular-nums ${rankColor(entry.rank)}`}>
                                                    {entry.rank}
                                                </td>
                                                <td className="px-4 py-3 text-sm font-medium">
                                                    {entry.username}
                                                    {entry.user_id === user?.id && (
                                                        <span className="ml-2 text-xs text-accent">(you)</span>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm tabular-nums font-semibold text-accent">
                                                    {entry.contest_score?.toFixed(1) ?? "-"}
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm tabular-nums text-text-secondary">
                                                    {entry.rating}
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm tabular-nums font-medium">
                                                    {entry.delta !== null && entry.delta !== undefined ? (
                                                        <span className={entry.delta > 0 ? "text-success" : entry.delta < 0 ? "text-error" : "text-text-muted"}>
                                                            {entry.delta > 0 ? "+" : ""}{entry.delta}
                                                        </span>
                                                    ) : (
                                                        <span className="text-text-muted">--</span>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ─── Confirmation Modal ─────────────────────────────────────────── */}
            {showConfirm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="card w-full max-w-sm mx-4 animate-fade-in">
                        <h3 className="text-lg font-semibold mb-2">Confirm Submission</h3>
                        <p className="text-sm text-text-secondary mb-1">
                            You are about to submit your prompt for evaluation.
                        </p>
                        <div className="flex items-center gap-3 text-xs text-text-muted mb-4">
                            <span>
                                Words: <strong className="text-foreground">{wordCount(promptText)}</strong>
                            </span>
                            <span>
                                Est. Tokens: <strong className="text-foreground">{estimateTokens(promptText)}</strong>
                            </span>
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowConfirm(false)}
                                className="btn-secondary flex-1"
                            >
                                Cancel
                            </button>
                            <button onClick={confirmSubmit} className="btn-primary flex-1">
                                Submit
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
