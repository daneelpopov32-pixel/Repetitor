"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import { slideUp, expand } from "@/lib/motion";
import Sidebar from "@/components/layout/Sidebar";
import PageWrapper from "@/components/layout/PageWrapper";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";

interface ThemeNode { id: string; name: string; fipi_code?: string; children: ThemeNode[]; }
// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface Task { id: string; type: string; theme_id: string; text_preview: string; exam_position?: number; difficulty_level?: string; }

export default function ContentPage() {
  const { auth, hydrated, logout } = useAuth();
  const router = useRouter();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [examType, setExamType] = useState<"EGE" | "OGE">("EGE");
  const [themeTree, setThemeTree] = useState<ThemeNode[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskTotal, setTaskTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showAddSubject, setShowAddSubject] = useState(false);
  const [newSubjectName, setNewSubjectName] = useState("");
  const [selectedTheme, setSelectedTheme] = useState("");
  const [expandedThemes, setExpandedThemes] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [syncStatus, setSyncStatus] = useState<Record<string, unknown>[] | null>(null);
  const [syncLoading, setSyncLoading] = useState(false);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token || auth.role !== "TUTOR") { router.replace("/auth/login"); return; }
    api.getSubjects(auth.token).then((data) => {
      setSubjects(data);
      if (data.length > 0) setSelectedSubject(data[0].id);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [auth.token, hydrated]);

  useEffect(() => {
    if (selectedSubject && auth.token) {
      api.getThemeTree(selectedSubject, auth.token).then((d) => setThemeTree(d.themes || [])).catch(() => {});
      loadTasks(selectedSubject);
    }
  }, [selectedSubject, auth.token]);

  const loadTasks = async (sid: string, tid?: string) => {
    if (!auth.token) return;
    try {
      const params = tid ? { theme_id: tid } : { subject_id: sid };
      const data = await api.listTasks(params, auth.token);
      setTasks(data.tasks || []);
      setTaskTotal(data.total || 0);
    } catch {}
  };

  const handleThemeClick = (id: string) => { setSelectedTheme(id); loadTasks(selectedSubject, id); };
  const toggleExpand = (id: string) => setExpandedThemes((prev) => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const handleAddSubject = async () => {
    if (!newSubjectName.trim()) return;
    try {
      await api.createSubject(newSubjectName.trim(), auth.token!);
      setNewSubjectName(""); setShowAddSubject(false); setSuccess("Предмет добавлен");
      api.getSubjects(auth.token!).then(setSubjects);
      setTimeout(() => setSuccess(""), 3000);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
  };

  const syncAction = async (fn: () => Promise<unknown>, msg: string) => {
    try { const res = await fn(); setSuccess(`${msg} (задача: ${(res as Record<string, string>).task_id?.slice(0, 8)}...)`); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
  };

  const loadSyncStatus = async () => {
    if (!auth.token) return;
    setSyncLoading(true);
    try {
      const data = await api.getSyncStatus(auth.token);
      setSyncStatus(data);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка загрузки статуса"); }
    setSyncLoading(false);
  };

  const renderThemeTree = (nodes: ThemeNode[], depth = 0): React.ReactNode =>
    nodes.map((node) => {
      const hasChildren = node.children?.length > 0;
      const isExpanded = expandedThemes.has(node.id);
      const isSelected = selectedTheme === node.id;
      return (
        <div key={node.id}>
          <motion.div
            onClick={() => handleThemeClick(node.id)}
            style={{
              padding: "0.35rem 0.5rem", paddingLeft: depth * 16 + 8,
              borderRadius: "var(--r-md)", cursor: "pointer",
              background: isSelected ? "var(--c-primary)" : "transparent",
              color: isSelected ? "white" : "var(--c-text)",
              display: "flex", alignItems: "center", gap: 6, fontSize: "var(--text-sm)",
            }}
            whileHover={{ background: isSelected ? undefined : "var(--c-hover)" }}
          >
            {hasChildren
              ? <span onClick={(e) => { e.stopPropagation(); toggleExpand(node.id); }} style={{ fontSize: 10, width: 14, textAlign: "center" }}>{isExpanded ? "▼" : "▶"}</span>
              : <span style={{ width: 14 }}
            />}
            {node.fipi_code && <span style={{ color: isSelected ? "#ccc" : "var(--c-text-tertiary)", fontSize: "var(--text-xs)" }}>{node.fipi_code}</span>}
            <span className="truncate">{node.name}</span>
          </motion.div>
          <AnimatePresence>
            {hasChildren && isExpanded && (
              <motion.div {...expand}>{renderThemeTree(node.children, depth + 1)}</motion.div>
            )}
          </AnimatePresence>
        </div>
      );
    });

  if (loading) return <div className="layout"><Sidebar /><div className="layout-content" style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><Spinner size="lg" /></div></div>;

  const filteredTasks = filterType ? tasks.filter((t) => t.type === filterType) : tasks;

  return (
    <div className="layout">
      <Sidebar />
      <PageWrapper
        title="Контент"
        actions={
          <div className="content-sync-actions">
            <Button variant="accent" size="sm" onClick={() => { const subj = subjects.find((s) => s.id === selectedSubject); syncAction(() => api.syncCodifier(subj?.name || "История", auth.token!, examType), "Кодификатор синхронизирован"); }}>⟳ Кодификатор</Button>
            <Button variant="secondary" size="sm" onClick={() => { const c = prompt("Код темы (напр. 8. или 1.1):"); if (c) { const subj = subjects.find((s) => s.id === selectedSubject); syncAction(() => api.syncTheme(c, auth.token!, examType, subj?.name || "История"), `Тема ${c} синхронизирована`); } }}>⟳ Тему</Button>
            <Button variant="secondary" size="sm" onClick={() => { if (confirm("Синхронизировать весь предмет?")) { const subj = subjects.find((s) => s.id === selectedSubject); syncAction(() => api.syncSubject(subj?.name || "История", auth.token!, examType), "Предмет синхронизирован"); } }}>⟳ Весь предмет</Button>
            <Button variant="secondary" size="sm" onClick={() => { if (confirm("Синхронизировать изображения из полного списка FIPI?")) { const subj = subjects.find((s) => s.id === selectedSubject); syncAction(() => api.syncImages(auth.token!, examType, subj?.name || "История"), "Синхронизация изображений запущена"); } }}>🖼 Изображения</Button>
          </div>
        }
      >
        {error && <div style={{ padding: "0.75rem 1rem", background: "var(--c-danger-bg)", border: "1px solid #fecaca", borderRadius: "var(--r-md)", color: "var(--c-danger)", marginBottom: "1rem", display: "flex", justifyContent: "space-between" }}><span>{error}</span><button onClick={() => setError("")} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button></div>}
        {success && <div style={{ padding: "0.75rem 1rem", background: "var(--c-success-bg)", border: "1px solid #bbf7d0", borderRadius: "var(--r-md)", color: "#166534", marginBottom: "1rem" }}>{success}</div>}

        {/* Sync Status */}
        <Card style={{ marginBottom: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: syncStatus ? "0.75rem" : 0 }}>
            <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600 }}>Статус синхронизации</h3>
            <Button variant="ghost" size="sm" onClick={loadSyncStatus} loading={syncLoading}>
              {syncStatus ? "Обновить" : "Показать"}
            </Button>
          </div>
          {syncStatus && (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {syncStatus.map((subject: Record<string, unknown>) => (
                <div key={String(subject.subject_id)}>
                  <div style={{ fontWeight: 600, fontSize: "var(--text-sm)", marginBottom: 4 }}>{String(subject.subject_name)}</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                    {(subject.themes as Array<Record<string, unknown>> || []).map((theme) => (
                      <Badge key={String(theme.theme_id)} variant={(theme.task_count as number) > 0 ? "success" : "default"}>
                        {String(theme.fipi_code)} {String(theme.task_count)} зад.
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {subjects.length === 0 && !showAddSubject ? (
          <EmptyState icon="📚" title="Нет предметов" text="Добавьте предмет, чтобы начать" action={<Button onClick={() => setShowAddSubject(true)}>Добавить предмет</Button>} />
        ) : (
          <div className="content-grid" style={{ display: "grid", gap: "1rem" }}>
            {/* Left: subjects */}
            <Card>
              {/* EGE/OGE tabs */}
              <div style={{ display: "flex", gap: 0, marginBottom: "0.75rem", borderRadius: "var(--r-md)", overflow: "hidden", border: "1px solid var(--c-border)" }}>
                {(["EGE", "OGE"] as const).map((et) => (
                  <button key={et} onClick={() => { setExamType(et); setSelectedSubject(""); setSelectedTheme(""); }}
                    style={{ flex: 1, padding: "0.4rem 0.5rem", border: "none", cursor: "pointer", fontSize: "var(--text-xs)", fontWeight: 600,
                      background: examType === et ? "var(--c-primary)" : "var(--c-bg-secondary)",
                      color: examType === et ? "white" : "var(--c-text-secondary)" }}>
                    {et === "EGE" ? "ЕГЭ" : "ОГЭ"}
                  </button>
                ))}
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600 }}>Предметы</h3>
                <Button variant="ghost" size="sm" onClick={() => setShowAddSubject(true)}>+</Button>
              </div>
              <AnimatePresence>
                {showAddSubject && (
                  <motion.div {...expand} style={{ marginBottom: "0.75rem" }}>
                    <Input placeholder="Название" value={newSubjectName} onChange={(e) => setNewSubjectName(e.target.value)} />
                    <div style={{ display: "flex", gap: "0.25rem", marginTop: "0.5rem" }}>
                      <Button size="sm" onClick={handleAddSubject} style={{ flex: 1 }}>Добавить</Button>
                      <Button variant="ghost" size="sm" onClick={() => { setShowAddSubject(false); setNewSubjectName(""); }}>Отмена</Button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              <div className="content-subjects-scroll">
                {subjects.filter((s) => s.exam_type === examType).map((s) => (
                  <div
                    key={s.id}
                    onClick={() => setSelectedSubject(s.id)}
                    style={{
                      padding: "0.4rem 0.75rem", borderRadius: "var(--r-md)", cursor: "pointer",
                      background: selectedSubject === s.id ? "var(--c-accent)" : "transparent",
                      color: selectedSubject === s.id ? "white" : "var(--c-text)",
                      fontSize: "var(--text-sm)", fontWeight: 500, whiteSpace: "nowrap", flexShrink: 0,
                    }}
                  >
                    {s.name}
                  </div>
                ))}
                {subjects.filter((s) => s.exam_type === examType).length === 0 && (
                  <div style={{ fontSize: "var(--text-sm)", color: "var(--c-text-tertiary)", padding: "0.5rem" }}>
                    {examType === "OGE" ? "Нет предметов ОГЭ. Нажмите + для добавления." : "Нет предметов"}
                  </div>
                )}
              </div>
            </Card>

            {/* Right: themes + tasks */}
            <div>
              {selectedSubject && (
                <>
                  <Card style={{ marginBottom: "1rem", maxHeight: 320, overflowY: "auto" }}>
                    <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.5rem" }}>Темы</h3>
                    {themeTree.length > 0 ? renderThemeTree(themeTree) : <Spinner />}
                  </Card>

                  <Card>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem", gap: "0.5rem", flexWrap: "wrap" }}>
                      <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600 }}>Задания ({taskTotal})</h3>
                      <Select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        options={[{ value: "", label: "Все типы" }, { value: "TEST", label: "Тест" }, { value: "ESSAY", label: "Развёрнутый" }]}
                        style={{ minWidth: 120 }}
                      />
                    </div>
                    {filteredTasks.length === 0 ? (
                      <EmptyState icon="📝" title="Нет заданий" text={selectedTheme ? "Выберите другую тему или синхронизируйте" : "Выберите тему слева"} />
                    ) : (
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: 400, overflowY: "auto" }}>
                        {filteredTasks.slice(0, 50).map((t) => (
                          <div key={t.id} style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 0.75rem", borderRadius: "var(--r-md)", border: "1px solid var(--c-border)", fontSize: "var(--text-sm)", flexWrap: "wrap" }}>
                            <Badge variant={t.type === "TEST" ? "info" : "warning"}>{t.type === "TEST" ? "Т" : "Э"}</Badge>
                            {t.exam_position && <Badge variant="default">Тип {t.exam_position}</Badge>}
                            <span className="truncate" style={{ flex: 1, color: "var(--c-text-secondary)", minWidth: 0 }}>
                              {(t.text_preview || "").slice(0, 100)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>
                </>
              )}
            </div>
          </div>
        )}
      </PageWrapper>
    </div>
  );
}
