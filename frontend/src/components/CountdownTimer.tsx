"use client";

import { useEffect, useState } from "react";

interface CountdownTimerProps {
    endTime: string;
}

export default function CountdownTimer({ endTime }: CountdownTimerProps) {
    const [timeLeft, setTimeLeft] = useState("");
    const [urgency, setUrgency] = useState<"normal" | "warning" | "critical">(
        "normal"
    );

    useEffect(() => {
        function tick() {
            const now = Date.now();
            const utcEndTime = endTime.endsWith("Z") ? endTime : `${endTime}Z`;
            const end = new Date(utcEndTime).getTime();
            const diff = end - now;

            if (diff <= 0) {
                setTimeLeft("Contest Ended");
                setUrgency("critical");
                return;
            }

            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
            const mins = Math.floor((diff / (1000 * 60)) % 60);
            const secs = Math.floor((diff / 1000) % 60);

            const pad = (n: number) => String(n).padStart(2, "0");

            if (days > 0) {
                setTimeLeft(`${days}d ${pad(hours)}:${pad(mins)}:${pad(secs)}`);
            } else {
                setTimeLeft(`${pad(hours)}:${pad(mins)}:${pad(secs)}`);
            }

            // Urgency levels
            const minutesLeft = diff / (1000 * 60);
            if (minutesLeft < 5) setUrgency("critical");
            else if (minutesLeft < 60) setUrgency("warning");
            else setUrgency("normal");
        }

        tick();
        const interval = setInterval(tick, 1000);
        return () => clearInterval(interval);
    }, [endTime]);

    const colorClass =
        urgency === "critical"
            ? "text-error"
            : urgency === "warning"
                ? "text-warning"
                : "text-text-secondary";

    return (
        <div className={`flex items-center gap-2 tabular-nums font-mono text-sm ${colorClass}`}>
            <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="shrink-0"
            >
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
            </svg>
            <span className="font-semibold">{timeLeft}</span>
        </div>
    );
}
