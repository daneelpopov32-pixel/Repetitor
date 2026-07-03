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

export default function TestDetailPage() {
  const { id: testId } = useParams();
  const { auth, hydrated, logout } = useAuth();
  const router = useRouter();
  const [test, setTest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentIdx, setCurrentIdx] = useState(0);

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

  const getTaskText = (task: any): string => {
    const tc = task.text_content;
    if (typeof tc === "object" && tc !== null) return tc.text || "";
    return tc || "";
  };

  const getInstruction = (task: any): string => {
    const text = getTaskText(task);
    const tc = task.text_content;
    const lines = text.split("\n");
    const instructionLines: string[] = [];
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      if (tc?.matching_left?.length && /^[А-Я]\)/.test(trimmed)) break;
      if (tc?.sequence_items?.length && /^\d+\)/.test(trimmed)) break;
      instructionLines.push(trimmed);
    }
    return instructionLines.join(" ") || text;
  };

  const getLeftTitle = (task: any): string => {
    const text = getTaskText(task);
    const possibleTitles = ["СОБЫТИЕ", "СОБЫТИЯ", "ПРОЦЕССЫ", "ФАКТЫ", "ГОД", "ГОДЫ",
      "УЧАСТНИКИ", "ФРАГМЕНТЫ ИСТОЧНИКОВ", "ХАРАКТЕРИСТИКИ", "ПАМЯТНИКИ КУЛЬТУРЫ",
      "ПРОИЗВЕДЕНИЯ КУЛЬТУРЫ", "НАЧАЛА СУЖДЕНИЙ"];
    for (const t of possibleTitles) {
      if (text.includes(t)) return t;
    }
    return "ЛЕВЫЙ СТОЛБЕЦ";
  };

  const getRightTitle = (task: any): string => {
    const text = getTaskText(task);
    const possibleTitles = ["ГОД", "ГОДЫ", "ФАКТЫ", "УЧАСТНИКИ", "ХАРАКТЕРИСТИКИ",
      "ВАРИАНТЫ ЗАВЕРШЕНИЯ", "ВАРИАНТЫ ЗАВЕРШЕНИЯ СУЖДЕНИЙ"];
    for (const t of possibleTitles) {
      if (text.includes(t)) return t;
    }
    return "ПРАВЫЙ СТОЛБЕЦ";
  };

  if (loading || !hydrated) {
    return <div className="test-screen"><div className="task-card" style={{ textAlign: "center" }}>Загрузка...</div></div>;
  }

  if (!test) {
    return (
      <div className="test-screen">
        <div className="task-card" style={{ textAlign: "center" }}>
          <h2>Тест не найден</h2>
          <Link href="/tests" className="submit-button" style={{ marginTop: "1rem", display: "inline-block" }}>
            К списку тестов
          </Link>
        </div>
      </div>
    );
  }

  const currentTask = test.tasks?.[currentIdx];
  const tc = currentTask?.text_content;
  const isMatching = tc?.matching_left && tc?.matching_right;
  const isSequence = tc?.sequence_items;

  return (
    <div className="test-screen">
      {/* Header */}
      <div className="test-header">
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <Link href="/tests" className="nav-button">&larr; Назад</Link>
          <div className="test-title">{test.title}</div>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <span style={{ fontSize: "0.85rem", color: "#666" }}>
            {test.tasks?.length || 0} заданий
            {test.time_limit_minutes ? ` | ${test.time_limit_minutes} мин` : ""}
          </span>
          <button className="submit-button" style={{ background: "#dc2626" }} onClick={deleteTest}>
            Удалить тест
          </button>
          <button className="nav-button" onClick={logout}>Выйти</button>
        </div>
      </div>

      {error && (
        <div style={{ padding: "0.75rem 1rem", background: "#ffebee", border: "1px solid #fecaca", borderRadius: "4px", color: "#c62828", marginBottom: "1rem" }}>
          {error}
          <button onClick={() => setError("")} style={{ marginLeft: "0.5rem", background: "none", border: "none", cursor: "pointer", color: "#c62828" }}>✕</button>
        </div>
      )}

      {/* Assignments */}
      {test.assignments?.length > 0 && (
        <div className="task-card" style={{ marginBottom: "1rem" }}>
          <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.5rem" }}>Назначения:</div>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {test.assignments.map((a: any) => (
              <span key={a.student_id} style={{ fontSize: "0.8rem", padding: "0.2rem 0.6rem", borderRadius: "9999px", background: STATUS_LABELS[a.status]?.color || "#f1f5f9" }}>
                {a.student_name || a.student_id.slice(0, 8)}: {STATUS_LABELS[a.status]?.label || a.status}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Navigation */}
      {test.tasks?.length > 0 && (
        <div className="task-navigation">
          <button className="nav-button" disabled={currentIdx === 0} onClick={() => setCurrentIdx((i) => i - 1)}>
            ← Предыдущее
          </button>
          <span className="task-counter">Задание {currentIdx + 1} из {test.tasks.length}</span>
          <button className="nav-button" disabled={currentIdx === test.tasks.length - 1} onClick={() => setCurrentIdx((i) => i + 1)}>
            Следующее →
          </button>
        </div>
      )}

      {/* Task Card */}
      {currentTask && (
        <div className="task-card">
          {/* Header */}
          <div className="task-header">
            <span className="task-type-badge">
              Тип {currentTask.order_number || currentIdx + 1} № {currentTask.block_id || currentTask.task_id?.slice(0, 8)}
            </span>
            <span style={{ fontSize: "0.8rem", color: "#666" }}>{currentTask.type}</span>
          </div>

          {/* Instruction */}
          <div className="task-instruction">{getInstruction(currentTask)}</div>

          {/* Content: Matching */}
          {isMatching && (
            <div className="task-content matching-layout">
              <div className="matching-columns">
                <div className="column left-column">
                  <div className="column-title">{getLeftTitle(currentTask)}</div>
                  <div className="column-items">
                    {tc.matching_left.map((item: any, j: number) => (
                      <div key={j} className="item">{item.label}) {item.text}</div>
                    ))}
                  </div>
                </div>
                <div className="column right-column">
                  <div className="column-title">{getRightTitle(currentTask)}</div>
                  <div className="column-items">
                    {tc.matching_right.map((item: any, j: number) => (
                      <div key={j} className="item">{item.label}) {item.text}</div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Content: Chronology */}
          {isSequence && (
            <div className="task-content chronology-layout">
              <ol className="events-list">
                {tc.sequence_items.map((item: any, j: number) => (
                  <li key={j} className="event-item">{item.text}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Content: Default */}
          {!isMatching && !isSequence && (
            <div className="task-content">
              {(() => {
                const opts = tc?.options;
                if (opts && Array.isArray(opts) && opts.length > 0) {
                  const flatOpts = Array.isArray(opts[0]) ? opts[0] : opts;
                  return (
                    <div>
                      {flatOpts.map((opt: string, i: number) => (
                        <div key={i} className="item" style={{ marginBottom: "8px" }}>
                          {String.fromCharCode(65 + i)}) {opt}
                        </div>
                      ))}
                    </div>
                  );
                }
                return null;
              })()}
            </div>
          )}

          {/* Task footer */}
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid #e0e0e0" }}>
            <button className="nav-button" style={{ color: "#dc2626", borderColor: "#dc2626" }} onClick={() => removeTask(currentTask.task_id)}>
              Удалить задание
            </button>
          </div>
        </div>
      )}

      {/* Bottom navigation */}
      {test.tasks?.length > 0 && (
        <div className="task-navigation" style={{ marginTop: "1rem" }}>
          <button className="nav-button" disabled={currentIdx === 0} onClick={() => setCurrentIdx((i) => i - 1)}>
            ← Предыдущее
          </button>
          <span className="task-counter">Задание {currentIdx + 1} из {test.tasks.length}</span>
          <button className="nav-button" disabled={currentIdx === test.tasks.length - 1} onClick={() => setCurrentIdx((i) => i + 1)}>
            Следующее →
          </button>
        </div>
      )}
    </div>
  );
}
