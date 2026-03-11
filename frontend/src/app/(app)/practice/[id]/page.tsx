"use client";

import { useEffect, useState, FormEvent } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import { useAuthStore } from "@/stores/authStore";
import api from "@/lib/api";
import SubmissionTracker from "@/components/SubmissionTracker";
import MySubmissions from "@/components/MySubmissions";

const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

/* ─── Types ─────────────────────────────────────────────────────────────── */

interface Problem {
    id: string;
    title: string;
    statement: string;
    schema_json: Record<string, unknown> | null;
    time_limit_sec: number;
    difficulty: string;
}

interface SampleTestcase {
    id: string;
    input_blob: string;
    expected_output_blob: string;
}

/* ─── Helpers ───────────────────────────────────────────────────────────── */

function estimateTokens(text: string): number {
    return Math.ceil(text.length / 4);
}

function wordCount(text: string): number {
    return text.trim() ? text.trim().split(/\s+/).length : 0;
}

/* ─── Page ──────────────────────────────────────────────────────────────── */

export default function PracticeDetailPage() {
    const params = useParams();
    const problemId = params.id as string;
    const { user } = useAuthStore();

    const [problem, setProblem] = useState<Problem | null>(null);
    const [samples, setSamples] = useState<SampleTestcase[]>([]);
    const [promptText, setPromptText] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState("");
    const [loading, setLoading] = useState(true);
    const [showConfirm, setShowConfirm] = useState(false);
    const [trackedSubmissionId, setTrackedSubmissionId] = useState<
        string | null
    >(null);

    useEffect(() => {
        async function load() {
            try {
                const [probRes, samplesRes] = await Promise.all([
                    api.get(`/problems/${problemId}`),
                    api.get(`/problems/${problemId}/sample-testcases`),
                ]);
                setProblem(probRes.data);
                setSamples(samplesRes.data);
            } catch {
                /* problem not found */
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [problemId]);

    function handleSubmitClick(e: FormEvent) {
        e.preventDefault();
        if (!problem || !promptText.trim()) return;
        setShowConfirm(true);
    }

    async function confirmSubmit() {
        if (!problem) return;
        setShowConfirm(false);
        setSubmitting(true);
        setSubmitError("");
        setTrackedSubmissionId(null);

        try {
            const { data } = await api.post("/submissions", {
                problem_id: problem.id,
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

    const diffBadge = (d: string) => {
        const styles: Record<string, string> = {
            easy: "bg-success/15 text-success border-success/30",
            medium: "bg-warning/15 text-warning border-warning/30",
            hard: "bg-error/15 text-error border-error/30",
        };
        return styles[d] || styles.medium;
    };

    /* ─── Loading / Error ────────────────────────────────────────────────── */

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </div>
        );
    }

    if (!problem) {
        return (
            <div className="mx-auto max-w-4xl px-6 py-20 text-center">
                <p className="text-text-secondary">Problem not found.</p>
            </div>
        );
    }

    /* ─── Render ──────────────────────────────────────────────────────────── */

    return (
        <div className="flex flex-col h-[calc(100vh-49px)] animate-fade-in">
            {/* ─── Header ────────────────────────────────────────────────────── */}
            <div className="shrink-0 border-b border-border px-6 py-3 flex items-center justify-between bg-surface/30">
                <div className="flex items-center gap-4">
                    <h1 className="text-lg font-bold truncate">
                        {problem.title}
                    </h1>
                    <span
                        className={`inline-flex text-xs font-medium px-2.5 py-0.5 rounded-full border capitalize ${diffBadge(
                            problem.difficulty
                        )}`}
                    >
                        {problem.difficulty}
                    </span>
                    <span className="inline-flex text-xs font-medium px-2 py-0.5 rounded-full border bg-accent/10 text-accent border-accent/30">
                        Practice
                    </span>
                </div>

                <div className="flex items-center gap-4 text-xs text-text-muted">
                    <span>
                        Time Limit:{" "}
                        <span className="text-foreground font-medium">
                            {problem.time_limit_sec}s
                        </span>
                    </span>
                </div>
            </div>

            {/* ─── Main Grid ─────────────────────────────────────────────────── */}
            <div className="flex-1 grid grid-cols-12 gap-0 min-h-0">
                {/* Left Panel — Problem Statement (5 cols) */}
                <div className="col-span-5 border-r border-border overflow-y-auto p-5">
                    <div className="space-y-5">
                        {/* Statement */}
                        <div>
                            <h2 className="text-lg font-semibold mb-2">
                                Problem Statement
                            </h2>
                            <div className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
                                {problem.statement}
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
                                        {problem.time_limit_sec}s
                                    </span>
                                </span>
                                <span>
                                    Mode:{" "}
                                    <span className="text-foreground font-medium">
                                        Practice (no ELO impact)
                                    </span>
                                </span>
                            </div>
                        </div>

                        {/* Schema */}
                        {problem.schema_json && (
                            <div>
                                <h4 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2">
                                    Expected Output Schema
                                </h4>
                                <pre className="rounded-md bg-background border border-border p-3 text-xs overflow-x-auto font-mono text-text-secondary">
                                    {JSON.stringify(
                                        problem.schema_json,
                                        null,
                                        2
                                    )}
                                </pre>
                            </div>
                        )}

                        {/* Sample Testcases */}
                        {samples.length > 0 && (
                            <div>
                                <h4 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
                                    Sample Test Cases ({samples.length} of many)
                                </h4>
                                <div className="space-y-3">
                                    {samples.map((tc, idx) => (
                                        <div
                                            key={tc.id}
                                            className="rounded-md border border-border p-3 space-y-2"
                                        >
                                            <p className="text-xs font-medium text-accent">
                                                Sample #{idx + 1}
                                            </p>
                                            <div>
                                                <p className="text-xs text-text-muted mb-1">
                                                    Input:
                                                </p>
                                                <pre className="bg-background border border-border rounded p-2 text-xs font-mono text-text-secondary whitespace-pre-wrap">
                                                    {tc.input_blob}
                                                </pre>
                                            </div>
                                            <div>
                                                <p className="text-xs text-text-muted mb-1">
                                                    Expected Output:
                                                </p>
                                                <pre className="bg-background border border-border rounded p-2 text-xs font-mono text-success/80 whitespace-pre-wrap">
                                                    {tc.expected_output_blob}
                                                </pre>
                                            </div>
                                        </div>
                                    ))}
                                    <p className="text-xs text-text-muted italic">
                                        Additional hidden test cases (including
                                        adversarial edge cases) will be used
                                        during evaluation.
                                    </p>
                                </div>
                            </div>
                        )}
                        {/* My Submissions */}
                        <MySubmissions
                            problemId={problemId}
                            refreshTrigger={trackedSubmissionId}
                        />
                    </div>
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
                                fontFamily:
                                    "var(--font-jetbrains-mono), monospace",
                            }}
                        />
                    </div>

                    {/* Bottom Bar */}
                    <div className="shrink-0 border-t border-border p-4 space-y-3 bg-surface/20">
                        {/* Stats + Submit */}
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
                                        !user
                                    }
                                    className="btn-primary px-6 py-1.5 text-sm disabled:opacity-50"
                                >
                                    {submitting
                                        ? "Submitting..."
                                        : !user
                                            ? "Sign In to Submit"
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
                            <SubmissionTracker
                                submissionId={trackedSubmissionId}
                            />
                        )}
                    </div>
                </div>
            </div>

            {/* ─── Confirmation Modal ──────────────────────────────────────────── */}
            {showConfirm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="card w-full max-w-sm mx-4 animate-fade-in">
                        <h3 className="text-lg font-semibold mb-2">
                            Confirm Submission
                        </h3>
                        <p className="text-sm text-text-secondary mb-1">
                            Your prompt will be evaluated against all hidden test
                            cases (including adversarial ones).
                        </p>
                        <p className="text-xs text-text-muted mb-4">
                            Practice submissions do not affect your competitive
                            ELO rating.
                        </p>
                        <div className="flex items-center gap-3 text-xs text-text-muted mb-4">
                            <span>
                                Words:{" "}
                                <strong className="text-foreground">
                                    {wordCount(promptText)}
                                </strong>
                            </span>
                            <span>
                                Est. Tokens:{" "}
                                <strong className="text-foreground">
                                    {estimateTokens(promptText)}
                                </strong>
                            </span>
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowConfirm(false)}
                                className="btn-secondary flex-1"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmSubmit}
                                className="btn-primary flex-1"
                            >
                                Submit
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
