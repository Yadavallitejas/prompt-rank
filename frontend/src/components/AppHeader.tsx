"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";

const NAV_ITEMS = [
    { href: "/dashboard", label: "Dashboard", icon: "⌂" },
    { href: "/contests", label: "Contests", icon: "⚔" },
    { href: "/practice", label: "Practice", icon: "✎" },
    { href: "/leaderboard", label: "Leaderboard", icon: "★" },
];

export default function AppHeader() {
    const { user, logout } = useAuthStore();
    const pathname = usePathname();

    return (
        <header className="flex items-center justify-between px-6 py-3 border-b border-border bg-surface/50 backdrop-blur-sm sticky top-0 z-50">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 shrink-0">
                <svg
                    width="24"
                    height="24"
                    viewBox="0 0 28 28"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    className="text-accent"
                >
                    <path
                        d="M4 20L14 4L24 20H4Z"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinejoin="round"
                    />
                    <path
                        d="M14 14V18"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                    />
                </svg>
                <span className="text-base font-semibold tracking-tight">
                    Prompt<span className="text-accent">Rank</span>
                </span>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center gap-1">
                {NAV_ITEMS.map((item) => {
                    const isActive = pathname.startsWith(item.href);
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${isActive
                                ? "bg-accent/10 text-accent"
                                : "text-text-secondary hover:text-foreground hover:bg-surface"
                                }`}
                        >
                            <span className="text-xs">{item.icon}</span>
                            {item.label}
                        </Link>
                    );
                })}
                {user?.role === "admin" && (
                    <Link
                        href="/admin"
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${pathname.startsWith("/admin")
                            ? "bg-error/10 text-error"
                            : "text-text-secondary hover:text-foreground hover:bg-surface"
                            }`}
                    >
                        <span className="text-xs">⚙</span>
                        Admin
                    </Link>
                )}
            </nav>

            {/* User */}
            <div className="flex items-center gap-3 shrink-0">
                {user ? (
                    <>
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-medium">{user.username}</p>
                            <p className="text-xs tabular-nums text-text-muted">
                                ELO {user.rating}
                            </p>
                        </div>
                        <button
                            onClick={logout}
                            className="btn-secondary text-xs px-3 py-1.5"
                        >
                            Logout
                        </button>
                    </>
                ) : (
                    <Link href="/login" className="btn-primary text-xs px-3 py-1.5">
                        Sign In
                    </Link>
                )}
            </div>
        </header>
    );
}
