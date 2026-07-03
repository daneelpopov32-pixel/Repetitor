"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  new: { label: "Новый", color: "#dbeafe" },
  viewed: { label: "Просмотрено", color: "#fef9c3" },
  in_progress: { label: "В работе", color: "#fed7aa" },
  completed: { label: "Выполнено", color: "#bbf7d0" },
};

export default function TestsPage() {
  const { auth, hydrated, logout } = useAuth();
  const router = useRouter();
  const [tests, setTests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Filters
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [minTasks, setMinTasks] = useState("");
  const [maxTasks, setMaxTasks] = useState("");

  // Assign
  const [showAssign, setShowAssign] = useState<string | null>(null);
  const [students, setStudents] = useState<any[]>([]);
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token || auth.role !== "TUTOR") {
      router.replace("/auth/login");
      return;
    }
    loadTests();
  }, [auth.token, hydrated]);

  const loadTests = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (minTasks) params.min_tasks = minTasks;
      if (maxTasks) params.max_tasks = maxTasks;
      const data = await api.getTests(params, auth.token!);
      setTests(data);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  }, [auth.token, search, dateFrom, dateTo, minTasks, maxTasks]);

  useEffect(() => {
    if (hydrated && auth.token) loadTests();
  }, [search, dateFrom, dateTo, minTasks, maxTasks]);

  const deleteTest = async (testId: string) => {
    if (!confirm("Удалить тест?")) return;
    try {
      await api.deleteTest(testId, auth.token!);
      setTests((prev) => prev.filter((t) => t.test_id !== testId));
    } catch (e: any) {
      setError(e.message);
    }
  };

  const loadStudents = async () => {
    try {
      const data = await api.getTutorStudents(auth.token!);
      const flat = data.flatMap((d: any) =>
        d.student_id ? [{ id: d.student_id, name: `Ученик ${d.student_id.slice(0, 8)}` }] : []
      );
      setStudents(flat);
    } catch {}
  };

  const openAssign = async (testId: string) => {
    setShowAssign(testId);
    setSelectedStudents([]);
    await loadStudents();
  };

  const doAssign = async () => {
    if (!showAssign || selectedStudents.length === 0) return;
    try {
      await api.assignTestToStudents(showAssign, selectedStudents, auth.token!);
      setShowAssign(null);
      loadTests();
    } catch (e: any) {
      setError(e.message);
    }
  };

  if (loading || !hydrated) {
    return <div className="container" style={{ padding: "2rem" }}>Загрузка...</div>;
  }

  return (
    <>
      <header className="header">
        <h1>Мои тесты</h1>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <Link href="/tests/new" className="btn btn-primary">Создать тест</Link>
          <Link href="/dashboard" className="btn btn-primary" style={{ background: "var(--success)" }}>Дашборд</Link>
          <button className="btn btn-danger" onClick={logout}>Выйти</button>
        </div>
      </header>
      <main className="container" style={{ padding: "2rem" }}>
        {error && (
          <div style={{ padding: "0.75rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "var(--radius)", color: "var(--danger)", marginBottom: "1rem" }}>
            {error}
            <button onClick={() => setError("")} style={{ marginLeft: "0.5rem", background: "none", border: "none", cursor: "pointer" }}>✕</button>
          </div>
        )}

        {/* Filters */}
        <div className="card" style={{ marginBottom: "1rem" }}>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "flex-end" }}>
            <div className="form-group" style={{ flex: 1, minWidth: 200 }}>
              <label style={{ fontSize: "0.75rem" }}>Поиск</label>
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Название теста или ФИО ученика" style={{ width: "100%", padding: "0.4rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.875rem" }} />
            </div>
            <div className="form-group" style={{ minWidth: 130 }}>
              <label style={{ fontSize: "0.75rem" }}>Дата от</label>
              <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} style={{ width: "100%", padding: "0.4rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.875rem" }} />
            </div>
            <div className="form-group" style={{ minWidth: 130 }}>
              <label style={{ fontSize: "0.75rem" }}>Дата до</label>
              <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} style={{ width: "100%", padding: "0.4rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.875rem" }} />
            </div>
            <div className="form-group" style={{ minWidth: 80 }}>
              <label style={{ fontSize: "0.75rem" }}>Мин. заданий</label>
              <input type="number" value={minTasks} onChange={(e) => setMinTasks(e.target.value)} min="0" style={{ width: "100%", padding: "0.4rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.875rem" }} />
            </div>
            <div className="form-group" style={{ minWidth: 80 }}>
              <label style={{ fontSize: "0.75rem" }}>Макс. заданий</label>
              <input type="number" value={maxTasks} onChange={(e) => setMaxTasks(e.target.value)} min="0" style={{ width: "100%", padding: "0.4rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.875rem" }} />
            </div>
            <button className="btn btn-primary" onClick={loadTests} style={{ height: "2rem" }}>Найти</button>
          </div>
        </div>

        <p style={{ color: "var(--text-secondary)", marginBottom: "0.5rem", fontSize: "0.875rem" }}>Найдено: {tests.length}</p>

        {/* Tests list */}
        {tests.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
            <h2 style={{ color: "var(--text-secondary)" }}>Тестов нет</h2>
            <Link href="/tests/new" className="btn btn-primary" style={{ marginTop: "1rem" }}>Создать тест</Link>
          </div>
        ) : (
          tests.map((t) => (
            <div
              key={t.test_id}
              className="card"
              style={{
                cursor: "pointer",
                marginBottom: "0.75rem",
                padding: "1rem 1.25rem",
                transition: "border-color 0.15s",
              }}
              onClick={() => router.push(`/tests/${t.test_id}`)}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--primary)")}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <strong style={{ fontSize: "1rem" }}>{t.title}</strong>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                    {t.tasks_count} зад. | {t.assignments?.length || 0} назнач.
                    {t.time_limit_minutes ? ` | ${t.time_limit_minutes} мин` : ""}
                  </div>
                </div>
                <div style={{ display: "flex", gap: "0.35rem", flexShrink: 0 }}>
                  <button
                    className="btn"
                    style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", background: "var(--success)", color: "white" }}
                    onClick={(e) => { e.stopPropagation(); openAssign(t.test_id); }}
                  >
                    Назначить
                  </button>
                  <button
                    className="btn btn-danger"
                    style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem" }}
                    onClick={(e) => { e.stopPropagation(); deleteTest(t.test_id); }}
                  >
                    ✕
                  </button>
                </div>
              </div>
              {t.assignments?.length > 0 && (
                <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
                  {t.assignments.map((a: any) => (
                    <span
                      key={a.student_id}
                      style={{
                        fontSize: "0.7rem",
                        padding: "0.15rem 0.5rem",
                        borderRadius: "9999px",
                        background: STATUS_LABELS[a.status]?.color || "#f1f5f9",
                      }}
                    >
                      {a.student_name?.slice(0, 15) || "?"}: {STATUS_LABELS[a.status]?.label || a.status}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}

        {/* Assign modal */}
        {showAssign && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div className="card" style={{ maxWidth: 400, width: "100%" }}>
              <h3 style={{ marginBottom: "1rem" }}>Назначить тест ученикам</h3>
              {students.length === 0 ? (
                <p style={{ color: "var(--text-secondary)" }}>Нет привязанных учеников</p>
              ) : (
                <div style={{ maxHeight: 300, overflow: "auto", marginBottom: "1rem" }}>
                  {students.map((s) => (
                    <label key={s.id} style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.25rem 0" }}>
                      <input
                        type="checkbox"
                        checked={selectedStudents.includes(s.id)}
                        onChange={() =>
                          setSelectedStudents((prev) =>
                            prev.includes(s.id) ? prev.filter((x) => x !== s.id) : [...prev, s.id]
                          )
                        }
                      />
                      <span style={{ fontSize: "0.875rem" }}>{s.name}</span>
                    </label>
                  ))}
                </div>
              )}
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="btn btn-primary" onClick={doAssign} disabled={selectedStudents.length === 0}>
                  Назначить ({selectedStudents.length})
                </button>
                <button className="btn" style={{ background: "var(--border)" }} onClick={() => setShowAssign(null)}>
                  Отмена
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
