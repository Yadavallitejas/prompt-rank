"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

interface Problem {
    id: string;
    title: string;
    difficulty: string;
    time_limit_sec: number;
    is_practice: boolean;
}

export default function AdminProblemsPage() {
    const [problems, setProblems] = useState<Problem[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);

    // Form state
    const [title, setTitle] = useState("");
    const [statement, setStatement] = useState("");
    const [difficulty, setDifficulty] = useState("medium");
    const [timeLimit, setTimeLimit] = useState("30");

    const fetchProblems = () => {
        setLoading(true);
        // Note: For now we leverage the public practice endpoint for listing, 
        // to show we can see the problems, or we could just list all from a new admin endpoint if it existed.
        api.get("/problems")
            .then((res) => setProblems(res.data))
            .catch((err) => console.error(err))
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchProblems();
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.post("/admin/problem", {
                title,
                statement,
                difficulty,
                time_limit_sec: parseInt(timeLimit),
                is_practice: true,
            });
            setIsCreating(false);
            setTitle("");
            setStatement("");
            setDifficulty("medium");
            setTimeLimit("30");
            fetchProblems();
        } catch (error) {
            console.error("Failed to create problem", error);
            alert("Failed to create problem. Check console.");
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure you want to delete this problem?")) return;
        try {
            await api.delete(`/admin/problems/${id}`);
            fetchProblems();
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="p-8 animate-fade-in max-w-5xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">Practice Problems</h1>
                <button
                    onClick={() => setIsCreating(!isCreating)}
                    className="btn-primary"
                >
                    {isCreating ? "Cancel" : "Add Practice Problem"}
                </button>
            </div>

            {isCreating && (
                <form onSubmit={handleCreate} className="card mb-8 space-y-4">
                    <h2 className="text-lg font-semibold mb-4">Create New Problem</h2>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">Title</label>
                            <input
                                required
                                type="text"
                                className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Difficulty</label>
                            <select
                                className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent"
                                value={difficulty}
                                onChange={(e) => setDifficulty(e.target.value)}
                            >
                                <option value="easy">Easy</option>
                                <option value="medium">Medium</option>
                                <option value="hard">Hard</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Statement</label>
                        <textarea
                            required
                            rows={4}
                            className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent"
                            value={statement}
                            onChange={(e) => setStatement(e.target.value)}
                            placeholder="Write a highly competitive prompt that outputs valid JSON..."
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Time Limit (sec)</label>
                        <input
                            required
                            type="number"
                            className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent"
                            value={timeLimit}
                            onChange={(e) => setTimeLimit(e.target.value)}
                        />
                    </div>
                    <button type="submit" className="btn-primary w-full">
                        Create Problem
                    </button>
                </form>
            )}

            {loading ? (
                <div className="flex justify-center p-8">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
            ) : (
                <div className="space-y-4">
                    {problems.map((p) => (
                        <div key={p.id} className="card flex justify-between items-center">
                            <div>
                                <h3 className="font-semibold text-lg">{p.title}</h3>
                                <p className="text-sm text-text-muted mt-1 capitalize">
                                    Difficulty: {p.difficulty} | Time Limit: {p.time_limit_sec}s
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <Link href={`/admin/problems/${p.id}`} className="btn-secondary px-3 py-1">
                                    Manage Testcases
                                </Link>
                                <button
                                    onClick={() => handleDelete(p.id)}
                                    className="btn-secondary px-3 py-1 text-error border-error/50 hover:bg-error/10 hover:border-error"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    ))}
                    {problems.length === 0 && !isCreating && (
                        <div className="text-center p-8 text-text-muted">
                            No practice problems found.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
