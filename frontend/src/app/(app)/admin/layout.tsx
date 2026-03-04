"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";

const ADMIN_NAV = [
    { href: "/admin", label: "Overview", icon: "📊" },
    { href: "/admin/contests", label: "Contests", icon: "⚔" },
    { href: "/admin/problems", label: "Practice Problems", icon: "📝" },
];

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user } = useAuthStore();
    const router = useRouter();
    const pathname = usePathname();

    // Route guard: redirect non-admin users
    useEffect(() => {
        if (user && user.role !== "admin") {
            router.replace("/dashboard");
        }
    }, [user, router]);

    if (!user || user.role !== "admin") {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </div>
        );
    }

    return (
        <div className="flex min-h-[calc(100vh-49px)]">
            {/* Sidebar */}
            <aside className="w-56 shrink-0 border-r border-border bg-surface/30 py-4 px-3">
                <h2 className="px-3 mb-4 text-xs font-semibold text-text-muted uppercase tracking-widest">
                    Admin Panel
                </h2>
                <nav className="space-y-1">
                    {ADMIN_NAV.map((item) => {
                        const isActive =
                            item.href === "/admin"
                                ? pathname === "/admin"
                                : pathname.startsWith(item.href);
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive
                                    ? "bg-accent/10 text-accent"
                                    : "text-text-secondary hover:text-foreground hover:bg-elevated/50"
                                    }`}
                            >
                                <span>{item.icon}</span>
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>
            </aside>

            {/* Main */}
            <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
    );
}
