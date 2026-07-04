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

  // Multi-select
  const [selectedTests, setSelectedTests] = useState<Set<string>>(new Set());
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string[] | null>(null);

  // Assign
  const [showAssign, setShowAssign] = useState<string | null>(null);
  const [students, setStudents] = useState<any[]>([]);
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);

  // Student answers modal
  const [showAnswers, setShowAnswers] = useState<{ testId: string; studentId: string; studentName: string } | null>(null);
  const [studentAnswers, setStudentAnswers] = useState<any>(null);

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
    const test = tests.find((t) => t.test_id === testId);
    const hasAssignments = test?.assignments?.length > 0;

    if (hasAssignments) {
      setShowDeleteConfirm([testId]);
      return;
    }

    if (!confirm("Удалить тест?")) return;
    try {
      await api.deleteTest(testId, auth.token!);
      setTests((prev) => prev.filter((t) => t.test_id !== testId));
    } catch (e: any) {
      setError(e.message);
    }
  };

  const deleteSelected = () => {
    if (selectedTests.size === 0) return;

    const ids = Array.from(selectedTests);
    const hasAssigned = ids.some((id) => {
      const t = tests.find((tt) => tt.test_id === id);
      return t?.assignments?.length > 0;
    });

    setShowDeleteConfirm(ids);
  };

  const confirmDelete = async () => {
    if (!showDeleteConfirm) return;
    for (const testId of showDeleteConfirm) {
      try {
        await api.deleteTest(testId, auth.token!);
      } catch (e: any) {
        setError(e.message);
      }
    }
    setTests((prev) => prev.filter((t) => !showDeleteConfirm.includes(t.test_id)));
    setSelectedTests(new Set());
    setShowDeleteConfirm(null);
  };

  const toggleTestSelect = (testId: string) => {
    setSelectedTests((prev) => {
      const next = new Set(prev);
      if (next.has(testId)) next.delete(testId);
      else next.add(testId);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedTests.size === tests.length) {
      setSelectedTests(new Set());
    } else {
      setSelectedTests(new Set(tests.map((t) => t.test_id)));
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

  const unassignStudent = async (testId: string, studentId: string) => {
    if (!confirm("Снять ученика с теста?")) return;
    try {
      await api.unassignStudent(testId, studentId, auth.token!);
      loadTests();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const openAnswers = async (testId: string, studentId: string, studentName: string) => {
    setShowAnswers({ testId, studentId, studentName });
    try {
      const data = await api.getStudentAnswers(testId, studentId, auth.token!);
      setStudentAnswers(data);
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

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>Найдено: {tests.length}</p>
          {tests.length > 0 && (
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <label style={{ fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "0.3rem", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={selectedTests.size === tests.length && tests.length > 0}
                  onChange={toggleAll}
                />
                Выбрать все ({selectedTests.size}/{tests.length})
              </label>
              {selectedTests.size > 0 && (
                <button className="btn btn-danger" style={{ fontSize: "0.75rem", padding: "0.25rem 0.75rem" }} onClick={deleteSelected}>
                  Удалить ({selectedTests.size})
                </button>
              )}
            </div>
          )}
        </div>

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
                <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start", flex: 1 }}>
                  <input
                    type="checkbox"
                    checked={selectedTests.has(t.test_id)}
                    onChange={(e) => { e.stopPropagation(); toggleTestSelect(t.test_id); }}
                    onClick={(e) => e.stopPropagation()}
                    style={{ marginTop: "0.25rem", flexShrink: 0 }}
                  />
                  <div>
                    <strong style={{ fontSize: "1rem" }}>{t.title}</strong>
                    <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                      {t.tasks_count} зад. | {t.assignments?.length || 0} назнач.
                      {t.time_limit_minutes ? ` | ${t.time_limit_minutes} мин` : ""}
                    </div>
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

              {/* Student assignments with progress */}
              {t.assignments?.length > 0 && (
                <div style={{ marginTop: "0.75rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {t.assignments.map((a: any) => (
                    <div
                      key={a.student_id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.75rem",
                        padding: "0.5rem 0.75rem",
                        background: "var(--bg)",
                        borderRadius: "var(--radius)",
                        fontSize: "0.8rem",
                      }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <span style={{ fontWeight: 500, minWidth: 120 }}>
                        {a.student_name || a.student_id.slice(0, 8)}
                      </span>
                      <span
                        style={{
                          padding: "0.1rem 0.5rem",
                          borderRadius: "9999px",
                          background: STATUS_LABELS[a.status]?.color || "#f1f5f9",
                          fontSize: "0.7rem",
                        }}
                      >
                        {STATUS_LABELS[a.status]?.label || a.status}
                      </span>

                      {/* Progress bar */}
                      <div style={{ flex: 1, display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <div style={{
                          flex: 1,
                          height: "6px",
                          background: "#e2e8f0",
                          borderRadius: "3px",
                          overflow: "hidden",
                        }}>
                          <div style={{
                            width: `${a.progress_percent || 0}%`,
                            height: "100%",
                            background: a.progress_percent === 100 ? "var(--success)" : "var(--primary)",
                            borderRadius: "3px",
                            transition: "width 0.3s",
                          }} />
                        </div>
                        <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", minWidth: 35 }}>
                          {a.progress_percent || 0}%
                        </span>
                      </div>

                      {a.auto_score != null && (
                        <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>
                          Балл: {a.auto_score}
                        </span>
                      )}

                      <button
                        className="btn"
                        style={{ fontSize: "0.65rem", padding: "0.15rem 0.4rem", background: "var(--primary)", color: "white" }}
                        onClick={(e) => { e.stopPropagation(); openAnswers(t.test_id, a.student_id, a.student_name); }}
                      >
                        Ответы
                      </button>
                      <button
                        className="btn"
                        style={{ fontSize: "0.65rem", padding: "0.15rem 0.4rem", background: "var(--danger)", color: "white" }}
                        onClick={(e) => { e.stopPropagation(); unassignStudent(t.test_id, a.student_id); }}
                      >
                        Снять
                      </button>
                    </div>
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

        {/* Student answers modal */}
        {showAnswers && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div className="card" style={{ maxWidth: 700, width: "90%", maxHeight: "80vh", overflow: "auto" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <h3>Ответы: {showAnswers.studentName}</h3>
                <button className="btn" style={{ background: "var(--border)" }} onClick={() => { setShowAnswers(null); setStudentAnswers(null); }}>
                  Закрыть
                </button>
              </div>

              {!studentAnswers ? (
                <p style={{ color: "var(--text-secondary)" }}>Загрузка...</p>
              ) : studentAnswers.answers?.length === 0 ? (
                <p style={{ color: "var(--text-secondary)" }}>Нет ответов</p>
              ) : (
                <div>
                  <div style={{ marginBottom: "0.75rem", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                    Статус: {studentAnswers.status} | Балл: {studentAnswers.auto_score ?? "—"}
                  </div>
                  {studentAnswers.answers.map((ans: any) => (
                    <div key={ans.task_id} style={{ padding: "0.75rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", marginBottom: "0.5rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
                        <span style={{ fontWeight: 500, fontSize: "0.875rem" }}>
                          Задание {ans.order_number} ({ans.type})
                        </span>
                        {ans.auto_score != null && (
                          <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                            Балл: {ans.auto_score}
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.25rem" }}>
                        {(ans.text_content?.text || "").slice(0, 100)}...
                      </div>
                      <div style={{ fontSize: "0.875rem", padding: "0.5rem", background: "var(--bg)", borderRadius: "var(--radius)" }}>
                        <strong>Ответ:</strong> {ans.student_input || <em style={{ color: "var(--text-secondary)" }}>нет ответа</em>}
                      </div>
                      {ans.ai_feedback && (
                        <div style={{ fontSize: "0.8rem", marginTop: "0.25rem", color: "var(--text-secondary)" }}>
                          AI: {ans.ai_feedback}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
        {/* Delete confirmation modal */}
        {showDeleteConfirm && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div className="card" style={{ maxWidth: 400, width: "100%" }}>
              <h3 style={{ marginBottom: "1rem" }}>Подтвердите удаление</h3>
              <p style={{ marginBottom: "1rem", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                {showDeleteConfirm.length === 1
                  ? "Вы уверены, что хотите удалить тест?"
                  : `Вы уверены, что хотите удалить ${showDeleteConfirm.length} тестов?`}
              </p>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="btn btn-danger" onClick={confirmDelete}>
                  Удалить
                </button>
                <button className="btn" style={{ background: "var(--border)" }} onClick={() => setShowDeleteConfirm(null)}>
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
