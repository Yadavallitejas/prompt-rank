"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/authStore";

/**
 * AuthProvider — hydrates the auth store on mount.
 * Shows a loading screen while restoring the session,
 * so protected pages don't flash the login screen.
 */
export default function AuthProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    const hydrate = useAuthStore((s) => s.hydrate);
    const [ready, setReady] = useState(false);

    useEffect(() => {
        async function init() {
            await hydrate();
            setReady(true);
        }
        init();
    }, [hydrate]);

    if (!ready) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </div>
        );
    }

    return <>{children}</>;
}
