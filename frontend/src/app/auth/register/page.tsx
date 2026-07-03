"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Link from "next/link";

export default function RegisterPage() {
  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    birth_date: "",
    role: "STUDENT",
    invitation_code: "",
    consent_152fz: false,
  });
  const [error, setError] = useState("");
  const { setAuth } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const data = { ...form, birth_date: form.birth_date || undefined };
      const res = await api.register(data);
      setAuth({ token: res.access_token, userId: res.user_id, role: res.role, email: res.email });
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Ошибка регистрации");
    }
  };

  return (
    <div className="container" style={{ maxWidth: 400, marginTop: "2rem" }}>
      <div className="card">
        <h1 style={{ marginBottom: "1.5rem", textAlign: "center" }}>Регистрация</h1>
        {error && <div className="error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Пароль</label>
            <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Фамилия</label>
            <input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Имя</label>
            <input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Дата рождения</label>
            <input type="date" value={form.birth_date} onChange={(e) => setForm({ ...form, birth_date: e.target.value })} />
          </div>
          <div className="form-group">
            <label>Роль</label>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="TUTOR">Репетитор</option>
              <option value="STUDENT">Ученик</option>
            </select>
          </div>
          {form.role === "STUDENT" && (
            <div className="form-group">
              <label>Код приглашения (опционально)</label>
              <input value={form.invitation_code} onChange={(e) => setForm({ ...form, invitation_code: e.target.value })} />
            </div>
          )}
          <div className="form-group">
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <input
                type="checkbox"
                checked={form.consent_152fz}
                onChange={(e) => setForm({ ...form, consent_152fz: e.target.checked })}
                required
              />
              Я согласен на обработку персональных данных (152-ФЗ)
            </label>
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: "100%" }}>
            Зарегистрироваться
          </button>
        </form>
        <p style={{ marginTop: "1rem", textAlign: "center", fontSize: "0.875rem" }}>
          Уже есть аккаунт? <Link href="/auth/login">Войти</Link>
        </p>
      </div>
    </div>
  );
}
