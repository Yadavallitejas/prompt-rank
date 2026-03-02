"use client";

import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";

interface SubmissionTrackerProps {
    submissionId: string;
}

interface MetricBreakdown {
    accuracy?: number;
    consistency?: number;
    format_compliance?: number;
    token_efficiency?: number;
    latency?: number;
    robustness?: number;
}

interface SubmissionData {
    id: string;
    status: string;
    final_score: number | null;
    metrics_json: MetricBreakdown | null;
    created_at: string;
}

const STEPS = ["queued", "running", "evaluated"] as const;

const METRIC_LABELS: Record<string, { label: string; weight: string }> = {
    accuracy: { label: "Accuracy", weight: "40%" },
    consistency: { label: "Consistency", weight: "20%" },
    format_compliance: { label: "Format", weight: "15%" },
    token_efficiency: { label: "Tokens", weight: "10%" },
    robustness: { label: "Robustness", weight: "10%" },
    latency: { label: "Latency", weight: "5%" },
};

export default function SubmissionTracker({
    submissionId,
}: SubmissionTrackerProps) {
    const [data, setData] = useState<SubmissionData | null>(null);
    const [error, setError] = useState("");

    const poll = useCallback(async () => {
        try {
            const res = await api.get(`/submissions/${submissionId}`);
            setData(res.data);
            return res.data.status;
        } catch {
            setError("Failed to fetch submission status.");
            return "error";
        }
    }, [submissionId]);

    useEffect(() => {
        let timer: NodeJS.Timeout;
        let mounted = true;

        async function loop() {
            const status = await poll();
            if (mounted && (status === "queued" || status === "running")) {
                timer = setTimeout(loop, 3000);
            }
        }

        loop();
        return () => {
            mounted = false;
            clearTimeout(timer);
        };
    }, [poll]);

    if (error) {
        return (
            <div className="rounded-md bg-error/10 border border-error/30 px-3 py-2 text-sm text-error">
                {error}
            </div>
        );
    }

    if (!data) {
        return (
            <div className="flex items-center gap-2 text-sm text-text-muted py-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                Loading...
            </div>
        );
    }

    const currentStep = STEPS.indexOf(
        data.status as (typeof STEPS)[number]
    );
    const isFailed = data.status === "failed";

    return (
        <div className="space-y-4">
            {/* Status Pipeline */}
            <div className="flex items-center gap-1">
                {STEPS.map((step, i) => {
                    const isActive = data.status === step;
                    const isComplete = currentStep > i;
                    return (
                        <div key={step} className="flex items-center gap-1">
                            {i > 0 && (
                                <div
                                    className={`h-px w-6 ${isComplete ? "bg-accent" : "bg-border"
                                        }`}
                                />
                            )}
                            <div
                                className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-all ${isActive
                                        ? "bg-accent/15 text-accent ring-1 ring-accent/30"
                                        : isComplete
                                            ? "bg-success/15 text-success"
                                            : "bg-surface text-text-muted"
                                    }`}
                            >
                                {isActive && data.status !== "evaluated" && (
                                    <div className="h-2 w-2 animate-pulse rounded-full bg-current" />
                                )}
                                {isComplete && <span>✓</span>}
                                {step.charAt(0).toUpperCase() + step.slice(1)}
                            </div>
                        </div>
                    );
                })}
                {isFailed && (
                    <div className="flex items-center gap-1">
                        <div className="h-px w-6 bg-error" />
                        <div className="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium bg-error/15 text-error ring-1 ring-error/30">
                            Failed
                        </div>
                    </div>
                )}
            </div>

            {/* Results — only when evaluated */}
            {data.status === "evaluated" && data.final_score !== null && (
                <div className="space-y-3 animate-fade-in">
                    {/* Final Score */}
                    <div className="flex items-baseline gap-3">
                        <span className="text-3xl font-bold tabular-nums text-accent">
                            {data.final_score.toFixed(2)}
                        </span>
                        <span className="text-sm text-text-muted">/ 100</span>
                    </div>

                    {/* Metric Breakdown Table */}
                    {data.metrics_json && (
                        <div className="rounded-md border border-border overflow-hidden">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-surface text-xs text-text-muted uppercase tracking-wider">
                                        <th className="px-3 py-2 text-left">Metric</th>
                                        <th className="px-3 py-2 text-right">Weight</th>
                                        <th className="px-3 py-2 text-right">Score</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/50">
                                    {Object.entries(METRIC_LABELS).map(([key, meta]) => {
                                        const val =
                                            data.metrics_json?.[key as keyof MetricBreakdown];
                                        return (
                                            <tr
                                                key={key}
                                                className="hover:bg-elevated/30 transition-colors"
                                            >
                                                <td className="px-3 py-2 font-medium">
                                                    {meta.label}
                                                </td>
                                                <td className="px-3 py-2 text-right text-text-muted">
                                                    {meta.weight}
                                                </td>
                                                <td className="px-3 py-2 text-right tabular-nums font-semibold text-accent">
                                                    {val !== undefined ? (val * 100).toFixed(1) : "—"}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {isFailed && (
                <p className="text-sm text-error">
                    Evaluation failed. Please try submitting again.
                </p>
            )}
        </div>
    );
}
