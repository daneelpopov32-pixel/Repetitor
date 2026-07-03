"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  new: { label: "Новый", color: "#dbeafe" },
  viewed: { label: "Просмотрено", color: "#fef9c3" },
  in_progress: { label: "В работе", color: "#fed7aa" },
  completed: { label: "Выполнено", color: "#bbf7d0" },
};

const OPTION_LETTERS = "АБВГДЕЖЗИК";

export default function TestDetailPage() {
  const { id: testId } = useParams();
  const { auth, hydrated, logout } = useAuth();
  const router = useRouter();
  const [test, setTest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Replace state
  const [replaceTaskId, setReplaceTaskId] = useState<string | null>(null);
  const [replacing, setReplacing] = useState<string | null>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token || auth.role !== "TUTOR") {
      router.replace("/auth/login");
      return;
    }
    loadTest();
  }, [auth.token, hydrated, testId]);

  const loadTest = useCallback(async () => {
    try {
      const data = await api.getTest(testId as string, auth.token!);
      setTest(data);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  }, [auth.token, testId]);

  const deleteTest = async () => {
    if (!confirm("Удалить тест?")) return;
    try {
      await api.deleteTest(testId as string, auth.token!);
      router.push("/tests");
    } catch (e: any) {
      setError(e.message);
    }
  };

  const removeTask = async (taskId: string) => {
    if (!confirm("Удалить задание из теста?")) return;
    try {
      await api.removeTaskFromTest(testId as string, taskId, auth.token!);
      setTest((prev: any) => ({
        ...prev,
        tasks: prev.tasks.filter((t: any) => t.task_id !== taskId),
      }));
    } catch (e: any) {
      setError(e.message);
    }
  };

  const replaceTaskAction = async (taskId: string, newType: string) => {
    setReplacing(taskId);
    try {
      await api.replaceTask(testId as string, taskId, newType, auth.token!);
      setReplaceTaskId(null);
      await loadTest();
    } catch (e: any) {
      setError(e.message);
    }
    setReplacing(null);
  };

  const getTaskText = (task: any): string => {
    if (typeof task.text_content === "object" && task.text_content !== null) {
      return task.text_content.text || "";
    }
    return task.text_content || "";
  };

  const getTaskOptions = (task: any): string[] => {
    if (typeof task.text_content === "object" && task.text_content !== null) {
      // For matching tasks, prefer matching_right (clean data from table parsing)
      if (task.text_content.matching_right && Array.isArray(task.text_content.matching_right)) {
        return task.text_content.matching_right.map((item: any) => item.text || item.label || "");
      }
      const opts = task.text_content.options;
      if (Array.isArray(opts) && opts.length > 0) {
        if (Array.isArray(opts[0])) {
          return opts[0];
        }
        return opts;
      }
    }
    return [];
  };

  if (loading || !hydrated) {
    return (
      <div className="container" style={{ padding: "2rem" }}>
        Загрузка...
      </div>
    );
  }

  if (!test) {
    return (
      <div className="container" style={{ padding: "2rem" }}>
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          <h2>Тест не найден</h2>
          <Link href="/tests" className="btn btn-primary" style={{ marginTop: "1rem" }}>
            К списку тестов
          </Link>
        </div>
      </div>
    );
  }

  return (
    <>
      <header className="header">
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <button
            className="btn"
            style={{ background: "var(--border)", fontSize: "0.8rem" }}
            onClick={() => router.push("/tests")}
          >
            &larr; Назад
          </button>
          <h1 style={{ fontSize: "1.1rem" }}>{test.title}</h1>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <button className="btn btn-danger" style={{ fontSize: "0.8rem" }} onClick={deleteTest}>
            Удалить тест
          </button>
          <button className="btn btn-danger" style={{ fontSize: "0.8rem" }} onClick={logout}>
            Выйти
          </button>
        </div>
      </header>

      <main className="container" style={{ maxWidth: 800, padding: "2rem" }}>
        {error && (
          <div
            style={{
              padding: "0.75rem 1rem",
              background: "#fef2f2",
              border: "1px solid #fecaca",
              borderRadius: "var(--radius)",
              color: "var(--danger)",
              marginBottom: "1.5rem",
            }}
          >
            {error}
            <button
              onClick={() => setError("")}
              style={{ marginLeft: "0.5rem", background: "none", border: "none", cursor: "pointer", color: "var(--danger)" }}
            >
              ✕
            </button>
          </div>
        )}

        {/* Test info */}
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: "1.5rem",
            marginBottom: "2rem",
          }}
        >
          <h2 style={{ fontSize: "1.25rem", marginBottom: "0.75rem" }}>{test.title}</h2>
          <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
            {test.time_limit_minutes && <span>Таймер: {test.time_limit_minutes} мин</span>}
            <span>Заданий: {test.tasks?.length || 0}</span>
          </div>
          {test.assignments?.length > 0 && (
            <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              {test.assignments.map((a: any) => (
                <span
                  key={a.student_id}
                  style={{
                    fontSize: "0.8rem",
                    padding: "0.25rem 0.75rem",
                    borderRadius: "9999px",
                    background: STATUS_LABELS[a.status]?.color || "#f1f5f9",
                  }}
                >
                  {a.student_name || a.student_id.slice(0, 8)}: {STATUS_LABELS[a.status]?.label || a.status}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Tasks */}
        {test.tasks?.map((task: any, i: number) => {
          const text = getTaskText(task);
          const options = getTaskOptions(task);

          return (
            <div
              key={task.task_id}
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius)",
                marginBottom: "1.5rem",
                overflow: "hidden",
              }}
            >
              {/* Task header */}
              <div
                style={{
                  padding: "1rem 1.5rem",
                  borderBottom: "1px solid var(--border)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
                  <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: 600 }}>
                    Вопрос {i + 1}
                  </span>
                  <span
                    className={`badge ${task.type === "TEST" ? "badge-info" : "badge-warning"}`}
                    style={{ fontSize: "0.75rem" }}
                  >
                    {task.type}
                  </span>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <div style={{ position: "relative" }}>
                    <button
                      className="btn"
                      style={{
                        fontSize: "0.75rem",
                        padding: "0.3rem 0.75rem",
                        background: replaceTaskId === task.task_id ? "var(--primary)" : "var(--border)",
                        color: replaceTaskId === task.task_id ? "white" : "var(--text)",
                      }}
                      onClick={() => setReplaceTaskId(replaceTaskId === task.task_id ? null : task.task_id)}
                    >
                      {replacing === task.task_id ? "Замена..." : "Заменить"}
                    </button>
                    {replaceTaskId === task.task_id && replacing !== task.task_id && (
                      <div
                        style={{
                          position: "absolute",
                          top: "110%",
                          right: 0,
                          background: "var(--surface)",
                          border: "1px solid var(--border)",
                          borderRadius: "var(--radius)",
                          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                          zIndex: 10,
                          minWidth: 160,
                          padding: "0.5rem",
                        }}
                      >
                        <button
                          style={{
                            display: "block",
                            width: "100%",
                            textAlign: "left",
                            padding: "0.5rem 0.75rem",
                            border: "none",
                            background: "none",
                            borderRadius: "var(--radius)",
                            cursor: "pointer",
                            fontSize: "0.85rem",
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg)")}
                          onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
                          onClick={() => replaceTaskAction(task.task_id, "TEST")}
                        >
                          <span className="badge badge-info" style={{ marginRight: "0.5rem", fontSize: "0.7rem" }}>TEST</span>
                          Заменить на тест
                        </button>
                        <button
                          style={{
                            display: "block",
                            width: "100%",
                            textAlign: "left",
                            padding: "0.5rem 0.75rem",
                            border: "none",
                            background: "none",
                            borderRadius: "var(--radius)",
                            cursor: "pointer",
                            fontSize: "0.85rem",
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg)")}
                          onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
                          onClick={() => replaceTaskAction(task.task_id, "ESSAY")}
                        >
                          <span className="badge badge-warning" style={{ marginRight: "0.5rem", fontSize: "0.7rem" }}>ESSAY</span>
                          Заменить на сочинение
                        </button>
                      </div>
                    )}
                  </div>
                  <button
                    className="btn btn-danger"
                    style={{ fontSize: "0.75rem", padding: "0.3rem 0.75rem" }}
                    onClick={() => removeTask(task.task_id)}
                  >
                    Удалить
                  </button>
                </div>
              </div>

              {/* Task body */}
              <div style={{ padding: "1.5rem" }}>
                {/* Question text */}
                <p
                  style={{
                    fontSize: "0.95rem",
                    lineHeight: 1.7,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    marginBottom: task.text_content?.matching_left ? "1.25rem" : (options.length > 0 ? "1.25rem" : 0),
                  }}
                >
                  {text}
                </p>

                {/* Matching task: two-column layout with dropdowns */}
                {task.text_content?.matching_left && task.text_content?.matching_right ? (
                  <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
                    {/* Left column: stems */}
                    <div style={{ flex: 1, minWidth: 280 }}>
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                        Начала суждений
                      </div>
                      {task.text_content.matching_left.map((item: any, j: number) => (
                        <div
                          key={j}
                          style={{
                            display: "flex",
                            alignItems: "flex-start",
                            gap: "0.75rem",
                            padding: "0.75rem 1rem",
                            border: "1px solid var(--border)",
                            borderRadius: "var(--radius)",
                            marginBottom: "0.5rem",
                            fontSize: "0.9rem",
                            lineHeight: 1.5,
                            background: "var(--bg)",
                          }}
                        >
                          <span
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              minWidth: 28,
                              height: 28,
                              borderRadius: "50%",
                              border: "2px solid var(--primary)",
                              fontSize: "0.8rem",
                              fontWeight: 700,
                              color: "var(--primary)",
                              flexShrink: 0,
                            }}
                          >
                            {item.label}
                          </span>
                          <span style={{ flex: 1, paddingTop: "2px" }}>{item.text}</span>
                        </div>
                      ))}
                    </div>

                    {/* Right column: options */}
                    <div style={{ flex: 1, minWidth: 280 }}>
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                        Варианты завершения
                      </div>
                      {task.text_content.matching_right.map((item: any, j: number) => (
                        <div
                          key={j}
                          style={{
                            display: "flex",
                            alignItems: "flex-start",
                            gap: "0.75rem",
                            padding: "0.75rem 1rem",
                            border: "1px solid var(--border)",
                            borderRadius: "var(--radius)",
                            marginBottom: "0.5rem",
                            fontSize: "0.9rem",
                            lineHeight: 1.5,
                          }}
                        >
                          <span
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              minWidth: 28,
                              height: 28,
                              borderRadius: "50%",
                              border: "2px solid var(--border)",
                              fontSize: "0.8rem",
                              fontWeight: 600,
                              color: "var(--text-secondary)",
                              flexShrink: 0,
                            }}
                          >
                            {item.label}
                          </span>
                          <span style={{ flex: 1, paddingTop: "2px" }}>{item.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : options.length > 0 ? (
                  /* Regular TEST options */
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {options.map((opt: string, j: number) => (
                      <div
                        key={j}
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: "0.75rem",
                          padding: "0.75rem 1rem",
                          border: "1px solid var(--border)",
                          borderRadius: "var(--radius)",
                          fontSize: "0.9rem",
                          lineHeight: 1.5,
                        }}
                      >
                        <span
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            minWidth: 28,
                            height: 28,
                            borderRadius: "50%",
                            border: "2px solid var(--border)",
                            fontSize: "0.8rem",
                            fontWeight: 600,
                            color: "var(--text-secondary)",
                            flexShrink: 0,
                          }}
                        >
                          {OPTION_LETTERS[j] || j + 1}
                        </span>
                        <span style={{ flex: 1, paddingTop: "2px" }}>{opt}</span>
                      </div>
                    ))}
                  </div>
                ) : null}

                {/* Criteria for ESSAY */}
                {task.type === "ESSAY" && task.fipi_criteria && task.fipi_criteria.length > 0 && (
                  <div
                    style={{
                      marginTop: "1rem",
                      padding: "1rem",
                      background: "var(--bg)",
                      borderRadius: "var(--radius)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    <div style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.5rem", color: "var(--text-secondary)" }}>
                      Критерии ФИПИ:
                    </div>
                    {task.fipi_criteria.map((c: any, ci: number) => (
                      <div
                        key={ci}
                        style={{
                          fontSize: "0.85rem",
                          padding: "0.25rem 0",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {c.name || c}
                        {c.max_score != null && (
                          <span style={{ marginLeft: "0.5rem", fontSize: "0.75rem" }}>(макс. {c.max_score} б.)</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {test.tasks?.length === 0 && (
          <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
            <h2 style={{ color: "var(--text-secondary)" }}>Нет заданий</h2>
          </div>
        )}
      </main>
    </>
  );
}
