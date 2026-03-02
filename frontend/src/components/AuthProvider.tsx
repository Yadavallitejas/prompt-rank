"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";

/**
 * AuthProvider — hydrates the auth store on mount.
 * Wrap the app root with this to auto-restore sessions.
 */
export default function AuthProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    const hydrate = useAuthStore((s) => s.hydrate);

    useEffect(() => {
        hydrate();
    }, [hydrate]);

    return <>{children}</>;
}
