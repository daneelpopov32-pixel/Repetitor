"use client";

import { useEffect, useState, useRef, useCallback } from "react";
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
import ProgressBar from "@/components/ui/ProgressBar";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ThemeNode = any;

export default function NewTestPage() {
  const { auth, hydrated } = useAuth();
  const router = useRouter();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [themeTree, setThemeTree] = useState<ThemeNode[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [taskCounts, setTaskCounts] = useState<Record<string, { test: number; essay: number }>>({});
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [expandedThemes, setExpandedThemes] = useState<Set<string>>(new Set());
  const [title, setTitle] = useState("");
  const [timeLimit, setTimeLimit] = useState("");
  const [countPerTheme, setCountPerTheme] = useState("5");
  const [taskType, setTaskType] = useState("TEST");
  const [selectedPositions, setSelectedPositions] = useState<number[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingCounts, setLoadingCounts] = useState(false);
  const [creating, setCreating] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [progress, setProgress] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);
  const [egeLoading, setEgeLoading] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [egeResult, setEgeResult] = useState<any>(null);
  const [egeError, setEgeError] = useState("");

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token || auth.role !== "TUTOR") { router.replace("/auth/login"); return; }
    api.getSubjects(auth.token).then(setSubjects).catch(() => {}).finally(() => setLoading(false));
  }, [auth.token, hydrated]);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const loadThemes = async (sid: string) => {
    setSelectedSubject(sid); setSelectedThemes([]); setError(""); setResult(null);
    setLoadingCounts(true); setThemeTree([]); setTaskCounts({});
    try { const d = await api.getThemeTree(sid, auth.token!); setThemeTree(d.themes || []); } catch { setLoadingCounts(false); return; }
    try {
      const fc = await api.getFipiCounts(sid, auth.token!);
      const c: Record<string, { test: number; essay: number }> = {};
      for (const x of fc) { if (x.fipi_code) c[x.fipi_code] = { test: x.test_count, essay: x.essay_count }; if (x.theme_id) c[x.theme_id] = { test: x.test_count, essay: x.essay_count }; }
      setTaskCounts(c);
    } catch {}
    setLoadingCounts(false);
  };

  const toggleTheme = (id: string) => setSelectedThemes((p) => p.includes(id) ? p.filter((t) => t !== id) : [...p, id]);
  const toggleExpand = (id: string) => setExpandedThemes((p) => { const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n; });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const collectThemeCodes = useCallback((nodes: any[], sel: string[]): string[] => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let codes: string[] = [];
    for (const n of nodes) { if (sel.includes(n.id) && n.fipi_code) codes.push(n.fipi_code); if (n.children) codes = codes.concat(collectThemeCodes(n.children, sel)); }
    return codes;
  }, []);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getCounts = (node: any) => node.fipi_code && taskCounts[node.fipi_code] ? taskCounts[node.fipi_code] : taskCounts[node.id] || null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderTree = (nodes: ThemeNode[], depth = 0): React.ReactNode =>
    nodes.map((node) => {
      const counts = getCounts(node);
      const total = (counts?.test || 0) + (counts?.essay || 0);
      const has = node.children?.length > 0;
      const exp = expandedThemes.has(node.id);
      return (
        <div key={node.id}>
          <label style={{ display: "flex", alignItems: "center", gap: 8, padding: "3px 0", paddingLeft: depth * 16 }}>
            <input type="checkbox" checked={selectedThemes.includes(node.id)} onChange={() => toggleTheme(node.id)} />
            {has ? <span onClick={(e) => { e.stopPropagation(); toggleExpand(node.id); }} style={{ cursor: "pointer", fontSize: 10, width: 14, textAlign: "center" }}>{exp ? "−" : "+"}</span> : <span style={{ width: 14 }} />}
            <span style={{ fontSize: "var(--text-sm)", cursor: has ? "pointer" : "default" }} onClick={() => has && toggleExpand(node.id)}>
              {node.fipi_code && <span style={{ color: "var(--c-text-tertiary)", marginRight: 4 }}>{node.fipi_code}</span>}
              {node.name}
            </span>
            {counts && total > 0 && <span style={{ fontSize: "var(--text-xs)", color: "var(--c-text-secondary)" }}>({counts.test}T {counts.essay}E)</span>}
            {!counts && !loadingCounts && <span style={{ fontSize: "var(--text-xs)", color: "var(--c-text-tertiary)" }}>нет заданий</span>}
            {loadingCounts && <Spinner size="sm" />}
          </label>
          <AnimatePresence>{has && exp && <motion.div {...expand}>{renderTree(node.children, depth + 1)}</motion.div>}</AnimatePresence>
        </div>
      );
    });

  const canCreate = title.trim() && selectedThemes.length > 0 && !creating;
  const validationError = !title.trim() ? "Введите название" : selectedThemes.length === 0 ? "Выберите темы" : null;

  const handleCreate = async () => {
    if (validationError) { setError(validationError); return; }
    setError(""); setCreating(true); setProgress({ status: "Запускаем..." });
    try {
      const res = await api.createTestAsync({ title: title.trim(), theme_codes: collectThemeCodes(themeTree, selectedThemes), count_per_theme: parseInt(countPerTheme) || 5, task_type: taskType, time_limit_minutes: timeLimit ? parseInt(timeLimit) : undefined, exam_positions: selectedPositions.length > 0 ? selectedPositions : undefined }, auth.token!);
      setTaskId(res.task_id);
      pollRef.current = setInterval(async () => {
        try {
          const s = await api.getTaskStatus(res.task_id, auth.token!);
          setProgress(s);
          if (s.status === "SUCCESS") { clearInterval(pollRef.current!); setResult(s.result); setCreating(false); setProgress(null); }
          else if (s.status === "FAILURE") { clearInterval(pollRef.current!); setError(s.error || "Ошибка"); setCreating(false); setProgress(null); }
        } catch {}
      }, 2000);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); setCreating(false); setProgress(null); }
  };

  const handleEGE = async () => {
    setEgeLoading(true); setEgeError(""); setEgeResult(null);
    try { const r = await api.generateEGE({}, auth.token!); setEgeResult(r); }
    catch (e: unknown) { setEgeError(e instanceof Error ? e.message : "Ошибка"); }
    setEgeLoading(false);
  };

  if (loading) return <div className="layout"><Sidebar /><div className="layout-content" style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><Spinner size="lg" /></div></div>;

  if (subjects.length === 0) return <div className="layout"><Sidebar /><PageWrapper title="Создать тест"><EmptyState icon="📚" title="Нет предметов" text="Синхронизируйте кодификатор из ФИПИ" action={<Button onClick={() => router.push("/content")}>Контент</Button>} /></PageWrapper></div>;

  if (result) return (
    <div className="layout"><Sidebar />
      <PageWrapper title="Тест создан!">
        <Card style={{ textAlign: "center" }}>
          <div style={{ fontSize: 48, marginBottom: "1rem" }}>✅</div>
          <h2 style={{ marginBottom: "0.5rem" }}>{result.title}</h2>
          <p style={{ color: "var(--c-text-secondary)", marginBottom: "1rem" }}>Добавлено заданий: {result.tasks_count}</p>
          {result.theme_stats && Object.entries(result.theme_stats).map(([code, count]) => (
            <div key={code} style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>Тема {code}: {String(count)} заданий{String(count) === "0" && <span style={{ color: "var(--c-danger)" }}> — не найдены</span>}</div>
          ))}
          <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center", marginTop: "1.5rem" }}>
            <Button onClick={() => router.push("/dashboard")}>На дашборд</Button>
            <Button variant="secondary" onClick={() => { setResult(null); setTitle(""); setSelectedThemes([]); }}>Создать ещё</Button>
          </div>
        </Card>
      </PageWrapper>
    </div>
  );

  return (
    <div className="layout"><Sidebar />
      <PageWrapper title="Создать тест">
        {error && <div style={{ padding: "0.75rem 1rem", background: "var(--c-danger-bg)", borderRadius: "var(--r-md)", color: "var(--c-danger)", marginBottom: "1rem", display: "flex", justifyContent: "space-between" }}><span>{error}</span><button onClick={() => setError("")} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button></div>}

        {creating && (
          <Card style={{ textAlign: "center", marginBottom: "1rem" }}>
            <Spinner size="lg" />
            <p style={{ fontWeight: 500, marginTop: "0.75rem" }}>{progress?.status || progress?.meta?.status || "Обработка..."}</p>
            {progress?.meta?.tasks_found !== undefined && <p style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>Найдено: {progress.meta.tasks_found}</p>}
          </Card>
        )}

        <motion.div style={{ display: "flex", flexDirection: "column", gap: "1rem" }} {...slideUp}>
          {/* Settings */}
          <Card>
            <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "1rem" }}>Параметры</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <Input label="Название теста" placeholder="Например: Диагностический тест по истории" value={title} onChange={(e) => setTitle(e.target.value)} disabled={creating} />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem" }}>
                <Input label="Лимит (мин)" type="number" placeholder="Без таймера" value={timeLimit} onChange={(e) => setTimeLimit(e.target.value)} disabled={creating} />
                <Input label="Заданий на тему" type="number" value={countPerTheme} onChange={(e) => setCountPerTheme(e.target.value)} disabled={creating} />
                <Select label="Тип" value={taskType} onChange={(e) => setTaskType(e.target.value)} options={[{ value: "TEST", label: "TEST" }, { value: "ESSAY", label: "ESSAY" }, { value: "MIX", label: "Микс" }]} />
              </div>
            </div>
          </Card>

          {/* Position filter */}
          <Card>
            <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.75rem" }}>Типы КИМ <span style={{ fontWeight: 400, fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>необязательно</span></h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {Array.from({ length: 21 }, (_, i) => i + 1).map((p) => (
                <motion.button key={p} whileTap={{ scale: 0.9 }}
                  style={{ padding: "4px 8px", borderRadius: "var(--r-sm)", border: "1px solid", fontSize: "var(--text-xs)", fontWeight: 500, cursor: "pointer",
                    background: selectedPositions.includes(p) ? "var(--c-primary)" : "var(--c-surface)",
                    color: selectedPositions.includes(p) ? "white" : "var(--c-text)",
                    borderColor: selectedPositions.includes(p) ? "var(--c-primary)" : "var(--c-border)" }}
                  onClick={() => setSelectedPositions((prev) => prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p])} disabled={creating}
                >{p}</motion.button>
              ))}
            </div>
            {selectedPositions.length > 0 && <div style={{ marginTop: 8 }}><Badge>{selectedPositions.join(", ")}</Badge> <button onClick={() => setSelectedPositions([])} style={{ background: "none", border: "none", color: "var(--c-danger)", fontSize: "var(--text-xs)", cursor: "pointer" }}>очистить</button></div>}
          </Card>

          {/* Subjects */}
          <Card>
            <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.75rem" }}>Предмет</h3>
            <div style={{ display: "flex", gap: 8 }}>
              {subjects.map((s) => (
                <motion.button key={s.id} whileTap={{ scale: 0.97 }}
                  style={{ padding: "6px 16px", borderRadius: "var(--r-md)", border: "1px solid", cursor: "pointer", fontWeight: 500, fontSize: "var(--text-sm)",
                    background: selectedSubject === s.id ? "var(--c-primary)" : "var(--c-surface)",
                    color: selectedSubject === s.id ? "white" : "var(--c-text)",
                    borderColor: selectedSubject === s.id ? "var(--c-primary)" : "var(--c-border)" }}
                  onClick={() => loadThemes(s.id)} disabled={creating}
                >{s.name}</motion.button>
              ))}
            </div>
          </Card>

          {/* Theme tree */}
          {themeTree.length > 0 && (
            <Card>
              <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.75rem" }}>Темы <span style={{ fontWeight: 400, fontSize: "var(--text-sm)", color: "var(--c-text-secondary)" }}>({selectedThemes.length} выбрано)</span></h3>
              <div style={{ maxHeight: 400, overflowY: "auto" }}>{renderTree(themeTree)}</div>
            </Card>
          )}

          {/* Create button */}
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <Button onClick={handleCreate} disabled={!canCreate}>{creating ? "Создание..." : "Создать тест"}</Button>
            <Button variant="secondary" onClick={() => router.back()} disabled={creating}>Отмена</Button>
          </div>

          {/* EGE Generator */}
          <Card>
            <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.5rem" }}>Генератор варианта ЕГЭ</h3>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)", marginBottom: "1rem" }}>Автоматически соберёт полный вариант из 21 задания (210 мин).</p>
            {egeResult && <div style={{ padding: "0.75rem", background: "var(--c-success-bg)", borderRadius: "var(--r-md)", color: "#166534", marginBottom: "1rem", fontSize: "var(--text-sm)" }}>Вариант: <strong>{egeResult.title}</strong> ({egeResult.tasks_count} заданий) <a href={`/tests/${egeResult.test_id}`}>Открыть →</a></div>}
            {egeError && <div style={{ padding: "0.75rem", background: "var(--c-danger-bg)", borderRadius: "var(--r-md)", color: "var(--c-danger)", marginBottom: "1rem", fontSize: "var(--text-sm)" }}>{egeError}</div>}
            <Button variant="secondary" onClick={handleEGE} loading={egeLoading}>Сгенерировать вариант ЕГЭ</Button>
          </Card>
        </motion.div>
      </PageWrapper>
    </div>
  );
}
