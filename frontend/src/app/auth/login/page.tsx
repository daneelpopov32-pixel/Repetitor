"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { motion } from "framer-motion";
import { scaleIn } from "@/lib/motion";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.login({ email, password });
      setAuth({ token: res.access_token, userId: res.user_id, role: res.role, email });
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    }
    setLoading(false);
  };

  return (
    <div className="layout-auth" style={{ background: "var(--c-bg)" }}>
      <motion.div
        className="card"
        style={{ width: "100%", maxWidth: 400, padding: "2rem" }}
        {...scaleIn}
      >
        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>🎓</div>
          <h1 style={{ fontSize: "var(--text-2xl)", fontWeight: 700 }}>Репетитор</h1>
          <p style={{ color: "var(--c-text-secondary)", fontSize: "var(--text-sm)" }}>
            Войдите в свой аккаунт
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Пароль"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <div className="error-text">{error}</div>}
          <Button type="submit" variant="accent" loading={loading} style={{ width: "100%", marginTop: "0.5rem" }}>
            Войти
          </Button>
        </form>

        <p style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>
          Нет аккаунта?{" "}
          <a href="/auth/register" style={{ fontWeight: 500 }}>Зарегистрироваться</a>
        </p>
      </motion.div>
    </div>
  );
}
