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
  const [viewMode, setViewMode] = useState<"single" | "list">("list");
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [showInfo, setShowInfo] = useState(false);

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

  const getShortText = (task: any): string => {
    const text = getTaskText(task);
    return text.length > 80 ? text.slice(0, 80) + "..." : text;
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

  const toggleExpand = (taskId: string) => {
    setExpandedTasks((prev) => {
      const next = new Set(prev);
      if (next.has(taskId)) next.delete(taskId);
      else next.add(taskId);
      return next;
    });
  };

  const renderTaskContent = (task: any, expanded: boolean) => {
    const tc = task.text_content;
    const isMatching = tc?.matching_left && tc?.matching_right;
    const isSequence = tc?.sequence_items;

    return (
      <div style={{ marginTop: expanded ? "0.75rem" : 0 }}>
        {/* Instruction */}
        <div style={{ fontSize: "0.875rem", lineHeight: 1.5, marginBottom: "0.5rem" }}>
          {expanded ? getInstruction(task) : getShortText(task)}
        </div>

        {/* Content: Matching */}
        {expanded && isMatching && (
          <div style={{ display: "flex", gap: "2rem", marginTop: "0.75rem" }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, textAlign: "center", marginBottom: "0.5rem", fontSize: "0.8rem" }}>
                {getLeftTitle(task)}
              </div>
              {tc.matching_left.map((item: any, j: number) => (
                <div key={j} style={{ fontSize: "0.8rem", marginBottom: "0.25rem" }}>
                  {item.label}) {item.text}
                </div>
              ))}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, textAlign: "center", marginBottom: "0.5rem", fontSize: "0.8rem" }}>
                {getRightTitle(task)}
              </div>
              {tc.matching_right.map((item: any, j: number) => (
                <div key={j} style={{ fontSize: "0.8rem", marginBottom: "0.25rem" }}>
                  {item.label}) {item.text}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Content: Sequence */}
        {expanded && isSequence && (
          <ol style={{ paddingLeft: "1.25rem", marginTop: "0.75rem" }}>
            {tc.sequence_items.map((item: any, j: number) => (
              <li key={j} style={{ fontSize: "0.8rem", marginBottom: "0.25rem" }}>{item.text}</li>
            ))}
          </ol>
        )}

        {/* Content: Default options */}
        {expanded && !isMatching && !isSequence && (() => {
          const opts = tc?.options;
          if (opts && Array.isArray(opts) && opts.length > 0) {
            const flatOpts = Array.isArray(opts[0]) ? opts[0] : opts;
            return (
              <div style={{ marginTop: "0.75rem" }}>
                {flatOpts.map((opt: string, i: number) => (
                  <div key={i} style={{ fontSize: "0.8rem", marginBottom: "0.25rem" }}>
                    {String.fromCharCode(65 + i)}) {opt}
                  </div>
                ))}
              </div>
            );
          }
          return null;
        })()}
      </div>
    );
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
                {a.progress_percent != null ? ` (${a.progress_percent}%)` : ""}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* View mode toggle */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button
          className={`btn ${viewMode === "single" ? "btn-primary" : ""}`}
          style={viewMode !== "single" ? { background: "var(--border)", color: "var(--text)" } : {}}
          onClick={() => setViewMode("single")}
        >
          По одному
        </button>
        <button
          className={`btn ${viewMode === "list" ? "btn-primary" : ""}`}
          style={viewMode !== "list" ? { background: "var(--border)", color: "var(--text)" } : {}}
          onClick={() => setViewMode("list")}
        >
          Список
        </button>
      </div>

      {/* Single view */}
      {viewMode === "single" && (
        <>
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

          {currentTask && (
            <div className="task-card">
              <div className="task-header">
                <span className="task-type-badge">
                  Тип {currentTask.exam_position || "?"} № {currentTask.block_id || currentTask.task_id?.slice(0, 8)}
                </span>
                <button
                  style={{ cursor: "pointer", fontSize: "0.85rem", padding: "0.1rem 0.3rem", border: "1px solid #ccc", borderRadius: "4px", background: "white" }}
                  onClick={() => setShowInfo(true)}
                >
                  i
                </button>
              </div>

              {/* Info Modal */}
              {showInfo && (
                <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
                  <div className="card" style={{ maxWidth: 500, width: "90%" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                      <h3 style={{ margin: 0 }}>Информация о задании</h3>
                      <button style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1.2rem" }} onClick={() => setShowInfo(false)}>Close</button>
                    </div>
                    <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>
                      Раздел кодификатора ФИПИ/Решу ЕГЭ: {currentTask.theme_name || currentTask.theme_id}
                    </p>
                    <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>
                      Тип задания: {currentTask.exam_position ? `Тип ${currentTask.exam_position}` : "—"}
                      {currentTask.difficulty_level ? ` (${currentTask.difficulty_level})` : ""}
                    </p>
                  </div>
                </div>
              )}

              {/* Images */}
              {currentTask.text_content?.images && currentTask.text_content.images.length > 0 && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem", margin: "1rem 0" }}>
                  {currentTask.text_content.images.map((imgPath: string, i: number) => (
                    <div key={i} style={{ position: "relative" }}>
                      <span style={{ position: "absolute", top: 4, left: 4, background: "rgba(0,0,0,0.6)", color: "white", padding: "0.1rem 0.4rem", borderRadius: "4px", fontSize: "0.75rem", fontWeight: 600, zIndex: 1 }}>
                        {i + 1})
                      </span>
                      <img
                        src={`/api/v1/media/images/${imgPath.split("/").pop()}`}
                        alt={`${i + 1}`}
                        style={{ width: "100%", display: "block", border: "1px solid #e0e0e0", borderRadius: "4px" }}
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    </div>
                  ))}
                </div>
              )}

              {renderTaskContent(currentTask, true)}

              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid #e0e0e0" }}>
                <button className="nav-button" style={{ color: "#dc2626", borderColor: "#dc2626" }} onClick={() => removeTask(currentTask.task_id)}>
                  Удалить задание
                </button>
              </div>
            </div>
          )}

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
        </>
      )}

      {/* List view */}
      {viewMode === "list" && (
        <div>
          {test.tasks?.map((task: any, idx: number) => {
            const isExpanded = expandedTasks.has(task.task_id);
            return (
              <div
                key={task.task_id}
                className="task-card"
                style={{ cursor: "pointer", marginBottom: "0.5rem" }}
                onClick={() => toggleExpand(task.task_id)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <span style={{ fontWeight: 600, minWidth: 24 }}>{idx + 1}</span>
                  <span style={{
                    fontSize: "0.75rem",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "4px",
                    background: "#e0e7ff",
                    color: "#3730a3",
                  }}>
                    Тип {task.exam_position || "?"}
                  </span>
                  <span style={{
                    fontSize: "0.7rem",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "9999px",
                    background: task.type === "TEST" ? "#dcfce7" : "#fef3c7",
                    color: task.type === "TEST" ? "#166534" : "#92400e",
                  }}>
                    {task.type}
                  </span>
                  <span style={{ flex: 1, fontSize: "0.85rem", color: "var(--text)" }}>
                    {getShortText(task)}
                  </span>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    {isExpanded ? "▲" : "▼"}
                  </span>
                </div>

                {isExpanded && renderTaskContent(task, true)}

                {isExpanded && (
                  <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid #e0e0e0" }}>
                    <button
                      className="nav-button"
                      style={{ color: "#dc2626", borderColor: "#dc2626", fontSize: "0.8rem" }}
                      onClick={(e) => { e.stopPropagation(); removeTask(task.task_id); }}
                    >
                      Удалить задание
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
