"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import Sidebar from "@/components/layout/Sidebar";

export default function RootPage() {
  const { auth, hydrated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!hydrated) return;
    router.replace(auth.token ? "/dashboard" : "/auth/login");
  }, [hydrated, auth.token, router]);

  if (!hydrated) {
    return (
      <div className="layout-auth">
        <div className="spinner spinner-lg" />
      </div>
    );
  }

  if (auth.token) {
    return (
      <div className="layout">
        <Sidebar />
        <main className="layout-content" />
      </div>
    );
  }

  return null;
}
