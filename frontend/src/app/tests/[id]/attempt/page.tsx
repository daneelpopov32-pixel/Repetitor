"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { slideUp } from "@/lib/motion";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import Spinner from "@/components/ui/Spinner";

export default function AttemptPage() {
  const { id: attemptId } = useParams();
  const { auth, hydrated } = useAuth();
  const router = useRouter();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [tasks, setTasks] = useState<any[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [remaining, setRemaining] = useState<number | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [attempt, setAttempt] = useState<any>(null);
  const [submitted, setSubmitted] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null);
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "error">("saved");
  const [showInfo, setShowInfo] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);
  const debounceRef = useRef<NodeJS.Timeout>(null);
  const timerRef = useRef<NodeJS.Timeout>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token) { router.replace("/auth/login"); return; }
    loadData();
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [auth.token, hydrated, attemptId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape" && lightboxSrc) setLightboxSrc(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [lightboxSrc]);

  const loadData = async () => {
    try {
      const att = await api.getAttempt(attemptId as string, auth.token!);
      setAttempt(att);
      if (att.status !== "IN_PROGRESS") { setSubmitted(true); return; }
      const taskData = await api.getAttemptTasks(attemptId as string, auth.token!);
      setTasks(taskData.tasks || []);
      const ea: Record<string, string> = {};
      for (const t of taskData.tasks || []) { if (t.student_input) ea[t.task_id] = t.student_input; }
      setAnswers(ea);
      if (att.time_limit_minutes && att.started_at) {
        const left = Math.max(0, Math.floor(((new Date(att.server_time).getTime() - new Date(att.started_at).getTime()) * -1 + att.time_limit_minutes * 60000) / 1000));
        if (left <= 0) { setSubmitted(true); return; }
        setRemaining(left);
        timerRef.current = setInterval(() => { setRemaining((p) => { if (p === null || p <= 1) { clearInterval(timerRef.current!); setSubmitted(true); return 0; } return p - 1; }); }, 1000);
      }
    } catch {}
  };

  const saveAnswer = useCallback(async (taskId: string, value: string) => {
    setSaveStatus("saving");
    try { await api.saveAnswer(attemptId as string, taskId, value, auth.token!); setSaveStatus("saved"); } catch { setSaveStatus("error"); }
  }, [attemptId, auth.token]);

  const handleChange = (taskId: string, value: string) => {
    setAnswers((p) => ({ ...p, [taskId]: value }));
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => saveAnswer(taskId, value), 1000);
  };

  const handleGridInput = (taskId: string, index: number, value: string, max: number) => {
    if (value && !/^[1-9]$/.test(value)) return;
    setAnswers((p) => { const c = (p[taskId] || "").split(""); c[index] = value; return { ...p, [taskId]: c.join("").slice(0, max + 1) }; });
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => { const c = (answers[taskId] || "").split(""); c[index] = value; saveAnswer(taskId, c.join("").slice(0, max + 1)); }, 1000);
    if (value) { const next = document.querySelector(`[data-task="${taskId}"][data-index="${index + 1}"]`) as HTMLInputElement; if (next) next.focus(); }
  };

  const handleSubmit = async () => {
    if (!confirm("Завершить тест?")) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    for (const [tid, val] of Object.entries(answers)) await saveAnswer(tid, val);
    try { const res = await api.submitAttempt(attemptId as string, auth.token!); setResult(res); setSubmitted(true); if (timerRef.current) clearInterval(timerRef.current); } catch {}
  };

  const fmt = (s: number) => `${Math.floor(s / 3600).toString().padStart(2, "0")}:${Math.floor((s % 3600) / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getText = (t: any): string => { const tc = t.text_content; return typeof tc === "object" && tc?.text ? tc.text : tc || ""; };

  // Extract FIPI column names (uppercase labels) from instruction text
  // e.g. "ПАМЯТНИКИ КУЛЬТУРЫ ХАРАКТЕРИСТИКИ" → left="ПАМЯТНИКИ КУЛЬТУРЫ", right="ХАРАКТЕРИСТИКИ"
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getFipiHeaders = (t: any): { left: string; right: string } | null => {
    const text = getText(t);
    const tc = t.text_content;
    if (!tc?.matching_left) return null;
    const lines = text.split("\n");
    const inst: string[] = [];
    for (const l of lines) {
      const tr = l.trim();
      if (!tr) continue;
      if (/^[А-Я]\)/.test(tr)) break;
      inst.push(tr);
    }
    const joined = inst.join(" ");
    // Match trailing uppercase words (FIPI column labels)
    const m = joined.match(/([А-ЯЁ][А-ЯЁ\s,]+)\s+([А-ЯЁ]+)\s*$/);
    if (!m) return null;
    return { left: m[1].trim(), right: m[2].trim() };
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getInstruction = (t: any): string => { const text = getText(t); const tc = t.text_content; const lines = text.split("\n"); const inst: string[] = []; for (const l of lines) { const tr = l.trim(); if (!tr) continue; if (tc?.matching_left?.length && /^[А-Я]\)/.test(tr)) break; if (tc?.sequence_items?.length && /^\d+\)/.test(tr)) break; inst.push(tr); } const joined = inst.join("\n") || text; return joined.trim(); };

  // Read source text directly from text_content.source_text
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getSourceText = (t: any): string => {
    const tc = t.text_content;
    return (typeof tc === "object" && tc?.source_text) || "";
  };

  if (submitted && result) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--c-bg)" }}>
      <motion.div className="card" style={{ textAlign: "center", maxWidth: 400, width: "100%" }} {...slideUp}>
        <div style={{ fontSize: 48, marginBottom: "1rem" }}>🎉</div>
        <h1 style={{ fontSize: "var(--text-2xl)", fontWeight: 700, marginBottom: "1rem" }}>Тест завершён!</h1>
        <Badge variant="accent" style={{ marginBottom: "0.75rem" }}>{result.status}</Badge>
        <p style={{ fontSize: "var(--text-2xl)", fontWeight: 700, marginBottom: "0.5rem" }}>{result.auto_score} / {result.max_auto_score}</p>
        {result.pending_essay_count > 0 && <p style={{ color: "var(--c-text-secondary)", fontSize: "var(--text-sm)" }}>{result.pending_essay_count} заданий ожидают проверки</p>}
        <Button variant="accent" onClick={() => router.push("/dashboard")} style={{ marginTop: "1.5rem" }}>На главную</Button>
      </motion.div>
    </div>
  );

  if (submitted) return <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}><p style={{ color: "var(--c-text-secondary)" }}>Время истекло. Тест завершён.</p></div>;
  if (tasks.length === 0) return <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}><Spinner size="lg" /></div>;

  const task = tasks[currentIdx];
  const tc = task.text_content;
  const source = getSourceText(task);
  const isMatching = tc?.matching_left && tc?.matching_right;
  const isSequence = tc?.sequence_items;
  const answer = answers[task.task_id] || "";
  const timerClass = remaining !== null && remaining < 60 ? "timer-critical" : remaining !== null && remaining < 300 ? "timer-warning" : "timer-normal";
  const fipiHeaders = getFipiHeaders(task);

  return (
    <div style={{ minHeight: "100vh", background: "var(--c-bg)" }}>
      {/* Top bar — calm timer as pill */}
      <div style={{ position: "sticky", top: 0, zIndex: 30, background: "var(--c-surface)", borderBottom: "1px solid var(--c-border)", padding: "0.625rem 1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontWeight: 600, fontSize: "var(--text-base)" }}>{attempt?.test_title || "Тест"}</span>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {remaining !== null && (
            <span className={`timer-pill ${timerClass}`}>
              ⏱ {fmt(remaining)}
            </span>
          )}
          <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
            <span className={`autosave-dot ${saveStatus === "saving" ? "autosave-saving" : ""}`} title={saveStatus === "saved" ? "Сохранено" : saveStatus === "saving" ? "Сохранение..." : "Ошибка"} />
            <Button variant="accent" size="sm" onClick={handleSubmit}>Завершить</Button>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 800, margin: "0 auto", padding: "1.5rem" }}>
        {/* Nav */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <Button variant="ghost" size="sm" disabled={currentIdx === 0} onClick={() => setCurrentIdx((i) => i - 1)}>← Назад</Button>
          <span style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>{currentIdx + 1} / {tasks.length}</span>
          <Button variant="ghost" size="sm" disabled={currentIdx === tasks.length - 1} onClick={() => setCurrentIdx((i) => i + 1)}>Вперёд →</Button>
        </div>

        {/* Task */}
        <motion.div key={task.task_id} {...slideUp}>
          <div className="card">
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
              <Badge variant="accent">Тип {task.exam_position || "?"}</Badge>
              <Badge variant={task.type === "TEST" ? "default" : "warning"}>{task.type}</Badge>
              <Button variant="ghost" size="sm" onClick={() => setShowInfo(true)}>ℹ</Button>
            </div>

            {/* Source Card — inherited source text */}
            {source && (
              <div className="source-card">
                <div className="source-card-label">Источник</div>
                <div className="source-card-text">{source}</div>
              </div>
            )}

            {/* Images */}
            {tc?.images?.filter((p: string) => p != null && p.length > 0).length > 0 && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "0.75rem", margin: "1rem 0" }}>
                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                {tc.images.filter((p: any) => p != null && p.length > 0).map((imgPath: string, i: number) => (
                  <div key={i} style={{ cursor: "pointer" }} onClick={() => setLightboxSrc(`/api/v1/media/images/${imgPath.split("/").pop()}`)}>
                    <img src={`/api/v1/media/images/${imgPath.split("/").pop()}`} alt={`${i + 1}`} style={{ width: "100%", display: "block", borderRadius: "var(--r-md)", border: "1px solid var(--c-border)" }} onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                  </div>
                ))}
              </div>
            )}

            {/* Instruction — larger text for exam readability */}
            <p style={{ fontSize: "var(--text-lg)", lineHeight: 1.7, marginBottom: "1rem", fontWeight: 500, whiteSpace: "pre-wrap" }}>{getInstruction(task)}</p>

            {/* Matching content */}
            {isMatching && (
              <div className="matching-grid">
                <div>
                  <div className="matching-col-header">{fipiHeaders?.left || "Левый столбец"}</div>
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {tc.matching_left.map((item: any, j: number) => <div key={j} className="matching-item">{item.label}) {item.text}</div>)}
                </div>
                <div>
                  <div className="matching-col-header">{fipiHeaders?.right || "Правый столбец"}</div>
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {tc.matching_right.map((item: any, j: number) => <div key={j} className="matching-item">{item.label}) {item.text}</div>)}
                </div>
              </div>
            )}

            {/* Sequence content */}
            {isSequence && (
              <ol style={{ paddingLeft: "1.25rem", marginBottom: "1.5rem" }}>
                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                {tc.sequence_items.map((item: any, j: number) => <li key={j} style={{ fontSize: "var(--text-sm)", marginBottom: 4 }}>{item.text}</li>)}
              </ol>
            )}

            {/* Default content — options as clickable radio/checkbox */}
            {!isMatching && !isSequence && (() => {
              const opts = tc?.options;
              if (opts && Array.isArray(opts) && opts.length > 0) {
                const flat = Array.isArray(opts[0]) ? opts[0] : opts;
                const isMultiple = task.answer_type === "multiple_choice";
                const selectedIndices = isMultiple ? (answer.split(",").filter(Boolean).map(Number)) : (answer !== "" ? [parseInt(answer, 10)] : []);
                const handleOptionToggle = (idx: number) => {
                  if (isMultiple) {
                    const current = answer.split(",").filter(Boolean).map(Number);
                    const next = current.includes(idx) ? current.filter((x) => x !== idx) : [...current, idx];
                    next.sort((a, b) => a - b);
                    handleChange(task.task_id, next.join(","));
                  } else {
                    handleChange(task.task_id, String(idx));
                  }
                };
                return (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginBottom: "1rem" }}>
                    {flat.map((opt: string, i: number) => {
                      const isSelected = selectedIndices.includes(i);
                      return (
                        <label key={i} style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.625rem 0.875rem", borderRadius: "var(--r-md)", cursor: "pointer", border: `1.5px solid ${isSelected ? "var(--c-accent)" : "var(--c-border)"}`, background: isSelected ? "color-mix(in srgb, var(--c-accent) 8%, transparent)" : "var(--c-bg)", transition: "all 0.15s" }} onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.borderColor = "var(--c-text-secondary)"; }} onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.borderColor = "var(--c-border)"; }}>
                          <input type={isMultiple ? "checkbox" : "radio"} name={`task-${task.task_id}`} checked={isSelected} onChange={() => handleOptionToggle(i)} style={{ accentColor: "var(--c-accent)", width: 16, height: 16 }} />
                          <span style={{ fontSize: "var(--text-sm)", fontWeight: 500, minWidth: 24, color: "var(--c-text-secondary)" }}>{String.fromCharCode(65 + i)})</span>
                          <span style={{ fontSize: "var(--text-sm)" }}>{opt}</span>
                        </label>
                      );
                    })}
                  </div>
                );
              }
              return null;
            })()}

            {/* Answer grid for matching */}
            {isMatching && (
              <div style={{ marginTop: "1rem" }}>
                <p style={{ fontSize: "var(--text-sm)", marginBottom: "0.5rem" }}>Запишите цифры в порядке букв:</p>
                <div className="matching-answer-grid-wrap">
                  <table className="matching-answer-grid">
                    <thead>
                      <tr>
                        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                        {tc.matching_left.map((item: any, j: number) => <th key={j}>{item.label}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                        {tc.matching_left.map((item: any, j: number) => <td key={j}><input type="text" maxLength={1} data-task={task.task_id} data-index={j} value={answer[j] || ""} onChange={(e) => handleGridInput(task.task_id, j, e.target.value, tc.matching_left.length - 1)} /></td>)}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Free text input for tasks without options */}
            {!isMatching && !isSequence && (() => {
              const opts = tc?.options;
              if (opts && Array.isArray(opts) && opts.length > 0) return null;
              return (
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginTop: "1rem" }}>
                  <span style={{ fontWeight: 600, fontSize: "var(--text-sm)" }}>Ответ:</span>
                  <input type="text" value={answer} onChange={(e) => handleChange(task.task_id, e.target.value)} placeholder="Введите ответ" style={{ flex: 1, maxWidth: 400, padding: "0.5rem 0.75rem", border: "1px solid var(--c-border)", borderRadius: "var(--r-md)", fontSize: "var(--text-base)" }} />
                </div>
              );
            })()}
          </div>
        </motion.div>

        {/* Bottom nav */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1rem" }}>
          <Button variant="ghost" size="sm" disabled={currentIdx === 0} onClick={() => setCurrentIdx((i) => i - 1)}>← Назад</Button>
          <span style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>{currentIdx + 1} / {tasks.length}</span>
          <Button variant="ghost" size="sm" disabled={currentIdx === tasks.length - 1} onClick={() => setCurrentIdx((i) => i + 1)}>Вперёд →</Button>
        </div>
      </div>

      <Modal open={showInfo} onClose={() => setShowInfo(false)} title="Информация о задании">
        <p style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>Тема: {task.theme_name || task.theme_id}</p>
        <p style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>Тип: {task.exam_position ? `Тип ${task.exam_position}` : "—"}{task.difficulty_level ? ` (${task.difficulty_level})` : ""}</p>
      </Modal>

      {/* Image lightbox */}
      {lightboxSrc && (
        <div onClick={() => setLightboxSrc(null)} style={{ position: "fixed", inset: 0, zIndex: 100, background: "rgba(0,0,0,0.85)", display: "flex", alignItems: "center", justifyContent: "center", cursor: "zoom-out", padding: "2rem" }}>
          <img src={lightboxSrc} style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain", borderRadius: "var(--r-md)" }} />
        </div>
      )}
    </div>
  );
}
