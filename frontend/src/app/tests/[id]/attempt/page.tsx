"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

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
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "error">("saved");
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
      setSaveStatus("saving");
      try {
        await api.saveAnswer(attemptId as string, taskId, value, auth.token!);
        setSaveStatus("saved");
      } catch {
        setSaveStatus("error");
      }
    },
    [attemptId, auth.token]
  );

  const handleChange = (taskId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [taskId]: value }));
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => saveAnswer(taskId, value), 1000);
  };

  const handleGridInput = (taskId: string, index: number, value: string, maxIndex: number) => {
    if (value && !/^[1-9]$/.test(value)) return;
    setAnswers((prev) => {
      const current = prev[taskId] || "";
      const parts = current.split("");
      parts[index] = value;
      const newAnswer = parts.join("").slice(0, maxIndex + 1);
      return { ...prev, [taskId]: newAnswer };
    });
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const current = answers[taskId] || "";
      const parts = current.split("");
      parts[index] = value;
      saveAnswer(taskId, parts.join("").slice(0, maxIndex + 1));
    }, 1000);
    if (value) {
      const nextInput = document.querySelector(
        `[data-task="${taskId}"][data-index="${index + 1}"]`
      ) as HTMLInputElement;
      if (nextInput) nextInput.focus();
    }
  };

  const handleGridKeydown = (
    e: React.KeyboardEvent,
    taskId: string,
    index: number
  ) => {
    if (e.key === "Backspace") {
      const current = answers[taskId] || "";
      if (!current[index] && index > 0) {
        const prevInput = document.querySelector(
          `[data-task="${taskId}"][data-index="${index - 1}"]`
        ) as HTMLInputElement;
        if (prevInput) prevInput.focus();
      }
    }
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
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const getTaskText = (task: any): string => {
    const tc = task.text_content;
    if (typeof tc === "object" && tc !== null) return tc.text || "";
    return tc || "";
  };

  if (submitted && result) {
    return (
      <div className="test-screen">
        <div className="task-card" style={{ textAlign: "center" }}>
          <h1 style={{ marginBottom: "1rem" }}>Тест завершён!</h1>
          <p>Статус: <span className="badge badge-info">{result.status}</span></p>
          <p>Балл: <strong>{result.auto_score}</strong> / {result.max_auto_score}</p>
          {result.pending_essay_count > 0 && (
            <p style={{ color: "#666" }}>
              {result.pending_essay_count} задание(я) ожидают проверки
            </p>
          )}
          <button
            className="submit-button"
            style={{ marginTop: "1.5rem" }}
            onClick={() => router.push("/dashboard")}
          >
            На главную
          </button>
        </div>
      </div>
    );
  }

  if (submitted && !result) {
    return (
      <div className="test-screen">
        <div className="task-card" style={{ textAlign: "center" }}>
          Время истекло. Тест завершён.
        </div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="test-screen">
        <div className="task-card" style={{ textAlign: "center" }}>
          Загрузка заданий...
        </div>
      </div>
    );
  }

  const currentTask = tasks[currentIdx];
  const tc = currentTask.text_content;
  const taskText = getTaskText(currentTask);
  const isMatching = tc?.matching_left && tc?.matching_right;
  const isSequence = tc?.sequence_items;
  const answer = answers[currentTask.task_id] || "";

  // Extract column titles from text
  const getLeftTitle = () => {
    if (!isMatching) return "";
    const text = taskText;
    const match = text.match(/([А-Я]+(?:\s[А-Я]+)*)\s*\n\s*[А-Я]\)/m);
    if (match) return match[1];
    const possibleTitles = ["СОБЫТИЕ", "СОБЫТИЯ", "ПРОЦЕССЫ", "ФАКТЫ", "ГОД", "ГОДЫ",
      "УЧАСТНИКИ", "ФРАГМЕНТЫ ИСТОЧНИКОВ", "ХАРАКТЕРИСТИКИ", "ПАМЯТНИКИ КУЛЬТУРЫ",
      "ПРОИЗВЕДЕНИЯ КУЛЬТУРЫ", "НАЧАЛА СУЖДЕНИЙ"];
    for (const t of possibleTitles) {
      if (text.includes(t)) return t;
    }
    return "ЛЕВЫЙ СТОЛБЕЦ";
  };

  const getRightTitle = () => {
    if (!isMatching) return "";
    const text = taskText;
    const possibleTitles = ["ГОД", "ГОДЫ", "ФАКТЫ", "УЧАСТНИКИ", "ХАРАКТЕРИСТИКИ",
      "ВАРИАНТЫ ЗАВЕРШЕНИЯ", "ВАРИАНТЫ ЗАВЕРШЕНИЯ СУЖДЕНИЙ"];
    for (const t of possibleTitles) {
      if (text.includes(t)) return t;
    }
    return "ПРАВЫЙ СТОЛБЕЦ";
  };

  // Get instruction from text (first paragraph before column titles)
  const getInstruction = () => {
    const lines = taskText.split("\n");
    const instructionLines: string[] = [];
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      if (tc?.matching_left?.length && /^[А-Я]\)/.test(trimmed)) break;
      if (tc?.sequence_items?.length && /^\d+\)/.test(trimmed)) break;
      instructionLines.push(trimmed);
    }
    return instructionLines.join(" ") || taskText;
  };

  return (
    <div className="test-screen">
      {/* Test Header */}
      <div className="test-header">
        <div className="test-title">{attempt?.test_title || "Тест"}</div>
        {remaining !== null && (
          <div
            className={`timer ${remaining < 60 ? "critical" : remaining < 300 ? "warning" : ""}`}
          >
            {formatTime(remaining)}
          </div>
        )}
        <button className="submit-button" onClick={handleSubmit}>
          Завершить тест
        </button>
      </div>

      {/* Task Navigation */}
      <div className="task-navigation">
        <button
          className="nav-button"
          disabled={currentIdx === 0}
          onClick={() => setCurrentIdx((i) => i - 1)}
        >
          ← Предыдущее
        </button>
        <span className="task-counter">
          Задание {currentIdx + 1} из {tasks.length}
        </span>
        <button
          className="nav-button"
          disabled={currentIdx === tasks.length - 1}
          onClick={() => setCurrentIdx((i) => i + 1)}
        >
          Следующее →
        </button>
      </div>

      {/* Task Card */}
      <div className="task-container">
        <div className="task-card">
          {/* Task Header */}
          <div className="task-header">
            <span className="task-type-badge">
              Тип {currentTask.order_number || currentIdx + 1} № {currentTask.block_id || currentTask.task_id?.slice(0, 8)}
            </span>
            {currentTask.hint && (
              <span className="task-info-icon" title={currentTask.hint}>
                ℹ️
              </span>
            )}
          </div>

          {/* Instruction */}
          <div className="task-instruction">{getInstruction()}</div>

          {/* Content: Matching */}
          {isMatching && (
            <div className="task-content matching-layout">
              <div className="matching-columns">
                <div className="column left-column">
                  <div className="column-title">{getLeftTitle()}</div>
                  <div className="column-items">
                    {tc.matching_left.map((item: any, j: number) => (
                      <div key={j} className="item">
                        {item.label}) {item.text}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="column right-column">
                  <div className="column-title">{getRightTitle()}</div>
                  <div className="column-items">
                    {tc.matching_right.map((item: any, j: number) => (
                      <div key={j} className="item">
                        {item.label}) {item.text}
                      </div>
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
                  <li key={j} className="event-item">
                    {item.text}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Content: Default (short_answer/essay) */}
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
                return (
                  <textarea
                    style={{
                      width: "100%",
                      minHeight: 150,
                      padding: "12px",
                      border: "1px solid #ccc",
                      borderRadius: "4px",
                      fontSize: "14px",
                      fontFamily: "inherit",
                    }}
                    value={answer}
                    onChange={(e) => handleChange(currentTask.task_id, e.target.value)}
                    placeholder="Введите ответ..."
                  />
                );
              })()}
            </div>
          )}

          {/* Answer Section: Matching grid */}
          {isMatching && (
            <>
              <div className="answer-instruction">
                Запишите в ответ цифры, расположив их в порядке, соответствующем буквам:
              </div>
              <div className="answer-grid">
                <table className="answer-table">
                  <thead>
                    <tr>
                      {tc.matching_left.map((item: any, j: number) => (
                        <th key={j}>{item.label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      {tc.matching_left.map((item: any, j: number) => (
                        <td key={j}>
                          <input
                            type="text"
                            maxLength={1}
                            className="answer-input"
                            data-task={currentTask.task_id}
                            data-index={j}
                            value={answer[j] || ""}
                            onChange={(e) =>
                              handleGridInput(
                                currentTask.task_id,
                                j,
                                e.target.value,
                                tc.matching_left.length - 1
                              )
                            }
                            onKeyDown={(e) =>
                              handleGridKeydown(e, currentTask.task_id, j)
                            }
                          />
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
                <div className="watermark">ege.sdamgia.ru</div>
              </div>
            </>
          )}

          {/* Answer Section: Final answer */}
          <div className="final-answer">
            <label className="answer-label">Ответ:</label>
            <input
              type="text"
              className="final-answer-input"
              value={answer}
              onChange={(e) => handleChange(currentTask.task_id, e.target.value)}
              placeholder={
                isMatching
                  ? "Введите ответ"
                  : isSequence
                  ? "Введите последовательность цифр"
                  : "Введите ответ"
              }
            />
          </div>
        </div>
      </div>

      {/* Autosave Status */}
      <div className={`autosave-status ${saveStatus === "saving" ? "saving" : saveStatus === "error" ? "error" : ""}`}>
        <span className="status-icon">{saveStatus === "saved" ? "✓" : saveStatus === "saving" ? "⏳" : "✕"}</span>
        <span className="status-text">
          {saveStatus === "saved" ? "Сохранено" : saveStatus === "saving" ? "Сохранение..." : "Ошибка сохранения"}
        </span>
      </div>

      {/* Bottom Navigation */}
      <div className="task-navigation" style={{ marginTop: "16px" }}>
        <button
          className="nav-button"
          disabled={currentIdx === 0}
          onClick={() => setCurrentIdx((i) => i - 1)}
        >
          ← Предыдущее
        </button>
        <span className="task-counter">
          Задание {currentIdx + 1} из {tasks.length}
        </span>
        <button
          className="nav-button"
          disabled={currentIdx === tasks.length - 1}
          onClick={() => setCurrentIdx((i) => i + 1)}
        >
          Следующее →
        </button>
      </div>
    </div>
  );
}
