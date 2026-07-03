"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function NewTestPage() {
  const { auth, hydrated } = useAuth();
  const router = useRouter();
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [themeTree, setThemeTree] = useState<any[]>([]);
  const [taskCounts, setTaskCounts] = useState<Record<string, { test: number; essay: number }>>({});
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [expandedThemes, setExpandedThemes] = useState<Set<string>>(new Set());
  const [title, setTitle] = useState("");
  const [timeLimit, setTimeLimit] = useState("");
  const [countPerTheme, setCountPerTheme] = useState("5");
  const [taskType, setTaskType] = useState("TEST");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  // Async creation state
  const [creating, setCreating] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!auth.token || auth.role !== "TUTOR") {
      router.replace("/auth/login");
      return;
    }
    loadSubjects();
  }, [auth.token, hydrated]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const loadSubjects = async () => {
    try {
      const data = await api.getSubjects(auth.token!);
      setSubjects(data);
    } catch {}
    setLoading(false);
  };

  const loadThemes = async (subjectId: string) => {
    setSelectedSubject(subjectId);
    setSelectedThemes([]);
    setError("");
    setResult(null);
    try {
      const [treeData, countsData] = await Promise.all([
        api.getThemeTree(subjectId, auth.token!),
        api.getThemeTaskCounts(subjectId, auth.token!),
      ]);
      setThemeTree(treeData.themes || []);
      const counts: Record<string, { test: number; essay: number }> = {};
      for (const c of countsData) {
        counts[c.theme_id] = { test: c.test_count, essay: c.essay_count };
      }
      setTaskCounts(counts);
    } catch {}
  };

  const toggleTheme = (id: string) => {
    setSelectedThemes((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  };

  const toggleAllChildren = (node: any) => {
    const collectIds = (n: any): string[] => {
      let ids = [n.id];
      (n.children || []).forEach((c: any) => (ids = ids.concat(collectIds(c))));
      return ids;
    };
    const ids = collectIds(node);
    const allSelected = ids.every((id) => selectedThemes.includes(id));
    if (allSelected) {
      setSelectedThemes((prev) => prev.filter((t) => !ids.includes(t)));
    } else {
      setSelectedThemes((prev) => [...new Set([...prev, ...ids])]);
    }
  };

  // Collect all theme codes (including children) for selected themes
  const collectThemeCodes = useCallback((nodes: any[], selected: string[]): string[] => {
    let codes: string[] = [];
    for (const n of nodes) {
      if (selected.includes(n.id) && n.fipi_code) {
        codes.push(n.fipi_code);
      }
      if (n.children) {
        codes = codes.concat(collectThemeCodes(n.children, selected));
      }
    }
    return codes;
  }, []);

  const toggleExpand = (id: string) => {
    setExpandedThemes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const renderTree = (nodes: any[], depth = 0) => {
    return nodes.map((node) => {
      const counts = taskCounts[node.id];
      const totalTasks = (counts?.test || 0) + (counts?.essay || 0);
      const hasChildren = node.children && node.children.length > 0;
      const isExpanded = expandedThemes.has(node.id);
      return (
        <div key={node.id} style={{ paddingLeft: depth * 1.5 + "rem" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.25rem 0" }}>
            <input
              type="checkbox"
              checked={selectedThemes.includes(node.id)}
              onChange={() => toggleTheme(node.id)}
            />
            {hasChildren ? (
              <span
                style={{ cursor: "pointer", color: "var(--primary)", fontSize: "0.75rem", userSelect: "none", width: "1rem", textAlign: "center" }}
                onClick={() => toggleExpand(node.id)}
              >
                {isExpanded ? "−" : "+"}
              </span>
            ) : (
              <span style={{ width: "1rem" }} />
            )}
            <span
              style={{ cursor: hasChildren ? "pointer" : "default", fontSize: "0.875rem" }}
              onClick={() => hasChildren && toggleExpand(node.id)}
            >
              {node.fipi_code ? `${node.fipi_code} ` : ""}{node.name}
            </span>
            {counts && totalTasks > 0 && (
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                ({counts.test} TEST, {counts.essay} ESSAY)
              </span>
            )}
            {(!counts || totalTasks === 0) && (
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                (будет загружено)
              </span>
            )}
          </label>
          {hasChildren && isExpanded && renderTree(node.children, depth + 1)}
        </div>
      );
    });
  };

  const canCreate = title.trim() && selectedThemes.length > 0 && !creating;

  const getValidationError = (): string | null => {
    if (!title.trim()) return "Введите название теста";
    if (!selectedSubject) return "Выберите предмет";
    if (selectedThemes.length === 0) return "Выберите хотя бы одну тему";
    return null;
  };

  const handleCreate = async () => {
    const validationError = getValidationError();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError("");
    setCreating(true);
    setProgress({ status: "Запускаем создание теста..." });

    try {
      const themeCodes = collectThemeCodes(themeTree, selectedThemes);
      const res = await api.createTestAsync(
        {
          title: title.trim(),
          theme_codes: themeCodes,
          count_per_theme: parseInt(countPerTheme) || 5,
          task_type: taskType,
          time_limit_minutes: timeLimit ? parseInt(timeLimit) : undefined,
        },
        auth.token!
      );
      setTaskId(res.task_id);
      pollStatus(res.task_id);
    } catch (err: any) {
      setError(err.message);
      setCreating(false);
      setProgress(null);
    }
  };

  const pollStatus = (tid: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const status = await api.getTaskStatus(tid, auth.token!);
        setProgress(status);

        if (status.status === "SUCCESS") {
          clearInterval(pollRef.current!);
          setResult(status.result);
          setCreating(false);
          setProgress(null);
        } else if (status.status === "FAILURE") {
          clearInterval(pollRef.current!);
          setError(status.error || "Ошибка при создании теста");
          setCreating(false);
          setProgress(null);
        }
      } catch {}
    }, 2000);
  };

  if (loading || !hydrated) return <div className="container" style={{ padding: "2rem" }}>Загрузка...</div>;

  if (subjects.length === 0) {
    return (
      <div className="container" style={{ maxWidth: 600, padding: "2rem" }}>
        <h1 style={{ marginBottom: "1.5rem" }}>Создать тест</h1>
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          <h2 style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>Нет доступных предметов</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
            Сначала синхронизируйте кодификатор тем из ФИПИ
          </p>
          <Link href="/content" className="btn btn-primary">
            Управление контентом
          </Link>
        </div>
      </div>
    );
  }

  if (result) {
    return (
      <div className="container" style={{ maxWidth: 600, padding: "2rem" }}>
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          <h2 style={{ marginBottom: "1rem", color: "var(--success)" }}>Тест создан!</h2>
          <p style={{ marginBottom: "0.5rem" }}>
            <strong>{result.title}</strong>
          </p>
          <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
            Добавлено заданий: {result.tasks_count}
          </p>
          {result.theme_stats && Object.keys(result.theme_stats).length > 0 && (
            <div style={{ marginBottom: "1.5rem", textAlign: "left" }}>
              <p style={{ fontSize: "0.875rem", fontWeight: 500, marginBottom: "0.25rem" }}>По темам:</p>
              {Object.entries(result.theme_stats).map(([code, count]) => (
                <div key={code} style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                  Тема {code}: {String(count)} заданий
                  {String(count) === "0" && (
                    <span style={{ color: "var(--danger)", marginLeft: "0.5rem" }}>
                      — задания не найдены на ФИПИ (возможно, тема из другого предмета)
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
          {result.tasks_count === 0 && (
            <div style={{ padding: "0.75rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "var(--radius)", color: "var(--danger)", marginBottom: "1rem", fontSize: "0.875rem" }}>
              Ни по одной из выбранных тем не удалось найти задания на ФИПИ. Проверьте, что темы относятся к нужному предмету.
            </div>
          )}
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
            <Link href="/dashboard" className="btn btn-primary">На дашборд</Link>
            <button className="btn" style={{ background: "var(--border)" }} onClick={() => { setResult(null); setTitle(""); setSelectedThemes([]); }}>
              Создать ещё
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ maxWidth: 800, padding: "2rem" }}>
      <h1 style={{ marginBottom: "1.5rem" }}>Создать тест</h1>

      {error && (
        <div style={{ padding: "0.75rem 1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "var(--radius)", color: "var(--danger)", marginBottom: "1rem" }}>
          {error}
          <button onClick={() => setError("")} style={{ marginLeft: "0.5rem", background: "none", border: "none", cursor: "pointer", color: "var(--danger)" }}>✕</button>
        </div>
      )}

      {creating && (
        <div className="card" style={{ textAlign: "center", padding: "2rem", marginBottom: "1rem" }}>
          <div style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>⏳</div>
          <p style={{ fontWeight: 500 }}>{progress?.status || progress?.meta?.status || "Обработка..."}</p>
          {progress?.meta?.tasks_found !== undefined && (
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              Найдено заданий: {progress.meta.tasks_found}
            </p>
          )}
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
            Пожалуйста, не закрывайте страницу
          </p>
        </div>
      )}

      <div className="card">
        <div className="form-group">
          <label>Название теста</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Например: Диагностический тест по истории" disabled={creating} />
        </div>
        <div className="grid grid-2" style={{ gap: "0.75rem" }}>
          <div className="form-group">
            <label>Лимит времени (минут)</label>
            <input type="number" value={timeLimit} onChange={(e) => setTimeLimit(e.target.value)} min="1" placeholder="Без таймера" disabled={creating} />
          </div>
          <div className="form-group">
            <label>Заданий на тему</label>
            <input type="number" value={countPerTheme} onChange={(e) => setCountPerTheme(e.target.value)} min="1" max="20" disabled={creating} />
          </div>
        </div>
        <div className="form-group">
          <label>Тип заданий</label>
          <select value={taskType} onChange={(e) => setTaskType(e.target.value)} disabled={creating}>
            <option value="TEST">Только TEST</option>
            <option value="ESSAY">Только ESSAY</option>
            <option value="MIX">Микс (TEST + ESSAY)</option>
          </select>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: "1rem" }}>Выберите предмет</h3>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {subjects.map((s) => (
            <button
              key={s.id}
              className={`btn ${selectedSubject === s.id ? "btn-primary" : ""}`}
              style={!selectedSubject || selectedSubject !== s.id ? { background: "var(--border)", color: "var(--text)" } : {}}
              onClick={() => loadThemes(s.id)}
              disabled={creating}
            >
              {s.name}
            </button>
          ))}
        </div>
      </div>

      {selectedSubject && themeTree.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
          <p style={{ color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Кодификатор тем не загружен</p>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
            Обратитесь к администратору для синхронизации тем из ФИПИ
          </p>
        </div>
      )}

      {themeTree.length > 0 && (
        <div className="card">
          <h3 style={{ marginBottom: "1rem" }}>
            Темы <span style={{ fontWeight: 400, fontSize: "0.875rem" }}>(выбрано: {selectedThemes.length})</span>
          </h3>
          <div style={{ maxHeight: 400, overflow: "auto" }}>{renderTree(themeTree)}</div>
        </div>
      )}

      <div style={{ marginTop: "1rem" }}>
        {!canCreate && !creating && (
          <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
            {getValidationError()}
          </div>
        )}
        <div style={{ display: "flex", gap: "1rem" }}>
          <button
            className="btn btn-primary"
            onClick={handleCreate}
            disabled={!canCreate}
            style={!canCreate ? { opacity: 0.5, cursor: "not-allowed" } : {}}
          >
            {creating ? "Создание..." : "Создать тест"}
          </button>
          <button className="btn" style={{ background: "var(--border)" }} onClick={() => router.back()} disabled={creating}>
            Отмена
          </button>
        </div>
      </div>
    </div>
  );
}
