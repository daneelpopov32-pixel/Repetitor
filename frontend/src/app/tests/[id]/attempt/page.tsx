"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const OPTION_LETTERS = "АБВГДЕЖЗИК";

export default function AttemptPage() {
  const { id: attemptId } = useParams();
  const { auth, hydrated } = useAuth();
  const router = useRouter();
  const [tasks, setTasks] = useState<any[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [remaining, setRemaining] = useState<number | null>(null);
  const [attempt, setAttempt] = useState<any>(null);
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<any>(null);
  const debounceRef = useRef<NodeJS.Timeout>(null);
  const timerRef = useRef<NodeJS.Timeout>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token) {
      router.replace("/auth/login");
      return;
    }
    loadData();
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [auth.token, hydrated, attemptId]);

  const loadData = async () => {
    try {
      const att = await api.getAttempt(attemptId as string, auth.token!);
      setAttempt(att);
      if (att.status !== "IN_PROGRESS") {
        setSubmitted(true);
        return;
      }
      const taskData = await api.getAttemptTasks(attemptId as string, auth.token!);
      setTasks(taskData.tasks || []);

      if (att.time_limit_minutes && att.started_at) {
        const started = new Date(att.started_at).getTime();
        const limit = att.time_limit_minutes * 60 * 1000;
        const serverNow = new Date(att.server_time).getTime();
        const elapsed = serverNow - started;
        const left = Math.max(0, Math.floor((limit - elapsed) / 1000));
        setRemaining(left);

        timerRef.current = setInterval(() => {
          setRemaining((prev) => {
            if (prev === null || prev <= 1) {
              if (timerRef.current) clearInterval(timerRef.current);
              setSubmitted(true);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
      }
    } catch {}
  };

  const saveAnswer = useCallback(
    async (taskId: string, value: string) => {
      try {
        await api.saveAnswer(attemptId as string, taskId, value, auth.token!);
      } catch {}
    },
    [attemptId, auth.token]
  );

  const handleChange = (taskId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [taskId]: value }));
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => saveAnswer(taskId, value), 1000);
  };

  const handleMatchingAnswer = (taskId: string, stemIdx: number, value: string) => {
    setAnswers((prev) => {
      const current = prev[taskId] || "";
      const parts = current ? current.split(",") : [];
      parts[stemIdx] = value;
      const newAnswer = parts.join(",");
      return { ...prev, [taskId]: newAnswer };
    });
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const current = answers[taskId] || "";
      const parts = current ? current.split(",") : [];
      parts[stemIdx] = value;
      saveAnswer(taskId, parts.join(","));
    }, 1000);
  };

  const handleSubmit = async () => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    for (const [taskId, value] of Object.entries(answers)) {
      await saveAnswer(taskId, value);
    }
    try {
      const res = await api.submitAttempt(attemptId as string, auth.token!);
      setResult(res);
      setSubmitted(true);
      if (timerRef.current) clearInterval(timerRef.current);
    } catch {}
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const getTaskText = (task: any): string => {
    const tc = task.text_content;
    if (typeof tc === "object" && tc !== null) return tc.text || "";
    return tc || "";
  };

  if (submitted && result) {
    return (
      <div className="container" style={{ maxWidth: 600, padding: "2rem" }}>
        <div className="card" style={{ textAlign: "center" }}>
          <h1 style={{ marginBottom: "1rem" }}>Тест завершён!</h1>
          <p>Статус: <span className="badge badge-info">{result.status}</span></p>
          <p>Балл за тестовую часть: <strong>{result.auto_score}</strong> / {result.max_auto_score}</p>
          {result.pending_essay_count > 0 && (
            <p style={{ color: "var(--text-secondary)" }}>
              {result.pending_essay_count} задание(я) ожидают проверки репетитором
            </p>
          )}
          <button className="btn btn-primary" style={{ marginTop: "1.5rem" }} onClick={() => router.push("/dashboard")}>
            На главную
          </button>
        </div>
      </div>
    );
  }

  if (submitted && !result) {
    return <div className="container" style={{ padding: "2rem" }}>Время истекло. Тест завершён.</div>;
  }

  if (tasks.length === 0) {
    return <div className="container" style={{ padding: "2rem" }}>Загрузка заданий...</div>;
  }

  const currentTask = tasks[currentIdx];
  const tc = currentTask.text_content;
  const taskText = getTaskText(currentTask);
  const isMatching = tc?.matching_left && tc?.matching_right;
  const isSequence = tc?.sequence_items;
  const answersPerStem = tc?.answers_per_stem || 1;

  // Parse matching answer: "1,3,2,4" → array of per-stem selections
  const matchingParts = isMatching ? (answers[currentTask.task_id] || "").split(",") : [];

  return (
    <>
      <header className="header">
        <h1 style={{ fontSize: "1rem" }}>Прохождение теста</h1>
        <div style={{ display: "flex", gap: "1.5rem", alignItems: "center" }}>
          {remaining !== null && (
            <span
              style={{
                fontFamily: "monospace",
                fontSize: "1.25rem",
                fontWeight: 600,
                color: remaining < 60 ? "var(--danger)" : "var(--text)",
              }}
            >
              {formatTime(remaining)}
            </span>
          )}
          <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
            {currentIdx + 1} / {tasks.length}
          </span>
        </div>
      </header>
      <main className="container" style={{ maxWidth: 900, padding: "2rem" }}>
        <div className="card">
          {/* Header: badge + type + hint */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
            <span
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: 36,
                height: 36,
                borderRadius: "var(--radius)",
                background: "var(--primary)",
                color: "white",
                fontSize: "0.9rem",
                fontWeight: 700,
              }}
            >
              {currentIdx + 1}
            </span>
            <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              {currentTask.type}
              {currentTask.block_id && <span style={{ marginLeft: "0.5rem" }}>#{currentTask.block_id}</span>}
            </span>
            {currentTask.hint && (
              <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontStyle: "italic" }}>
                {currentTask.hint}
              </span>
            )}
          </div>

          {/* Condition text */}
          <p style={{ fontSize: "0.95rem", lineHeight: 1.7, whiteSpace: "pre-wrap", wordBreak: "break-word", marginBottom: "1.5rem" }}>
            {taskText}
          </p>

          {/* Matching task: two-column list + answer table */}
          {isMatching ? (
            <div>
              {/* Two-column list */}
              <div style={{ display: "flex", gap: "2rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
                {/* Left column: stems */}
                <div style={{ flex: 1, minWidth: 280 }}>
                  <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.5rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Начала суждений
                  </div>
                  {tc.matching_left.map((item: any, j: number) => (
                    <div
                      key={j}
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "0.5rem",
                        padding: "0.5rem 0.75rem",
                        borderBottom: "1px solid var(--border)",
                        fontSize: "0.9rem",
                        lineHeight: 1.5,
                      }}
                    >
                      <span style={{ fontWeight: 700, color: "var(--primary)", flexShrink: 0 }}>
                        {item.label})
                      </span>
                      <span style={{ flex: 1 }}>{item.text}</span>
                    </div>
                  ))}
                </div>

                {/* Right column: options */}
                <div style={{ flex: 1, minWidth: 280 }}>
                  <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.5rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Варианты завершения
                  </div>
                  {tc.matching_right.map((item: any, j: number) => (
                    <div
                      key={j}
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "0.5rem",
                        padding: "0.5rem 0.75rem",
                        borderBottom: "1px solid var(--border)",
                        fontSize: "0.9rem",
                        lineHeight: 1.5,
                      }}
                    >
                      <span style={{ fontWeight: 700, color: "var(--text-secondary)", flexShrink: 0 }}>
                        {item.label})
                      </span>
                      <span style={{ flex: 1 }}>{item.text}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Answer table */}
              <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                Запишите в ответ цифры, расположив их в порядке, соответствующем буквам:
              </div>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
                {tc.matching_left.map((item: any, j: number) => (
                  <div key={j} style={{ textAlign: "center" }}>
                    <div style={{ fontWeight: 700, fontSize: "0.9rem", marginBottom: "0.25rem", color: "var(--primary)" }}>
                      {item.label}
                    </div>
                    <div style={{ display: "flex", gap: "0.25rem" }}>
                      {Array.from({ length: answersPerStem }).map((_, si) => (
                        <select
                          key={si}
                          value={matchingParts[j]?.[si] || ""}
                          onChange={(e) => {
                            const current = matchingParts[j] || "";
                            const chars = current.split("");
                            chars[si] = e.target.value;
                            handleMatchingAnswer(currentTask.task_id, j, chars.join(""));
                          }}
                          style={{
                            width: 48,
                            padding: "0.35rem",
                            border: "1px solid var(--border)",
                            borderRadius: "var(--radius)",
                            fontSize: "0.85rem",
                            textAlign: "center",
                          }}
                        >
                          <option value="">-</option>
                          {tc.matching_right.map((r: any) => (
                            <option key={r.label} value={r.label}>{r.label}</option>
                          ))}
                        </select>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Answer preview */}
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>Ответ:</span>
                <input
                  type="text"
                  value={answers[currentTask.task_id] || ""}
                  onChange={(e) => handleChange(currentTask.task_id, e.target.value)}
                  style={{
                    flex: 1,
                    padding: "0.4rem 0.75rem",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius)",
                    fontSize: "0.9rem",
                  }}
                  placeholder="Например: 3142"
                />
              </div>
            </div>
          ) : isSequence ? (
            /* Sequence task: numbered list + single input */
            <div>
              <div style={{ marginBottom: "1rem" }}>
                {tc.sequence_items.map((item: any, j: number) => (
                  <div
                    key={j}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "0.5rem",
                      padding: "0.5rem 0",
                      borderBottom: "1px solid var(--border)",
                      fontSize: "0.9rem",
                      lineHeight: 1.5,
                    }}
                  >
                    <span style={{ fontWeight: 700, color: "var(--text-secondary)", flexShrink: 0 }}>
                      {item.position})
                    </span>
                    <span style={{ flex: 1 }}>{item.text}</span>
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>Ответ:</span>
                <input
                  type="text"
                  value={answers[currentTask.task_id] || ""}
                  onChange={(e) => handleChange(currentTask.task_id, e.target.value)}
                  style={{
                    flex: 1,
                    padding: "0.4rem 0.75rem",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius)",
                    fontSize: "0.9rem",
                  }}
                  placeholder="Например: 213"
                />
              </div>
            </div>
          ) : (
            /* Default: short_answer or essay */
            <div>
              {(() => {
                const opts = tc?.options;
                if (opts && Array.isArray(opts) && opts.length > 0) {
                  const flatOpts = Array.isArray(opts[0]) ? opts[0] : opts;
                  return (
                    <div style={{ marginBottom: "1rem" }}>
                      {flatOpts.map((opt: string, i: number) => (
                        <label key={i} style={{ display: "block", padding: "0.5rem", cursor: "pointer", borderBottom: "1px solid var(--border)" }}>
                          <input
                            type="radio"
                            name={`task-${currentTask.task_id}`}
                            value={String(i + 1)}
                            checked={answers[currentTask.task_id] === String(i + 1)}
                            onChange={(e) => handleChange(currentTask.task_id, e.target.value)}
                          />
                          <span style={{ marginLeft: "0.5rem" }}>{opt}</span>
                        </label>
                      ))}
                    </div>
                  );
                }
                return (
                  <textarea
                    style={{ width: "100%", minHeight: 150, padding: "0.75rem", border: "1px solid var(--border)", borderRadius: "var(--radius)", fontSize: "0.9rem" }}
                    value={answers[currentTask.task_id] || ""}
                    onChange={(e) => handleChange(currentTask.task_id, e.target.value)}
                    placeholder="Введите ответ..."
                  />
                );
              })()}
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "1rem" }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>Ответ:</span>
                <input
                  type="text"
                  value={answers[currentTask.task_id] || ""}
                  onChange={(e) => handleChange(currentTask.task_id, e.target.value)}
                  style={{
                    flex: 1,
                    padding: "0.4rem 0.75rem",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius)",
                    fontSize: "0.9rem",
                  }}
                  placeholder="Введите ответ"
                />
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "1rem" }}>
          <button
            className="btn"
            style={{ background: "var(--border)" }}
            disabled={currentIdx === 0}
            onClick={() => setCurrentIdx((i) => i - 1)}
          >
            Назад
          </button>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            {currentIdx < tasks.length - 1 && (
              <button className="btn btn-primary" onClick={() => setCurrentIdx((i) => i + 1)}>
                Далее
              </button>
            )}
            {currentIdx === tasks.length - 1 && (
              <button className="btn btn-success" onClick={handleSubmit}>
                Завершить и отправить
              </button>
            )}
          </div>
        </div>

        {/* Task navigation grid */}
        <div style={{ display: "flex", gap: "0.25rem", marginTop: "1.5rem", flexWrap: "wrap" }}>
          {tasks.map((t, i) => (
            <button
              key={t.task_id}
              style={{
                width: 32,
                height: 32,
                borderRadius: "var(--radius)",
                border: "1px solid var(--border)",
                background: i === currentIdx ? "var(--primary)" : answers[t.task_id] ? "#dcfce7" : "var(--surface)",
                color: i === currentIdx ? "white" : "var(--text)",
                cursor: "pointer",
                fontSize: "0.75rem",
              }}
              onClick={() => setCurrentIdx(i)}
            >
              {i + 1}
            </button>
          ))}
        </div>
      </main>
    </>
  );
}
