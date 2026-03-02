"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";

interface Problem {
    id: string;
    title: string;
    statement: string;
    schema_json: Record<string, unknown> | null;
    time_limit_sec: number;
    contest_id: string | null;
    created_at: string;
}

interface Contest {
    id: string;
    name: string;
    status: string;
}

export default function AdminContestDetailPage() {
    const params = useParams();
    const contestId = params.id as string;

    const [contest, setContest] = useState<Contest | null>(null);
    const [problems, setProblems] = useState<Problem[]>([]);
    const [loading, setLoading] = useState(true);

    // Create problem form
    const [showCreate, setShowCreate] = useState(false);
    const [form, setForm] = useState({
        title: "",
        statement: "",
        schema_json: "",
        time_limit_sec: 30,
    });
    const [creating, setCreating] = useState(false);

    async function load() {
        try {
            const [contestRes, problemsRes] = await Promise.all([
                api.get(`/contests/${contestId}`),
                api.get(`/admin/contests/${contestId}/problems`),
            ]);
            setContest(contestRes.data);
            setProblems(problemsRes.data);
        } catch { }
        setLoading(false);
    }

    useEffect(() => {
        load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [contestId]);

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault();
        setCreating(true);
        try {
            let schemaObj = null;
            if (form.schema_json.trim()) {
                schemaObj = JSON.parse(form.schema_json);
            }
            await api.post("/admin/problem", {
                title: form.title,
                statement: form.statement,
                schema_json: schemaObj,
                time_limit_sec: form.time_limit_sec,
                contest_id: contestId,
            });
            setShowCreate(false);
            setForm({ title: "", statement: "", schema_json: "", time_limit_sec: 30 });
            load();
        } catch {
            alert("Failed to create problem. Check JSON validity.");
        }
        setCreating(false);
    }

    async function handleDelete(problemId: string) {
        if (!confirm("Delete this problem and all its testcases?")) return;
        try {
            await api.delete(`/admin/problems/${problemId}`);
            setProblems((prev) => prev.filter((p) => p.id !== problemId));
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
                <span className="text-foreground">{contest?.name || contestId}</span>
            </div>

            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">{contest?.name} — Problems</h1>
                <button
                    onClick={() => setShowCreate(!showCreate)}
                    className="btn-primary text-sm"
                >
                    {showCreate ? "Cancel" : "+ Add Problem"}
                </button>
            </div>

            {/* Create Problem Form */}
            {showCreate && (
                <form onSubmit={handleCreate} className="card mb-6 space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-text-muted mb-1">Title</label>
                        <input
                            type="text"
                            value={form.title}
                            onChange={(e) => setForm({ ...form, title: e.target.value })}
                            className="input w-full"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-text-muted mb-1">Problem Statement</label>
                        <textarea
                            value={form.statement}
                            onChange={(e) => setForm({ ...form, statement: e.target.value })}
                            className="input w-full h-32 font-mono text-sm"
                            required
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-text-muted mb-1">
                                Expected Output Schema (JSON, optional)
                            </label>
                            <textarea
                                value={form.schema_json}
                                onChange={(e) => setForm({ ...form, schema_json: e.target.value })}
                                className="input w-full h-20 font-mono text-xs"
                                placeholder='{"animal": "string", "habitat": "string"}'
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-text-muted mb-1">Time Limit (seconds)</label>
                            <input
                                type="number"
                                value={form.time_limit_sec}
                                onChange={(e) => setForm({ ...form, time_limit_sec: parseInt(e.target.value) })}
                                className="input w-full"
                                min={5}
                            />
                        </div>
                    </div>
                    <button type="submit" className="btn-primary" disabled={creating}>
                        {creating ? "Creating..." : "Create Problem"}
                    </button>
                </form>
            )}

            {/* Problems List */}
            {problems.length === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-text-secondary">No problems yet. Add one!</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {problems.map((p) => (
                        <div key={p.id} className="card flex items-center justify-between">
                            <div>
                                <Link
                                    href={`/admin/contests/${contestId}/problems/${p.id}`}
                                    className="text-sm font-medium text-accent hover:underline"
                                >
                                    {p.title}
                                </Link>
                                <p className="text-xs text-text-muted mt-1 line-clamp-1">
                                    {p.statement.substring(0, 120)}...
                                </p>
                            </div>
                            <div className="flex items-center gap-3">
                                <Link
                                    href={`/admin/contests/${contestId}/problems/${p.id}`}
                                    className="text-xs text-accent hover:underline"
                                >
                                    Manage Testcases →
                                </Link>
                                <button
                                    onClick={() => handleDelete(p.id)}
                                    className="text-xs text-error hover:text-error/80 font-medium"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
