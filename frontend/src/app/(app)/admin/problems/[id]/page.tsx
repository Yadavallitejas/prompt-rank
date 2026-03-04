"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/lib/api";

interface Testcase {
    id: string;
    input_blob: string;
    expected_output_blob: string;
    is_adversarial: boolean;
}

export default function AdminProblemDetails() {
    const params = useParams();
    const router = useRouter();
    const problemId = params.id as string;

    const [testcases, setTestcases] = useState<Testcase[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);

    // Create form
    const [inputBlob, setInputBlob] = useState("");
    const [expectedOutput, setExpectedOutput] = useState("");
    const [isAdversarial, setIsAdversarial] = useState(false);

    // Edit state
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editInputBlob, setEditInputBlob] = useState("");
    const [editExpectedOutput, setEditExpectedOutput] = useState("");
    const [editIsAdversarial, setEditIsAdversarial] = useState(false);
    const [saving, setSaving] = useState(false);

    const fetchTestcases = () => {
        setLoading(true);
        api.get(`/admin/problems/${problemId}/testcases`)
            .then((res) => setTestcases(res.data))
            .catch((err) => console.error(err))
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchTestcases();
    }, [problemId]);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.post("/admin/testcases", {
                problem_id: problemId,
                input_blob: inputBlob,
                expected_output_blob: expectedOutput,
                is_adversarial: isAdversarial,
            });
            setIsCreating(false);
            setInputBlob("");
            setExpectedOutput("");
            setIsAdversarial(false);
            fetchTestcases();
        } catch (err) {
            console.error(err);
            alert("Failed to create testcase");
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Delete this testcase?")) return;
        try {
            await api.delete(`/admin/testcases/${id}`);
            fetchTestcases();
        } catch (err) {
            console.error(err);
        }
    };

    const startEditing = (t: Testcase) => {
        setEditingId(t.id);
        setEditInputBlob(t.input_blob);
        setEditExpectedOutput(t.expected_output_blob);
        setEditIsAdversarial(t.is_adversarial);
    };

    const cancelEditing = () => {
        setEditingId(null);
    };

    const handleSaveEdit = async (id: string) => {
        setSaving(true);
        try {
            await api.put(`/admin/testcases/${id}`, {
                input_blob: editInputBlob,
                expected_output_blob: editExpectedOutput,
                is_adversarial: editIsAdversarial,
            });
            setEditingId(null);
            fetchTestcases();
        } catch (err) {
            console.error(err);
            alert("Failed to update testcase");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="p-8 animate-fade-in max-w-5xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-4">
                    <button onClick={() => router.back()} className="text-text-muted hover:text-white transition-colors">
                        ← Back
                    </button>
                    <h1 className="text-2xl font-bold">Manage Testcases</h1>
                </div>
                <button
                    onClick={() => setIsCreating(!isCreating)}
                    className="btn-primary"
                >
                    {isCreating ? "Cancel" : "Add Testcase"}
                </button>
            </div>

            {isCreating && (
                <form onSubmit={handleCreate} className="card mb-8 space-y-4">
                    <h2 className="text-lg font-semibold mb-4">New Testcase</h2>
                    <div>
                        <label className="block text-sm font-medium mb-1">Input Blob (what the model sees)</label>
                        <textarea
                            required
                            rows={3}
                            className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent font-mono"
                            value={inputBlob}
                            onChange={(e) => setInputBlob(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Expected Output (for exact/eval scoring)</label>
                        <textarea
                            required
                            rows={3}
                            className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent font-mono"
                            value={expectedOutput}
                            onChange={(e) => setExpectedOutput(e.target.value)}
                        />
                    </div>
                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                        <input
                            type="checkbox"
                            checked={isAdversarial}
                            onChange={(e) => setIsAdversarial(e.target.checked)}
                            className="rounded border-border bg-surface text-accent focus:ring-accent"
                        />
                        Mark as Adversarial / Edge Case
                    </label>
                    <button type="submit" className="btn-primary w-full mt-2">
                        Create Testcase
                    </button>
                </form>
            )}

            {loading ? (
                <div className="flex justify-center p-8">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
            ) : (
                <div className="space-y-4">
                    {testcases.map((t, idx) => (
                        <div key={t.id} className="card relative">
                            {t.is_adversarial && editingId !== t.id && (
                                <span className="absolute top-4 right-4 bg-error/15 text-error text-xs px-2 py-1 rounded font-medium border border-error/30">
                                    Adversarial
                                </span>
                            )}
                            <h3 className="font-semibold text-lg mb-4 text-accent">Testcase #{idx + 1}</h3>

                            {editingId === t.id ? (
                                /* ── Edit Mode ─────────────────────── */
                                <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="text-sm font-medium text-text-muted mb-2 block">Input Blob</label>
                                            <textarea
                                                rows={5}
                                                className="w-full bg-surface border border-border rounded-md px-3 py-2 text-xs focus:outline-none focus:border-accent font-mono"
                                                value={editInputBlob}
                                                onChange={(e) => setEditInputBlob(e.target.value)}
                                            />
                                        </div>
                                        <div>
                                            <label className="text-sm font-medium text-text-muted mb-2 block">Expected Output</label>
                                            <textarea
                                                rows={5}
                                                className="w-full bg-surface border border-border rounded-md px-3 py-2 text-xs focus:outline-none focus:border-accent font-mono"
                                                value={editExpectedOutput}
                                                onChange={(e) => setEditExpectedOutput(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={editIsAdversarial}
                                            onChange={(e) => setEditIsAdversarial(e.target.checked)}
                                            className="rounded border-border bg-surface text-accent focus:ring-accent"
                                        />
                                        Adversarial / Edge Case
                                    </label>
                                    <div className="flex justify-end gap-2">
                                        <button
                                            onClick={cancelEditing}
                                            className="btn-secondary px-4 py-1.5 text-sm"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            onClick={() => handleSaveEdit(t.id)}
                                            disabled={saving}
                                            className="btn-primary px-4 py-1.5 text-sm"
                                        >
                                            {saving ? "Saving…" : "Save Changes"}
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                /* ── View Mode ─────────────────────── */
                                <>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <h4 className="text-sm font-medium text-text-muted mb-2">Input Blob</h4>
                                            <pre className="bg-surface border border-border p-3 rounded text-xs overflow-x-auto text-text-secondary h-32 whitespace-pre-wrap">
                                                {t.input_blob}
                                            </pre>
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-medium text-text-muted mb-2">Expected Output</h4>
                                            <pre className="bg-surface border border-border p-3 rounded text-xs overflow-x-auto text-text-secondary h-32 whitespace-pre-wrap">
                                                {t.expected_output_blob}
                                            </pre>
                                        </div>
                                    </div>
                                    <div className="mt-4 flex justify-end gap-2">
                                        <button
                                            onClick={() => startEditing(t)}
                                            className="btn-secondary px-3 py-1 text-sm text-accent border-accent/50 hover:bg-accent/10 hover:border-accent"
                                        >
                                            Edit
                                        </button>
                                        <button
                                            onClick={() => handleDelete(t.id)}
                                            className="btn-secondary px-3 py-1 text-sm text-error border-error/50 hover:bg-error/10 hover:border-error"
                                        >
                                            Delete
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                    {testcases.length === 0 && !isCreating && (
                        <div className="text-center p-8 text-text-muted">
                            No testcases for this problem yet.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
