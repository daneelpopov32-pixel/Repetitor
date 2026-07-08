"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import { slideUp, stagger } from "@/lib/motion";
import Sidebar from "@/components/layout/Sidebar";
import PageWrapper from "@/components/layout/PageWrapper";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ProgressBar from "@/components/ui/ProgressBar";
import EmptyState from "@/components/ui/EmptyState";
import Spinner from "@/components/ui/Spinner";

const STATUS: Record<string, { label: string; variant: "default" | "success" | "warning" | "info" }> = {
  ASSIGNED: { label: "Назначен", variant: "info" },
  VIEWED: { label: "Просмотрен", variant: "warning" },
  IN_PROGRESS: { label: "В работе", variant: "warning" },
  COMPLETED: { label: "Выполнен", variant: "success" },
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default function TestsPage() {
  const { auth, hydrated } = useAuth();
  const router = useRouter();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [tests, setTests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [expandedTest, setExpandedTest] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [assignments, setAssignments] = useState<Record<string, any[]>>({});
  // Assign modal
  const [assignTestId, setAssignTestId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [students, setStudents] = useState<any[]>([]);
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);
  // Answers modal
  const [answersTestId, setAnswersTestId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [answers, setAnswers] = useState<any>(null);
  const [answersStudent, setAnswersStudent] = useState("");
  // Delete
  const [deleteId, setDeleteId] = useState<string | null>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token || auth.role !== "TUTOR") { router.replace("/auth/login"); return; }
    loadTests();
  }, [auth.token, hydrated]);

  const loadTests = useCallback(async () => {
    if (!auth.token) return;
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      const data = await api.getTests(params, auth.token);
      setTests(data || []);
    } catch {}
    setLoading(false);
  }, [auth.token, search]);

  useEffect(() => { loadTests(); }, [loadTests]);

  const loadAssignments = async (testId: string) => {
    if (!auth.token) return;
    try {
      const data = await api.getTest(testId, auth.token);
      setAssignments((prev) => ({ ...prev, [testId]: data.assignments || [] }));
    } catch {}
  };

  const toggleExpand = (id: string) => {
    if (expandedTest === id) { setExpandedTest(null); return; }
    setExpandedTest(id);
    if (!assignments[id]) loadAssignments(id);
  };

  const openAssign = async (testId: string) => {
    setAssignTestId(testId);
    setSelectedStudents([]);
    if (!students.length && auth.token) {
      try { const data = await api.getTutorStudents(auth.token); setStudents(data || []); } catch {}
    }
  };

  const doAssign = async () => {
    if (!assignTestId || !auth.token || !selectedStudents.length) return;
    try {
      await api.assignTestToStudents(assignTestId, selectedStudents, auth.token);
      setAssignTestId(null);
      loadAssignments(assignTestId);
    } catch {}
  };

  const doDelete = async () => {
    if (!deleteId || !auth.token) return;
    try { await api.deleteTest(deleteId, auth.token); setDeleteId(null); loadTests(); } catch {}
  };

  const viewAnswers = async (testId: string, studentId: string, name: string) => {
    if (!auth.token) return;
    setAnswersTestId(testId);
    setAnswersStudent(name);
    try { const data = await api.getStudentAnswers(testId, studentId, auth.token); setAnswers(data); } catch {}
  };

  const doUnassign = async (testId: string, studentId: string) => {
    if (!auth.token) return;
    try { await api.unassignStudent(testId, studentId, auth.token); loadAssignments(testId); } catch {}
  };

  if (loading) return <div className="layout"><Sidebar /><div className="layout-content" style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><Spinner size="lg" /></div></div>;

  return (
    <div className="layout">
      <Sidebar />
      <PageWrapper
        title="Тесты"
        actions={<Button variant="accent" onClick={() => router.push("/tests/new")}>+ Создать тест</Button>}
      >
        <div style={{ marginBottom: "1rem" }}>
          <Input placeholder="Поиск по названию..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ maxWidth: 320 }} />
        </div>

        {tests.length === 0 ? (
          <EmptyState icon="📝" title="Нет тестов" text="Создайте первый тест из банка ФИПИ" action={<Button variant="accent" onClick={() => router.push("/tests/new")}>Создать тест</Button>} />
        ) : (
          <motion.div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }} {...stagger}>
            {tests.map((t, idx) => {
              const testId = t.test_id;
              const isExpanded = expandedTest === testId;
              const assigns = assignments[testId] || [];
              return (
                <motion.div key={String(testId || idx)} {...slideUp}>
                  <Card hover>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ flex: 1, cursor: "pointer" }} onClick={() => toggleExpand(testId)}>
                        <div style={{ fontWeight: 600, marginBottom: 2 }}>{t.title || "Без названия"}</div>
                        <div style={{ fontSize: "var(--text-xs)", color: "var(--c-text-secondary)" }}>
                          {t.tasks_count || 0} заданий{t.time_limit_minutes ? ` • ${t.time_limit_minutes} мин` : ""} • {new Date(t.created_at).toLocaleDateString("ru-RU")}
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: "0.5rem" }} onClick={(e) => e.stopPropagation()}>
                        <Button variant="secondary" size="sm" onClick={() => router.push(`/tests/${testId}`)}>Открыть</Button>
                        <Button variant="secondary" size="sm" onClick={() => openAssign(testId)}>Назначить</Button>
                        <Button variant="ghost" size="sm" onClick={() => setDeleteId(testId)}>🗑</Button>
                      </div>
                    </div>
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} style={{ overflow: "hidden" }}>
                          <div style={{ marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid var(--c-border)" }}>
                            {assigns.length === 0 ? (
                              <div style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>Нет назначенных учеников</div>
                            ) : (
                              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                                {assigns.map((a: Record<string, unknown>) => {
                                  const st = STATUS[a.status as string] || STATUS.ASSIGNED;
                                  const score = a.score as number | null;
                                  return (
                                    <div key={a.student_id as string} style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.5rem 0.75rem", background: "var(--c-bg)", borderRadius: "var(--r-md)" }}>
                                      <span style={{ flex: 1, fontSize: "var(--text-sm)" }}>{String(a.student_name || "Ученик")}</span>
                                      <Badge variant={st.variant}>{st.label}</Badge>
                                      {score !== null && score !== undefined && <span style={{ fontWeight: 600, fontSize: "var(--text-sm)" }}>{score}%</span>}
                                      <div style={{ width: 80 }}><ProgressBar value={score || 0} /></div>
                      <Button variant="ghost" size="sm" onClick={() => viewAnswers(testId, a.student_id as string, a.student_name as string)}>Ответы</Button>
                                       <Button variant="ghost" size="sm" onClick={() => doUnassign(testId, a.student_id as string)}>✕</Button>
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </PageWrapper>

      {/* Assign Modal */}
      <Modal open={!!assignTestId} onClose={() => setAssignTestId(null)} title="Назначить тест" footer={<><Button variant="secondary" onClick={() => setAssignTestId(null)}>Отмена</Button><Button variant="accent" onClick={doAssign}>Назначить</Button></>}>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: 300, overflowY: "auto" }}>
          {students.map((s) => (
            <label key={s.id} style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem", borderRadius: "var(--r-md)", cursor: "pointer" }}
              onMouseEnter={(e) => e.currentTarget.style.background = "var(--c-hover)"}
              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
            >
              <input type="checkbox" checked={selectedStudents.includes(s.id)} onChange={(e) => setSelectedStudents((prev) => e.target.checked ? [...prev, s.id] : prev.filter((id) => id !== s.id))} />
              <span style={{ fontSize: "var(--text-sm)" }}>{s.first_name} {s.last_name}</span>
            </label>
          ))}
        </div>
      </Modal>

      {/* Answers Modal */}
      <Modal open={!!answersTestId} onClose={() => { setAnswersTestId(null); setAnswers(null); }} title={`Ответы: ${answersStudent}`} maxWidth="600px">
        {answers ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {(answers.answers || []).map((a: any, i: number) => (
              <div key={i} style={{ padding: "0.75rem", background: "var(--c-bg)", borderRadius: "var(--r-md)" }}>
                <div style={{ fontSize: "var(--text-xs)", color: "var(--c-text-secondary)", marginBottom: 4 }}>Задание {i + 1}</div>
                <div style={{ fontSize: "var(--text-sm)" }}>{a.student_input || <em>Нет ответа</em>}</div>
                {a.auto_score !== null && <Badge variant={a.auto_score > 0 ? "success" : "danger"} style={{ marginTop: 4 }}>{a.auto_score} б.</Badge>}
              </div>
            ))}
          </div>
        ) : <Spinner />}
      </Modal>

      {/* Delete Confirm */}
      <Modal open={!!deleteId} onClose={() => setDeleteId(null)} title="Удалить тест" footer={<><Button variant="secondary" onClick={() => setDeleteId(null)}>Отмена</Button><Button variant="danger" onClick={doDelete}>Удалить</Button></>}>
        <p style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>Вы уверены? Это действие необратимо.</p>
      </Modal>
    </div>
  );
}
