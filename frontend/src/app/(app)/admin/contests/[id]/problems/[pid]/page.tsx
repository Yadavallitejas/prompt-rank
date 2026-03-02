"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";

interface Testcase {
    id: string;
    problem_id: string;
    input_blob: string;
    expected_output_blob: string;
    is_adversarial: boolean;
    created_at: string;
}

interface Problem {
    id: string;
    title: string;
}

export default function AdminTestcasesPage() {
    const params = useParams();
    const contestId = params.id as string;
    const problemId = params.pid as string;

    const [problem, setProblem] = useState<Problem | null>(null);
    const [testcases, setTestcases] = useState<Testcase[]>([]);
    const [loading, setLoading] = useState(true);

    // Create form
    const [showCreate, setShowCreate] = useState(false);
    const [form, setForm] = useState({
        input_blob: "",
        expected_output_blob: "",
        is_adversarial: false,
    });
    const [creating, setCreating] = useState(false);

    async function load() {
        try {
            const tcRes = await api.get(`/admin/problems/${problemId}/testcases`);
            setTestcases(tcRes.data);
            // Try to get problem title
            try {
                const probRes = await api.get(`/contests/${contestId}/problems`);
                const found = probRes.data.find((p: Problem) => p.id === problemId);
                if (found) setProblem(found);
            } catch { }
        } catch { }
        setLoading(false);
    }

    useEffect(() => {
        load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [problemId]);

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault();
        setCreating(true);
        try {
            await api.post("/admin/testcases", {
                problem_id: problemId,
                input_blob: form.input_blob,
                expected_output_blob: form.expected_output_blob,
                is_adversarial: form.is_adversarial,
            });
            setShowCreate(false);
            setForm({ input_blob: "", expected_output_blob: "", is_adversarial: false });
            load();
        } catch {
            alert("Failed to create testcase.");
        }
        setCreating(false);
    }

    async function handleDelete(id: string) {
        if (!confirm("Delete this testcase?")) return;
        try {
            await api.delete(`/admin/testcases/${id}`);
            setTestcases((prev) => prev.filter((t) => t.id !== id));
        } catch { }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </div>
        );
    }

    return (
        <div className="p-8 animate-fade-in">
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-xs text-text-muted mb-4">
                <Link href="/admin/contests" className="hover:text-foreground">Contests</Link>
                <span>/</span>
                <Link href={`/admin/contests/${contestId}`} className="hover:text-foreground">
                    Contest
                </Link>
                <span>/</span>
                <span className="text-foreground">{problem?.title || "Problem"}</span>
            </div>

            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold">
                        Hidden Testcases
                    </h1>
                    <p className="text-sm text-text-muted mt-1">
                        {problem?.title} — {testcases.length} testcase{testcases.length !== 1 && "s"}
                    </p>
                </div>
                <button
                    onClick={() => setShowCreate(!showCreate)}
                    className="btn-primary text-sm"
                >
                    {showCreate ? "Cancel" : "+ Add Testcase"}
                </button>
            </div>

            {/* Create Testcase Form */}
            {showCreate && (
                <form onSubmit={handleCreate} className="card mb-6 space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-text-muted mb-1">
                            Input (text that will be passed as user message to the LLM)
                        </label>
                        <textarea
                            value={form.input_blob}
                            onChange={(e) => setForm({ ...form, input_blob: e.target.value })}
                            className="input w-full h-24 font-mono text-xs"
                            placeholder="The African elephant lives in savanna grasslands and forests. It is a herbivore that eats leaves, bark, grass, and fruits."
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-text-muted mb-1">
                            Expected Output (JSON the LLM should produce)
                        </label>
                        <textarea
                            value={form.expected_output_blob}
                            onChange={(e) => setForm({ ...form, expected_output_blob: e.target.value })}
                            className="input w-full h-24 font-mono text-xs"
                            placeholder='{"animal": "African elephant", "habitat": "savanna grasslands and forests", "diet": "herbivore"}'
                            required
                        />
                    </div>
                    <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                        <input
                            type="checkbox"
                            checked={form.is_adversarial}
                            onChange={(e) => setForm({ ...form, is_adversarial: e.target.checked })}
                            className="rounded border-border"
                        />
                        Adversarial testcase (edge case / tricky input)
                    </label>
                    <button type="submit" className="btn-primary" disabled={creating}>
                        {creating ? "Creating..." : "Create Testcase"}
                    </button>
                </form>
            )}

            {/* Testcases List */}
            {testcases.length === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-text-secondary">No testcases yet. Add one!</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {testcases.map((tc, idx) => (
                        <div key={tc.id} className="card space-y-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-bold text-text-muted">
                                        TC #{idx + 1}
                                    </span>
                                    {tc.is_adversarial && (
                                        <span className="text-xs px-2 py-0.5 rounded-full bg-error/10 text-error border border-error/20">
                                            Adversarial
                                        </span>
                                    )}
                                </div>
                                <button
                                    onClick={() => handleDelete(tc.id)}
                                    className="text-xs text-error hover:text-error/80 font-medium"
                                >
                                    Delete
                                </button>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-xs font-medium text-text-muted mb-1">Input</p>
                                    <pre className="text-xs bg-background border border-border rounded-md p-3 overflow-x-auto font-mono text-text-secondary max-h-32 overflow-y-auto">
                                        {tc.input_blob}
                                    </pre>
                                </div>
                                <div>
                                    <p className="text-xs font-medium text-text-muted mb-1">Expected Output</p>
                                    <pre className="text-xs bg-background border border-border rounded-md p-3 overflow-x-auto font-mono text-text-secondary max-h-32 overflow-y-auto">
                                        {tc.expected_output_blob}
                                    </pre>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
