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
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ThemeNode = any;

const OGE_POSITIONS: Record<string, number> = { "История": 24, "Обществознание": 26 };
const EGE_POSITIONS: Record<string, number> = { "История": 21, "Обществознание": 1 };

export default function NewTestPage() {
  const { auth, hydrated } = useAuth();
  const router = useRouter();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [examType, setExamType] = useState<"EGE" | "OGE">("EGE");
  const [themeTree, setThemeTree] = useState<ThemeNode[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [taskCounts, setTaskCounts] = useState<Record<string, { test: number; essay: number }>>({});
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [expandedThemes, setExpandedThemes] = useState<Set<string>>(new Set());
  const [title, setTitle] = useState("");
  const [timeLimit, setTimeLimit] = useState("");
  const [countPerTheme, setCountPerTheme] = useState("5");
  const [taskType, setTaskType] = useState("MIX");
  const [selectedPositions, setSelectedPositions] = useState<number[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingCounts, setLoadingCounts] = useState(false);
  const [creating, setCreating] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [progress, setProgress] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  // Quick generation state
  const [quickSubject, setQuickSubject] = useState("");
  const [quickLoading, setQuickLoading] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [quickResult, setQuickResult] = useState<any>(null);
  const [quickError, setQuickError] = useState("");

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
            {has ? <span onClick={(e) => { e.stopPropagation(); toggleExpand(node.id); }} style={{ cursor: "pointer", fontSize: 10, width: 14, textAlign: "center" }}>{exp ? "\u2212" : "+"}</span> : <span style={{ width: 14 }} />}
            <span style={{ fontSize: "var(--text-sm)", cursor: has ? "pointer" : "default" }} onClick={() => has && toggleExpand(node.id)}>
              {node.fipi_code && <span style={{ color: "var(--c-text-tertiary)", marginRight: 4 }}>{node.fipi_code}</span>}
              {node.name}
            </span>
            {counts && total > 0 && <span style={{ fontSize: "var(--text-xs)", color: "var(--c-text-secondary)" }}>({counts.test}T {counts.essay}E)</span>}
            {!counts && !loadingCounts && <span style={{ fontSize: "var(--text-xs)", color: "var(--c-text-tertiary)" }}>нет</span>}
            {loadingCounts && <Spinner size="sm" />}
          </label>
          <AnimatePresence>{has && exp && <motion.div {...expand}>{renderTree(node.children, depth + 1)}</motion.div>}</AnimatePresence>
        </div>
      );
    });

  const currentSubject = subjects.find((s) => s.id === selectedSubject);
  const maxPos = examType === "EGE" ? (EGE_POSITIONS[currentSubject?.name || ""] || 21) : (OGE_POSITIONS[currentSubject?.name || ""] || 24);
  const subjectList = subjects.filter((s) => s.exam_type === examType);

  // Quick generation flow
  const quickSubjects = subjects.filter((s) => s.exam_type === "EGE" || s.exam_type === "OGE");
  // Unique subject names (История, Обществознание)
  const quickSubjectNames = [...new Set(quickSubjects.map((s) => s.name))];

  const handleQuickGenerate = async (examType: "EGE" | "OGE") => {
    setQuickLoading(true); setQuickError(""); setQuickResult(null);
    try {
      const r = examType === "EGE"
        ? await api.generateEGE({}, auth.token!)
        : await api.generateOGE({ subject_name: quickSubject }, auth.token!);
      setQuickResult(r);
    } catch (e: unknown) { setQuickError(e instanceof Error ? e.message : "Ошибка"); }
    setQuickLoading(false);
  };

  // Create test flow
  const handleCreate = async () => {
    if (!title.trim()) { setError("Введите название"); return; }
    if (!selectedSubject) { setError("Выберите предмет"); return; }
    setError(""); setCreating(true); setProgress({ status: "Запускаем..." });
    try {
      const res = await api.createTestAsync({
        title: title.trim(),
        theme_codes: selectedThemes.length > 0 ? collectThemeCodes(themeTree, selectedThemes) : [],
        count_per_theme: parseInt(countPerTheme) || 5,
        task_type: taskType,
        time_limit_minutes: timeLimit ? parseInt(timeLimit) : undefined,
        exam_positions: selectedPositions.length > 0 ? selectedPositions : undefined,
      }, auth.token!);
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

  if (loading) return <div className="layout"><Sidebar /><div className="layout-content" style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><Spinner size="lg" /></div></div>;

  if (subjects.length === 0) return <div className="layout"><Sidebar /><PageWrapper title="Создать тест"><EmptyState icon="📚" title="Нет предметов" text="Синхронизируйте кодификатор из ФИПИ" action={<Button onClick={() => router.push("/content")}>Контент</Button>} /></PageWrapper></div>;

  if (result) return (
    <div className="layout"><Sidebar />
      <PageWrapper title="Тест создан!">
        <Card style={{ textAlign: "center" }}>
          <div style={{ fontSize: 48, marginBottom: "1rem" }}>{"\u2713"}</div>
          <h2 style={{ marginBottom: "0.5rem" }}>{result.title}</h2>
          <p style={{ color: "var(--c-text-secondary)", marginBottom: "1rem" }}>Заданий: {result.tasks_count}{result.max_points ? `, ${result.max_points} баллов` : ""}</p>
          {result.warnings?.length > 0 && <div style={{ marginBottom: "1rem", textAlign: "left" }}>{result.warnings.map((w: string, i: number) => <div key={i} style={{ fontSize: "var(--text-sm)", color: "var(--c-warning)" }}>{"\u26A0"} {w}</div>)}</div>}
          <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center", marginTop: "1.5rem" }}>
            <Button onClick={() => router.push(`/tests/${result.test_id}`)}>Открыть тест</Button>
            <Button variant="secondary" onClick={() => { setResult(null); setTitle(""); setSelectedThemes([]); setSelectedSubject(""); }}>Создать ещё</Button>
          </div>
        </Card>
      </PageWrapper>
    </div>
  );

  return (
    <div className="layout"><Sidebar />
      <PageWrapper title="Создать тест">
        {error && <div style={{ padding: "0.75rem 1rem", background: "var(--c-danger-bg)", borderRadius: "var(--r-md)", color: "var(--c-danger)", marginBottom: "1rem", display: "flex", justifyContent: "space-between" }}><span>{error}</span><button onClick={() => setError("")} style={{ background: "none", border: "none", cursor: "pointer" }}>{"\u2715"}</button></div>}
        {creating && <Card style={{ textAlign: "center", marginBottom: "1rem" }}><Spinner size="lg" /><p style={{ fontWeight: 500, marginTop: "0.75rem" }}>{progress?.status || progress?.meta?.status || "Обработка..."}</p></Card>}

        <motion.div style={{ display: "flex", flexDirection: "column", gap: "1rem" }} {...slideUp}>

          {/* === БЛОК 1: Быстрая генерация === */}
          <Card>
            <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.5rem" }}>Быстрая генерация</h3>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--c-text-secondary)", marginBottom: "1rem" }}>Автоматический подбор варианта по КИМам</p>

            {/* Шаг 1: Выбор предмета */}
            <div style={{ marginBottom: quickSubject ? "0.75rem" : 0 }}>
              <div style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--c-text-secondary)", marginBottom: 6, textTransform: "uppercase" }}>Предмет</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {quickSubjectNames.map((name) => (
                  <motion.button key={name} whileTap={{ scale: 0.97 }}
                    style={{ padding: "6px 16px", borderRadius: "var(--r-md)", border: "1px solid", cursor: "pointer", fontWeight: 500, fontSize: "var(--text-sm)",
                      background: quickSubject === name ? "var(--c-primary)" : "var(--c-surface)",
                      color: quickSubject === name ? "white" : "var(--c-text)",
                      borderColor: quickSubject === name ? "var(--c-primary)" : "var(--c-border)" }}
                    onClick={() => { setQuickSubject(name); setQuickResult(null); setQuickError(""); }}
                    disabled={quickLoading}>
                    {name}
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Шаг 2: Кнопки генерации (после выбора предмета) */}
            {quickSubject && (
              <div>
                <div style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--c-text-secondary)", marginBottom: 6, textTransform: "uppercase" }}>Экзамен</div>
                {quickError && <div style={{ padding: "0.75rem", background: "var(--c-danger-bg)", borderRadius: "var(--r-md)", color: "var(--c-danger)", marginBottom: "0.75rem", fontSize: "var(--text-sm)" }}>{quickError}</div>}
                {quickResult && <div style={{ padding: "0.75rem", background: "var(--c-success-bg)", borderRadius: "var(--r-md)", color: "#166534", marginBottom: "0.75rem", fontSize: "var(--text-sm)" }}>
                  <strong>{quickResult.title}</strong> {"\u2014"} {quickResult.tasks_count} заданий{quickResult.max_points ? `, ${quickResult.max_points} баллов` : ""}
                  {" "}<a href={`/tests/${quickResult.test_id}`}>Открыть {"\u2192"}</a>
                </div>}
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                  <Button variant="accent" onClick={() => handleQuickGenerate("EGE")} loading={quickLoading}>Сгенерировать ЕГЭ</Button>
                  <Button variant="secondary" onClick={() => handleQuickGenerate("OGE")} loading={quickLoading}>Сгенерировать ОГЭ</Button>
                </div>
              </div>
            )}
          </Card>

          {/* === БЛОК 2: Создать тест === */}
          <Card>
            <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginBottom: "0.75rem" }}>Создать тест</h3>

            {/* Шаг 1: Название */}
            <Input label="Название теста" placeholder="Например: Диагностический тест по истории" value={title} onChange={(e) => setTitle(e.target.value)} disabled={creating} />

            {/* Шаг 2: Тип экзамена */}
            <div style={{ marginTop: "1rem" }}>
              <div style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--c-text-secondary)", marginBottom: 6, textTransform: "uppercase" }}>Тип экзамена</div>
              <div style={{ display: "flex", gap: 0, borderRadius: "var(--r-md)", overflow: "hidden", border: "1px solid var(--c-border)" }}>
                {(["EGE", "OGE"] as const).map((et) => (
                  <button key={et} onClick={() => { setExamType(et); setSelectedSubject(""); setSelectedThemes([]); setThemeTree([]); setSelectedPositions([]); }}
                    style={{ flex: 1, padding: "0.5rem 1rem", border: "none", cursor: "pointer", fontSize: "var(--text-sm)", fontWeight: 600,
                      background: examType === et ? "var(--c-primary)" : "var(--c-bg-secondary)",
                      color: examType === et ? "white" : "var(--c-text-secondary)" }}>
                    {et === "EGE" ? "ЕГЭ" : "ОГЭ"}
                  </button>
                ))}
              </div>
            </div>

            {/* Шаг 3: Предмет */}
            <div style={{ marginTop: "1rem" }}>
              <div style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--c-text-secondary)", marginBottom: 6, textTransform: "uppercase" }}>Предмет</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {subjectList.map((s) => (
                  <motion.button key={s.id} whileTap={{ scale: 0.97 }}
                    style={{ padding: "5px 14px", borderRadius: "var(--r-md)", border: "1px solid", cursor: "pointer", fontWeight: 500, fontSize: "var(--text-sm)",
                      background: selectedSubject === s.id ? "var(--c-primary)" : "var(--c-surface)",
                      color: selectedSubject === s.id ? "white" : "var(--c-text)",
                      borderColor: selectedSubject === s.id ? "var(--c-primary)" : "var(--c-border)" }}
                    onClick={() => loadThemes(s.id)} disabled={creating}>
                    {s.name}
                  </motion.button>
                ))}
                {subjectList.length === 0 && <span style={{ fontSize: "var(--text-sm)", color: "var(--c-text-tertiary)" }}>Нет предметов</span>}
              </div>
            </div>

            {/* Шаг 4: Темы + Типы заданий + Параметры */}
            {selectedSubject && (
              <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                {/* Темы */}
                {themeTree.length > 0 && (
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <div style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--c-text-secondary)", textTransform: "uppercase" }}>Темы <span style={{ fontWeight: 400, textTransform: "none" }}>({selectedThemes.length} выбрано)</span></div>
                      <div style={{ display: "flex", gap: 4 }}>
                        <Button variant="ghost" size="sm" onClick={() => setSelectedThemes(themeTree.map((n) => n.id))}>Все</Button>
                        <Button variant="ghost" size="sm" onClick={() => setSelectedThemes([])}>Очистить</Button>
                      </div>
                    </div>
                    <div style={{ maxHeight: 280, overflowY: "auto", border: "1px solid var(--c-border)", borderRadius: "var(--r-md)", padding: "0.5rem" }}>
                      {renderTree(themeTree)}
                    </div>
                  </div>
                )}

                {/* Тип заданий */}
                <div>
                  <div style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--c-text-secondary)", marginBottom: 6, textTransform: "uppercase" }}>Тип заданий</div>
                  <div style={{ display: "flex", gap: 6 }}>
                    {[{ value: "MIX", label: "Все" }, { value: "TEST", label: "Тест" }, { value: "ESSAY", label: "Развёрнутые" }].map((opt) => (
                      <motion.button key={opt.value} whileTap={{ scale: 0.97 }}
                        style={{ padding: "5px 14px", borderRadius: "var(--r-md)", border: "1px solid", cursor: "pointer", fontWeight: 500, fontSize: "var(--text-sm)",
                          background: taskType === opt.value ? "var(--c-accent)" : "var(--c-surface)",
                          color: taskType === opt.value ? "white" : "var(--c-text)",
                          borderColor: taskType === opt.value ? "var(--c-accent)" : "var(--c-border)" }}
                        onClick={() => setTaskType(opt.value)} disabled={creating}>
                        {opt.label}
                      </motion.button>
                    ))}
                  </div>
                </div>

                {/* Параметры */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                  <Input label="Лимит (мин)" type="number" placeholder="Без таймера" value={timeLimit} onChange={(e) => setTimeLimit(e.target.value)} disabled={creating} />
                  <Input label="Заданий на тему" type="number" value={countPerTheme} onChange={(e) => setCountPerTheme(e.target.value)} disabled={creating} />
                </div>

                {/* Типы КИМ */}
                <div>
                  <div style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--c-text-secondary)", marginBottom: 6, textTransform: "uppercase" }}>Типы КИМ <span style={{ fontWeight: 400, textTransform: "none" }}>(необязательно)</span></div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                    {Array.from({ length: maxPos }, (_, i) => i + 1).map((p) => (
                      <motion.button key={p} whileTap={{ scale: 0.9 }}
                        style={{ padding: "3px 7px", borderRadius: "var(--r-sm)", border: "1px solid", fontSize: "var(--text-xs)", fontWeight: 500, cursor: "pointer",
                          background: selectedPositions.includes(p) ? "var(--c-accent)" : "var(--c-surface)",
                          color: selectedPositions.includes(p) ? "white" : "var(--c-text)",
                          borderColor: selectedPositions.includes(p) ? "var(--c-accent)" : "var(--c-border)" }}
                        onClick={() => setSelectedPositions((prev) => prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p])} disabled={creating}>
                        {p}
                      </motion.button>
                    ))}
                  </div>
                  {selectedPositions.length > 0 && <div style={{ marginTop: 6 }}><Badge>{selectedPositions.length} поз.</Badge> <button onClick={() => setSelectedPositions([])} style={{ background: "none", border: "none", color: "var(--c-danger)", fontSize: "var(--text-xs)", cursor: "pointer" }}>очистить</button></div>}
                </div>
              </div>
            )}

            {/* Кнопка создания */}
            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
              <Button variant="accent" onClick={handleCreate} disabled={!title.trim() || !selectedSubject || creating} loading={creating}>{creating ? "Создание..." : "Создать тест"}</Button>
              <Button variant="secondary" onClick={() => router.back()} disabled={creating}>Отмена</Button>
            </div>
          </Card>

        </motion.div>
      </PageWrapper>
    </div>
  );
}
