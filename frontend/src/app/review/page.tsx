"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function ReviewPage() {
  const { auth, hydrated, logout } = useAuth();
  const router = useRouter();
  const [queue, setQueue] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [aiResult, setAiResult] = useState<any>(null);
  const [scores, setScores] = useState<Record<string, number>>({});
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token || auth.role !== "TUTOR") {
      router.replace("/auth/login");
      return;
    }
    loadQueue();
  }, [auth.token, hydrated]);

  const loadQueue = async () => {
    try {
      const data = await api.getReviewQueue(auth.token!);
      setQueue(data);
    } catch {}
  };

  const requestAi = async (taskId: string, answer: string) => {
    setLoading(true);
    try {
      const res = await api.aiCheck(taskId, answer, auth.token!);
      setAiResult(res);
      if (res.suggested_scores) {
        setScores(res.suggested_scores);
      }
    } catch {
      setAiResult({ ai_feedback: "AI временно недоступен", suggested_scores: {} });
    }
    setLoading(false);
  };

  const submitGrade = async () => {
    if (!selected) return;
    try {
      await api.gradeAnswer(selected.id, scores, comment, auth.token!);
      setSelected(null);
      setAiResult(null);
      setScores({});
      setComment("");
      loadQueue();
    } catch {}
  };

  return (
    <>
      <header className="header">
        <h1>Проверка ответов</h1>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <button className="btn btn-primary" onClick={() => router.push("/dashboard")}>
            Дашборд
          </button>
          <button className="btn btn-danger" onClick={logout}>Выйти</button>
        </div>
      </header>
      <main className="container" style={{ padding: "2rem" }}>
        <div className="grid grid-2">
          <div>
            <h2 style={{ marginBottom: "1rem" }}>Очередь на проверке ({queue.length})</h2>
            {!queue.length ? (
              <div className="empty-state">Нет ответов на проверке</div>
            ) : (
              queue.map((item) => (
                <div
                  key={item.answer_id}
                  className="card"
                  style={{ cursor: "pointer", border: selected?.answer_id === item.answer_id ? "2px solid var(--primary)" : undefined }}
                  onClick={() => {
                    setSelected(item);
                    setAiResult(null);
                    setScores({});
                    setComment("");
                  }}
                >
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Попытка: {item.attempt_id.slice(0, 8)}...
                  </div>
                  <div style={{ marginTop: "0.5rem", fontSize: "0.875rem" }}>
                    {item.student_input?.slice(0, 150)}...
                  </div>
                </div>
              ))
            )}
          </div>
          <div>
            {selected ? (
              <div>
                <div className="card">
                  <h3>Ответ ученика</h3>
                  <p style={{ marginTop: "0.5rem" }}>{selected.student_input}</p>
                </div>
                <button
                  className="btn btn-primary"
                  style={{ marginTop: "1rem", marginBottom: "1rem" }}
                  onClick={() => requestAi(selected.task_id, selected.student_input)}
                  disabled={loading}
                >
                  {loading ? "AI анализирует..." : "Запросить AI-подсказку"}
                </button>
                {aiResult && (
                  <div className="card" style={{ background: "#f0f9ff" }}>
                    <h3>AI-подсказка</h3>
                    <p style={{ marginTop: "0.5rem", whiteSpace: "pre-wrap" }}>{aiResult.ai_feedback}</p>
                    {Object.keys(aiResult.suggested_scores || {}).length > 0 && (
                      <div style={{ marginTop: "0.5rem" }}>
                        <strong>Предложенные баллы:</strong>
                        {Object.entries(aiResult.suggested_scores as Record<string, number>).map(([k, v]) => (
                          <div key={k} style={{ fontSize: "0.875rem" }}>
                            {k}: {String(v)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                <div className="card" style={{ marginTop: "1rem" }}>
                  <h3>Выставление баллов</h3>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                    Вручную проставьте баллы по каждому критерию
                  </p>
                  {Object.keys(scores).map((k) => (
                    <div key={k} className="form-group" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <label style={{ flex: 1 }}>{k}</label>
                      <input
                        type="number"
                        min="0"
                        max="10"
                        style={{ width: 80 }}
                        value={scores[k]}
                        onChange={(e) => setScores({ ...scores, [k]: parseInt(e.target.value) || 0 })}
                      />
                    </div>
                  ))}
                  <div className="form-group">
                    <label>Комментарий</label>
                    <textarea
                      style={{ width: "100%", minHeight: 80, padding: "0.5rem", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                    />
                  </div>
                  <button className="btn btn-success" onClick={submitGrade}>
                    Сохранить оценку
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty-state">Выберите ответ из очереди</div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
