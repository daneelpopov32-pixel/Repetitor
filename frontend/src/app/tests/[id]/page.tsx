"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { slideUp, expand } from "@/lib/motion";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Sidebar from "@/components/layout/Sidebar";
import PageWrapper from "@/components/layout/PageWrapper";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import Spinner from "@/components/ui/Spinner";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const STATUS: Record<string, { label: string; variant: "default" | "success" | "warning" | "info" }> = {
  ASSIGNED: { label: "Назначен", variant: "info" },
  VIEWED: { label: "Просмотрен", variant: "warning" },
  IN_PROGRESS: { label: "В работе", variant: "warning" },
  COMPLETED: { label: "Выполнен", variant: "success" },
};

export default function TestDetailPage() {
  const { id: testId } = useParams();
  const { auth, hydrated } = useAuth();
  const router = useRouter();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [test, setTest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentIdx, setCurrentIdx] = useState(0);
  const [viewMode, setViewMode] = useState<"single" | "list">("list");
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [showInfo, setShowInfo] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token || auth.role !== "TUTOR") { router.replace("/auth/login"); return; }
    api.getTest(testId as string, auth.token).then(setTest).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [auth.token, hydrated, testId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape" && lightboxSrc) setLightboxSrc(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [lightboxSrc]);

  const deleteTest = async () => { if (!confirm("Удалить тест?")) return; try { await api.deleteTest(testId as string, auth.token!); router.push("/tests"); } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); } };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const removeTask = async (tid: string) => { if (!confirm("Удалить задание?")) return; try { await api.removeTaskFromTest(testId as string, tid, auth.token!); setTest((p: any) => ({ ...p, tasks: p.tasks.filter((t: any) => t.task_id !== tid) })); } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); } };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const replaceTask = async (tid: string, newType: string) => { if (!confirm("Заменить задание?")) return; try { await api.replaceTask(testId as string, tid, newType, auth.token!); api.getTest(testId as string, auth.token!).then(setTest); } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); } };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getText = (t: any): string => { const tc = t.text_content; return typeof tc === "object" && tc?.text ? tc.text : tc || ""; };

  // Extract FIPI column names (uppercase labels) from instruction text
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
    const m = joined.match(/([А-ЯЁ][А-ЯЁ\s,]+)\s+([А-ЯЁ]+)\s*$/);
    if (!m) return null;
    return { left: m[1].trim(), right: m[2].trim() };
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getInstruction = (t: any): string => { const text = getText(t); const tc = t.text_content; const lines = text.split("\n"); const inst: string[] = []; for (const l of lines) { const tr = l.trim(); if (!tr) continue; if (tc?.matching_left?.length && /^[А-Я]\)/.test(tr)) break; if (tc?.sequence_items?.length && /^\d+\)/.test(tr)) break; inst.push(tr); } const joined = inst.join(" ") || text; const stripped = joined.replace(/\s+[А-ЯЁ][А-ЯЁ\s,()]+[А-ЯЁ]+(?:\s+[А-ЯЁ][А-ЯЁ\s,()]+[А-ЯЁ]+)*$/g, "").trim(); return stripped || text; };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getShort = (t: any): string => { const text = getText(t); return text.length > 80 ? text.slice(0, 80) + "..." : text; };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderContent = (task: any, expanded: boolean) => {
    const tc = task.text_content;
    const fipiHeaders = getFipiHeaders(task);
    return (
      <div style={{ marginTop: expanded ? "0.75rem" : 0 }}>
        <div style={{ fontSize: "var(--text-sm)", lineHeight: 1.6, color: "var(--c-text)" }}>{expanded ? getInstruction(task) : getShort(task)}</div>
        {expanded && tc?.matching_left && (
          <div className="matching-grid" style={{ marginTop: "0.75rem" }}>
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
        {expanded && tc?.sequence_items && (
          <ol style={{ paddingLeft: "1.25rem", marginTop: "0.75rem" }}>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {tc.sequence_items.map((item: any, j: number) => <li key={j} style={{ fontSize: "var(--text-sm)", marginBottom: 4 }}>{item.text}</li>)}
          </ol>
        )}
      </div>
    );
  };

  if (loading) return <div className="layout"><Sidebar /><div className="layout-content" style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><Spinner size="lg" /></div></div>;
  if (!test) return <div className="layout"><Sidebar /><PageWrapper title="Тест не найден"><Button onClick={() => router.push("/tests")}>К списку тестов</Button></PageWrapper></div>;

  const currentTask = test.tasks?.[currentIdx];

  return (
    <div className="layout">
      <Sidebar />
      <PageWrapper
        title={test.title || "Тест"}
        actions={
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <span style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>{test.tasks?.length || 0} заданий{test.time_limit_minutes ? ` • ${test.time_limit_minutes} мин` : ""}</span>
            <Button variant="danger" size="sm" onClick={deleteTest}>Удалить</Button>
          </div>
        }
      >
        {error && <div style={{ padding: "0.75rem 1rem", background: "var(--c-danger-bg)", borderRadius: "var(--r-md)", color: "var(--c-danger)", marginBottom: "1rem" }}>{error} <button onClick={() => setError("")} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button></div>}

        {/* Assignments */}
        {test.assignments?.length > 0 && (
          <Card style={{ marginBottom: "1rem" }}>
            <div style={{ fontSize: "var(--text-sm)", fontWeight: 600, marginBottom: "0.5rem" }}>Назначения:</div>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {test.assignments.map((a: any) => {
                const st = STATUS[a.status] || STATUS.ASSIGNED;
                return <Badge key={a.student_id} variant={st.variant}>{a.student_name || "Ученик"}: {st.label}{a.progress_percent != null ? ` (${a.progress_percent}%)` : ""}</Badge>;
              })}
            </div>
          </Card>
        )}

        {/* View toggle */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
          <Button variant={viewMode === "single" ? "primary" : "secondary"} size="sm" onClick={() => setViewMode("single")}>По одному</Button>
          <Button variant={viewMode === "list" ? "primary" : "secondary"} size="sm" onClick={() => setViewMode("list")}>Список</Button>
        </div>

        {viewMode === "single" && currentTask && (
          <motion.div key={currentTask.task_id} {...slideUp}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
              <Button variant="ghost" size="sm" disabled={currentIdx === 0} onClick={() => setCurrentIdx((i) => i - 1)}>← Назад</Button>
              <span style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>{currentIdx + 1} / {test.tasks.length}</span>
              <Button variant="ghost" size="sm" disabled={currentIdx === test.tasks.length - 1} onClick={() => setCurrentIdx((i) => i + 1)}>Вперёд →</Button>
            </div>
            <Card>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
                <Badge variant="info">Тип {currentTask.exam_position || "?"}</Badge>
                <Badge variant={currentTask.type === "TEST" ? "default" : "warning"}>{currentTask.type}</Badge>
                <Button variant="ghost" size="sm" onClick={() => setShowInfo(true)}>ℹ</Button>
              </div>
              {currentTask.text_content?.images?.filter((p: string) => p != null && p.length > 0).length > 0 && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "0.75rem", margin: "1rem 0" }}>
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {currentTask.text_content.images.filter((p: any) => p != null && p.length > 0).map((imgPath: string, i: number) => (
                    <div key={imgPath} style={{ position: "relative", cursor: "pointer" }} onClick={() => setLightboxSrc(`/api/v1/media/images/${imgPath.split("/").pop()}`)}>
                      <img src={`/api/v1/media/images/${imgPath.split("/").pop()}`} alt={`${i + 1}`} style={{ width: "100%", display: "block", borderRadius: "var(--r-md)", border: "1px solid var(--c-border)" }} onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                    </div>
                  ))}
                </div>
              )}
              {renderContent(currentTask, true)}
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid var(--c-border)" }}>
                <Button variant="ghost" size="sm" onClick={() => replaceTask(currentTask.task_id, currentTask.type)}>Заменить</Button>
                <Button variant="ghost" size="sm" onClick={() => removeTask(currentTask.task_id)}>Удалить задание</Button>
              </div>
            </Card>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.75rem" }}>
              <Button variant="ghost" size="sm" disabled={currentIdx === 0} onClick={() => setCurrentIdx((i) => i - 1)}>← Назад</Button>
              <span style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>{currentIdx + 1} / {test.tasks.length}</span>
              <Button variant="ghost" size="sm" disabled={currentIdx === test.tasks.length - 1} onClick={() => setCurrentIdx((i) => i + 1)}>Вперёд →</Button>
            </div>
          </motion.div>
        )}

        {viewMode === "list" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {test.tasks?.map((task: any, idx: number) => {
              const exp = expandedTasks.has(task.task_id);
              return (
                <motion.div key={task.task_id} {...slideUp}>
                  <Card hover onClick={() => setExpandedTasks((p) => { const n = new Set(p); n.has(task.task_id) ? n.delete(task.task_id) : n.add(task.task_id); return n; })}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                      <span style={{ fontWeight: 600, minWidth: 24, fontSize: "var(--text-sm)" }}>{idx + 1}</span>
                      <Badge variant="info">Тип {task.exam_position || "?"}</Badge>
                      <Badge variant={task.type === "TEST" ? "default" : "warning"}>{task.type}</Badge>
                      <span style={{ flex: 1, fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>{getShort(task)}</span>
                      <span style={{ fontSize: "var(--text-xs)", color: "var(--c-text-tertiary)" }}>{exp ? "▲" : "▼"}</span>
                    </div>
                    <AnimatePresence>
                      {exp && (
                        <motion.div {...expand}>
                          {renderContent(task, true)}
                          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid var(--c-border)" }}>
                            <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); replaceTask(task.task_id, task.type); }}>Заменить</Button>
                            <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); removeTask(task.task_id); }}>Удалить</Button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        )}
      </PageWrapper>

      {/* Info Modal */}
      <Modal open={showInfo} onClose={() => setShowInfo(false)} title="Информация о задании">
        <p style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>Тема: {currentTask?.theme_name || currentTask?.theme_id}</p>
        <p style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>Тип: {currentTask?.exam_position ? `Тип ${currentTask.exam_position}` : "—"}{currentTask?.difficulty_level ? ` (${currentTask.difficulty_level})` : ""}</p>
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
