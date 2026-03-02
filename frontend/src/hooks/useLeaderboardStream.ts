"use client";

import { useEffect, useState, useRef, useCallback } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UseLeaderboardStreamOptions {
    /** SSE stream URL path, e.g. "/leaderboard/stream" */
    streamPath: string;
    /** REST fallback URL path, e.g. "/leaderboard" */
    restPath: string;
    /** Polling interval in ms when SSE is unavailable (default 15000) */
    pollInterval?: number;
}

export interface LeaderboardEntry {
    rank: number;
    user_id: string;
    username: string;
    rating: number;
    created_at?: string;
    contest_score?: number | null;
    delta?: number | null;
}

/**
 * Custom hook that connects to an SSE leaderboard stream,
 * falls back to REST polling if SSE drops.
 */
export function useLeaderboardStream({
    streamPath,
    restPath,
    pollInterval = 15000,
}: UseLeaderboardStreamOptions) {
    const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
    const [isLive, setIsLive] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const eventSourceRef = useRef<EventSource | null>(null);
    const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

    const fetchRest = useCallback(async () => {
        try {
            const token =
                typeof window !== "undefined"
                    ? localStorage.getItem("pr_token")
                    : null;
            const headers: Record<string, string> = {};
            if (token) headers["Authorization"] = `Bearer ${token}`;

            const res = await fetch(`${API_BASE}${restPath}`, { headers });
            if (res.ok) {
                const data = await res.json();
                setEntries(data);
            }
        } catch {
            // Silently ignore
        } finally {
            setIsLoading(false);
        }
    }, [restPath]);

    const startPolling = useCallback(() => {
        if (pollTimerRef.current) clearInterval(pollTimerRef.current);
        pollTimerRef.current = setInterval(fetchRest, pollInterval);
    }, [fetchRest, pollInterval]);

    const stopPolling = useCallback(() => {
        if (pollTimerRef.current) {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
        }
    }, []);

    useEffect(() => {
        let cancelled = false;

        // Try to connect SSE
        const url = `${API_BASE}${streamPath}`;
        const es = new EventSource(url);
        eventSourceRef.current = es;

        es.onopen = () => {
            if (!cancelled) {
                setIsLive(true);
                stopPolling();
            }
        };

        es.onmessage = (event) => {
            if (cancelled) return;
            try {
                const data = JSON.parse(event.data);
                setEntries(data);
                setIsLoading(false);
            } catch {
                // Ignore invalid JSON (heartbeat comments)
            }
        };

        es.onerror = () => {
            if (cancelled) return;
            setIsLive(false);
            es.close();
            // Fall back to polling
            fetchRest();
            startPolling();
        };

        return () => {
            cancelled = true;
            es.close();
            stopPolling();
        };
    }, [streamPath, fetchRest, startPolling, stopPolling]);

    return { entries, isLive, isLoading };
}
