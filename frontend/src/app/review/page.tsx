"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { motion } from "framer-motion";
import { slideUp, stagger } from "@/lib/motion";
import Sidebar from "@/components/layout/Sidebar";
import PageWrapper from "@/components/layout/PageWrapper";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default function ReviewPage() {
  const { auth, hydrated } = useAuth();
  const router = useRouter();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [queue, setQueue] = useState<any[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [selected, setSelected] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [aiResult, setAiResult] = useState<any>(null);
  const [scores, setScores] = useState<Record<string, number>>({});
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token || auth.role !== "TUTOR") { router.replace("/auth/login"); return; }
    api.getReviewQueue(auth.token).then(setQueue).catch(() => {});
  }, [auth.token, hydrated]);

  const requestAi = async (taskId: string, answer: string) => {
    setLoading(true);
    try { const res = await api.aiCheck(taskId, answer, auth.token!); setAiResult(res); if (res.suggested_scores) setScores(res.suggested_scores); }
    catch { setAiResult({ ai_feedback: "AI временно недоступен", suggested_scores: {} }); }
    setLoading(false);
  };

  const submitGrade = async () => {
    if (!selected) return;
    try { await api.gradeAnswer(selected.answer_id, scores, comment, auth.token!); setSelected(null); setAiResult(null); setScores({}); setComment(""); api.getReviewQueue(auth.token!).then(setQueue); } catch {}
  };

  return (
    <div className="layout">
      <Sidebar />
      <PageWrapper title="Проверка ответов">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: "1rem", alignItems: "start" }}>
          {/* Queue */}
          <div>
            <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.75rem" }}>Очередь ({queue.length})</h3>
            {!queue.length ? (
              <EmptyState icon="✅" title="Пусто" text="Нет ответов на проверку" />
            ) : (
              <motion.div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }} {...stagger}>
                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                {queue.map((item: any) => (
                  <motion.div key={item.answer_id} {...slideUp}>
                    <Card
                      hover
                      onClick={() => { setSelected(item); setAiResult(null); setScores({}); setComment(""); }}
                      style={{ border: selected?.answer_id === item.answer_id ? "2px solid var(--c-accent)" : undefined, cursor: "pointer" }}
                    >
                      <div style={{ fontSize: "var(--text-xs)", color: "var(--c-text-secondary)", marginBottom: 4 }}>Попытка: {item.attempt_id.slice(0, 8)}...</div>
                      <div style={{ fontSize: "var(--text-sm)" }}>{item.student_input?.slice(0, 120)}...</div>
                    </Card>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </div>

          {/* Detail */}
          <div>
            {selected ? (
              <motion.div {...slideUp} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                <Card>
                  <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.5rem" }}>Ответ ученика</h3>
                  <p style={{ fontSize: "var(--text-sm)", lineHeight: 1.6 }}>{selected.student_input}</p>
                </Card>

                <Button variant="accent" onClick={() => requestAi(selected.task_id, selected.student_input)} loading={loading}>
                  {loading ? "AI анализирует..." : "Запросить AI-подсказку"}
                </Button>

                {aiResult && (
                  <Card style={{ background: "var(--c-info-bg)" }}>
                    <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.5rem" }}>AI-подсказка</h3>
                    <p style={{ fontSize: "var(--text-sm)", whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{aiResult.ai_feedback}</p>
                    {Object.keys(aiResult.suggested_scores || {}).length > 0 && (
                      <div style={{ marginTop: "0.75rem" }}>
                        <div style={{ fontSize: "var(--text-sm)", fontWeight: 600, marginBottom: 4 }}>Предложенные баллы:</div>
                        {Object.entries(aiResult.suggested_scores as Record<string, number>).map(([k, v]) => (
                          <div key={k} style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>{k}: {String(v)}</div>
                        ))}
                      </div>
                    )}
                  </Card>
                )}

                <Card>
                  <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.75rem" }}>Выставление баллов</h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                    {Object.keys(scores).map((k) => (
                      <div key={k} style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                        <span style={{ flex: 1, fontSize: "var(--text-sm)" }}>{k}</span>
                        <input type="number" min="0" max="10" style={{ width: 80, padding: "0.375rem 0.5rem", border: "1px solid var(--c-border)", borderRadius: "var(--r-md)", fontSize: "var(--text-sm)", textAlign: "center" }} value={scores[k]} onChange={(e) => setScores({ ...scores, [k]: parseInt(e.target.value) || 0 })} />
                      </div>
                    ))}
                  </div>
                  <div style={{ marginTop: "1rem" }}>
                    <label style={{ fontSize: "var(--text-sm)", fontWeight: 500, display: "block", marginBottom: 4 }}>Комментарий</label>
                    <textarea style={{ width: "100%", minHeight: 80, padding: "0.5rem", border: "1px solid var(--c-border)", borderRadius: "var(--r-md)", fontFamily: "var(--font)", fontSize: "var(--text-sm)", resize: "vertical" }} value={comment} onChange={(e) => setComment(e.target.value)} />
                  </div>
                  <Button variant="accent" onClick={submitGrade} style={{ marginTop: "1rem" }}>Сохранить оценку</Button>
                </Card>
              </motion.div>
            ) : (
              <EmptyState icon="📝" title="Выберите ответ" text="Кликните на ответ из очереди слева" />
            )}
          </div>
        </div>
      </PageWrapper>
    </div>
  );
}
