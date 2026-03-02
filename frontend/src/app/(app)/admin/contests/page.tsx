"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

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

export default function AdminContestsPage() {
    const [contests, setContests] = useState<Contest[]>([]);
    const [loading, setLoading] = useState(true);

    // Create form
    const [showCreate, setShowCreate] = useState(false);
    const [form, setForm] = useState({
        name: "",
        start_time: "",
        end_time: "",
        submission_limit: 3,
        allowed_model: "gpt-4o-mini",
        temperature: 0.7,
        seed_base: 42,
    });
    const [creating, setCreating] = useState(false);

    async function loadContests() {
        try {
            const res = await api.get("/admin/contests");
            setContests(res.data);
        } catch { }
        setLoading(false);
    }

    useEffect(() => {
        loadContests();
    }, []);

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault();
        setCreating(true);
        try {
            await api.post("/admin/contest", form);
            setShowCreate(false);
            setForm({
                name: "",
                start_time: "",
                end_time: "",
                submission_limit: 3,
                allowed_model: "gpt-4o-mini",
                temperature: 0.7,
                seed_base: 42,
            });
            loadContests();
        } catch { }
        setCreating(false);
    }

    async function handleDelete(id: string) {
        if (!confirm("Are you sure you want to delete this contest?")) return;
        try {
            await api.delete(`/admin/contests/${id}`);
            setContests((prev) => prev.filter((c) => c.id !== id));
        } catch { }
    }

    async function handleFinalize(id: string) {
        if (!confirm("Finalize this contest? This will compute ELO ratings and cannot be undone.")) return;
        try {
            await api.post(`/leaderboard/finalize/${id}`);
            alert("Contest finalized! ELO ratings updated.");
            loadContests();
        } catch {
            alert("Failed to finalize. Is the contest ended with evaluated submissions?");
        }
    }

    const statusBadge = (status: string) => {
        const map: Record<string, string> = {
            active: "bg-success/15 text-success border-success/30",
            scheduled: "bg-warning/15 text-warning border-warning/30",
            ended: "bg-text-muted/15 text-text-muted border-text-muted/30",
        };
        return map[status] || map.ended;
    };

    return (
        <div className="p-8 animate-fade-in">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Contests</h1>
                <button
                    onClick={() => setShowCreate(!showCreate)}
                    className="btn-primary text-sm"
                >
                    {showCreate ? "Cancel" : "+ Create Contest"}
                </button>
            </div>

            {/* Create Form */}
            {showCreate && (
                <form onSubmit={handleCreate} className="card mb-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-text-muted mb-1">Name</label>
                            <input
                                type="text"
                                value={form.name}
                                onChange={(e) => setForm({ ...form, name: e.target.value })}
                                className="input w-full"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-text-muted mb-1">Allowed Model</label>
                            <input
                                type="text"
                                value={form.allowed_model}
                                onChange={(e) => setForm({ ...form, allowed_model: e.target.value })}
                                className="input w-full"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-text-muted mb-1">Start Time</label>
                            <input
                                type="datetime-local"
                                value={form.start_time}
                                onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                                className="input w-full"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-text-muted mb-1">End Time</label>
                            <input
                                type="datetime-local"
                                value={form.end_time}
                                onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                                className="input w-full"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-text-muted mb-1">Submission Limit</label>
                            <input
                                type="number"
                                value={form.submission_limit}
                                onChange={(e) => setForm({ ...form, submission_limit: parseInt(e.target.value) })}
                                className="input w-full"
                                min={1}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-text-muted mb-1">Temperature</label>
                            <input
                                type="number"
                                step="0.1"
                                value={form.temperature}
                                onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })}
                                className="input w-full"
                                min={0}
                                max={2}
                            />
                        </div>
                    </div>
                    <button type="submit" className="btn-primary" disabled={creating}>
                        {creating ? "Creating..." : "Create Contest"}
                    </button>
                </form>
            )}

            {/* Contests Table */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
            ) : contests.length === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-text-secondary">No contests yet. Create one!</p>
                </div>
            ) : (
                <div className="card overflow-hidden p-0">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-border text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                                <th className="px-4 py-3">Name</th>
                                <th className="px-4 py-3">Status</th>
                                <th className="px-4 py-3">Model</th>
                                <th className="px-4 py-3">Dates</th>
                                <th className="px-4 py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border/50">
                            {contests.map((c) => (
                                <tr key={c.id} className="hover:bg-elevated/50 transition-colors">
                                    <td className="px-4 py-3">
                                        <Link
                                            href={`/admin/contests/${c.id}`}
                                            className="text-sm font-medium text-accent hover:underline"
                                        >
                                            {c.name}
                                        </Link>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={`inline-flex text-xs font-medium px-2 py-0.5 rounded-full border ${statusBadge(c.status)}`}>
                                            {c.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-xs text-text-secondary">{c.allowed_model}</td>
                                    <td className="px-4 py-3 text-xs text-text-muted tabular-nums">
                                        {new Date(c.start_time).toLocaleDateString()} — {new Date(c.end_time).toLocaleDateString()}
                                    </td>
                                    <td className="px-4 py-3 text-right space-x-2">
                                        <button
                                            onClick={() => handleFinalize(c.id)}
                                            className="text-xs text-warning hover:text-warning/80 font-medium"
                                        >
                                            Finalize
                                        </button>
                                        <button
                                            onClick={() => handleDelete(c.id)}
                                            className="text-xs text-error hover:text-error/80 font-medium"
                                        >
                                            Delete
                                        </button>
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
