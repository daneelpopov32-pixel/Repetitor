"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { motion } from "framer-motion";
import { scaleIn } from "@/lib/motion";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Button from "@/components/ui/Button";

export default function RegisterPage() {
  const [form, setForm] = useState({
    email: "", password: "", first_name: "", last_name: "",
    birth_date: "", role: "STUDENT", invitation_code: "", consent: false,
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuth();
  const router = useRouter();

  const update = (field: string, value: string | boolean) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.consent) { setError("Необходимо согласие на обработку ПДн"); return; }
    setError("");
    setLoading(true);
    try {
      const res = await api.register({
        email: form.email, password: form.password,
        first_name: form.first_name, last_name: form.last_name,
        birth_date: form.birth_date || null,
        role: form.role,
        invitation_code: form.role === "STUDENT" ? form.invitation_code : undefined,
        consent_152fz: form.consent,
      });
      setAuth({ token: res.access_token, userId: res.user_id, role: res.role, email: form.email });
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ошибка регистрации");
    }
    setLoading(false);
  };

  return (
    <div className="layout-auth" style={{ background: "var(--c-bg)" }}>
      <motion.div
        className="card"
        style={{ width: "100%", maxWidth: 440, padding: "2rem" }}
        {...scaleIn}
      >
        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>🎓</div>
          <h1 style={{ fontSize: "var(--text-2xl)", fontWeight: 700 }}>Регистрация</h1>
          <p style={{ color: "var(--c-text-secondary)", fontSize: "var(--text-sm)" }}>
            Создайте аккаунт для работы с тестами ФИПИ
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <Input label="Имя" placeholder="Иван" value={form.first_name} onChange={(e) => update("first_name", e.target.value)} required />
            <Input label="Фамилия" placeholder="Иванов" value={form.last_name} onChange={(e) => update("last_name", e.target.value)} required />
          </div>
          <Input label="Email" type="email" placeholder="you@example.com" value={form.email} onChange={(e) => update("email", e.target.value)} required />
          <Input label="Пароль" type="password" placeholder="••••••••" value={form.password} onChange={(e) => update("password", e.target.value)} required />
          <Input label="Дата рождения" type="date" value={form.birth_date} onChange={(e) => update("birth_date", e.target.value)} />
          <Select
            label="Роль"
            value={form.role}
            onChange={(e) => update("role", e.target.value)}
            options={[{ value: "STUDENT", label: "Ученик" }, { value: "TUTOR", label: "Репетитор" }]}
          />
          {form.role === "STUDENT" && (
            <Input label="Код приглашения" placeholder="Введите код от репетитора" value={form.invitation_code} onChange={(e) => update("invitation_code", e.target.value)} />
          )}
          <label style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem", fontSize: "var(--text-sm)", color: "var(--c-text-secondary)", cursor: "pointer" }}>
            <input type="checkbox" checked={form.consent} onChange={(e) => update("consent", e.target.checked)} style={{ marginTop: 2 }} />
            <span>Согласен на обработку персональных данных в соответствии с 152-ФЗ</span>
          </label>
          {error && <div className="error-text">{error}</div>}
          <Button type="submit" variant="accent" loading={loading} style={{ width: "100%", marginTop: "0.5rem" }}>
            Зарегистрироваться
          </Button>
        </form>

        <p style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>
          Уже есть аккаунт?{" "}
          <a href="/auth/login" style={{ fontWeight: 500 }}>Войти</a>
        </p>
      </motion.div>
    </div>
  );
}
