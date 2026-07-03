"use client";

import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
  const { auth, hydrated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!hydrated) return;
    if (auth.token) {
      router.replace("/dashboard");
    } else {
      router.replace("/auth/login");
    }
  }, [auth.token, hydrated, router]);

  return <main style={{ padding: "2rem" }}>Загрузка...</main>;
}
